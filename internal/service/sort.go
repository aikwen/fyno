package service

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"slices"
	"sync"
	"time"

	"github.com/aikwen/fyno/internal/domain"
	"github.com/aikwen/fyno/internal/store"
)

const sortSaveInterval = time.Second

// SortService 管理辅助排序的内存状态和异步持久化。
type SortService struct {
	store *store.Store

	mu           sync.Mutex
	data         *store.Sort
	version      uint64
	savedVersion uint64

	stop      chan struct{}
	done      chan struct{}
	closeOnce sync.Once
	closeErr  error
}

// NewSortService 加载一次排序文件，并启动唯一的后台保存循环。
func NewSortService(s *store.Store) (*SortService, error) {
	if s == nil {
		return nil, fmt.Errorf("create sort service: store must not be nil")
	}

	data, err := s.LoadSort()
	dirty := false
	if err != nil {
		if !isRecoverableSortError(err) {
			return nil, fmt.Errorf("create sort service: load sort: %w", err)
		}
		data = newSort()
		dirty = true
	} else if data == nil {
		data = newSort()
		dirty = true
	} else {
		if data.Sections == nil {
			data.Sections = make(map[int64][]int64)
			dirty = true
		}
		if data.Pages == nil {
			data.Pages = make(map[int64][]int64)
			dirty = true
		}
	}

	service := &SortService{
		store: s,
		data:  data,
		stop:  make(chan struct{}),
		done:  make(chan struct{}),
	}
	if dirty {
		service.version = 1
	}
	go service.saveLoop()
	return service, nil
}

// Close 停止后台循环，等待最终保存完成，并返回最终保存错误。
func (s *SortService) Close() error {
	s.closeOnce.Do(func() {
		close(s.stop)
	})

	<-s.done
	return s.closeErr
}

func (s *SortService) saveLoop() {
	ticker := time.NewTicker(sortSaveInterval)
	defer ticker.Stop()
	defer close(s.done)

	for {
		select {
		case <-ticker.C:
			_ = s.persistPendingSort()
		case <-s.stop:
			s.closeErr = s.persistPendingSort()
			return
		}
	}
}

// persistPendingSort 在锁内取得同一时刻的版本化快照，在锁外执行文件写入。
func (s *SortService) persistPendingSort() error {
	snapshot, version, ok := s.pendingSnapshot()
	if !ok {
		return nil
	}

	if err := s.store.SaveSort(snapshot); err != nil {
		return fmt.Errorf("save sort snapshot version %d: %w", version, err)
	}
	s.markSaved(version)
	return nil
}

func (s *SortService) pendingSnapshot() (*store.Sort, uint64, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.version == s.savedVersion {
		return nil, 0, false
	}
	return cloneSort(s.data), s.version, true
}

func (s *SortService) markSaved(version uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if version > s.savedVersion {
		s.savedVersion = version
	}
}

// GetRootList 根据 SQLite 的当前 ID 集合修复并返回内存中的 Notebook 排序。
func (s *SortService) GetRootList(current []int64) ([]int64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, changed := mergeOrder(s.data.Notebooks, current)
	if changed {
		s.saveRootListLocked(order)
	}
	return slices.Clone(order), nil
}

// GetNotebookList 根据 SQLite 的当前 ID 集合修复并返回内存中的 Section 排序。
func (s *SortService) GetNotebookList(notebookID int64, current []int64) ([]int64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, changed := mergeOrder(s.data.Sections[notebookID], current)
	if changed {
		s.saveNotebookListLocked(notebookID, order)
	}
	return slices.Clone(order), nil
}

// GetSectionList 根据 SQLite 的当前 ID 集合修复并返回内存中的 Page 排序。
func (s *SortService) GetSectionList(sectionID int64, current []int64) ([]int64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, changed := mergeOrder(s.data.Pages[sectionID], current)
	if changed {
		s.saveSectionListLocked(sectionID, order)
	}
	return slices.Clone(order), nil
}

// MoveRoot 在一次加锁中合并当前 ID、移动 Notebook 并更新内存排序。
func (s *SortService) MoveRoot(current []int64, id, afterID int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, _ := mergeOrder(s.data.Notebooks, current)
	moved, _, err := moveAfter(order, id, afterID)
	if err != nil {
		return err
	}
	s.saveRootListLocked(moved)
	return nil
}

// MoveNotebook 在一次加锁中合并当前 ID、移动 Section 并更新内存排序。
func (s *SortService) MoveNotebook(notebookID int64, current []int64, id, afterID int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, _ := mergeOrder(s.data.Sections[notebookID], current)
	moved, _, err := moveAfter(order, id, afterID)
	if err != nil {
		return err
	}
	s.saveNotebookListLocked(notebookID, moved)
	return nil
}

// MoveSection 在一次加锁中合并当前 ID、移动 Page 并更新内存排序。
func (s *SortService) MoveSection(sectionID int64, current []int64, id, afterID int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	order, _ := mergeOrder(s.data.Pages[sectionID], current)
	moved, _, err := moveAfter(order, id, afterID)
	if err != nil {
		return err
	}
	s.saveSectionListLocked(sectionID, moved)
	return nil
}

func (s *SortService) saveRootListLocked(ids []int64) {
	if slices.Equal(s.data.Notebooks, ids) {
		return
	}
	s.data.Notebooks = slices.Clone(ids)
	s.version++
}

func (s *SortService) saveNotebookListLocked(notebookID int64, ids []int64) {
	if slices.Equal(s.data.Sections[notebookID], ids) {
		return
	}
	s.data.Sections[notebookID] = slices.Clone(ids)
	s.version++
}

func (s *SortService) saveSectionListLocked(sectionID int64, ids []int64) {
	if slices.Equal(s.data.Pages[sectionID], ids) {
		return
	}
	s.data.Pages[sectionID] = slices.Clone(ids)
	s.version++
}

// MoveNotebook 校验 SQLite 节点后，将 Notebook 移动到指定兄弟节点之后。
func (s *LibraryService) MoveNotebook(ctx context.Context, id, afterID int64) error {
	if err := validateMoveIDs("notebook", id, afterID); err != nil {
		return err
	}
	if _, err := s.store.GetNotebook(ctx, id); err != nil {
		return fmt.Errorf("move notebook %d: %w", id, err)
	}
	if afterID != 0 {
		if _, err := s.store.GetNotebook(ctx, afterID); err != nil {
			return fmt.Errorf("move notebook %d after %d: %w", id, afterID, err)
		}
	}

	notebooks, err := s.store.ListNotebooks(ctx)
	if err != nil {
		return fmt.Errorf("move notebook %d: list notebooks: %w", id, err)
	}
	if err := s.sort.MoveRoot(notebookIDs(notebooks), id, afterID); err != nil {
		return fmt.Errorf("move notebook %d: %w", id, err)
	}
	return nil
}

// MoveSection 校验 SQLite 节点及父关系后，移动同一 Notebook 中的 Section。
func (s *LibraryService) MoveSection(ctx context.Context, id, afterID int64) error {
	if err := validateMoveIDs("section", id, afterID); err != nil {
		return err
	}
	section, err := s.store.GetSection(ctx, id)
	if err != nil {
		return fmt.Errorf("move section %d: %w", id, err)
	}
	if afterID != 0 {
		after, err := s.store.GetSection(ctx, afterID)
		if err != nil {
			return fmt.Errorf("move section %d after %d: %w", id, afterID, err)
		}
		if after.NotebookID != section.NotebookID {
			return fmt.Errorf("move section %d: target section %d belongs to another notebook", id, afterID)
		}
	}

	sections, err := s.store.ListSections(ctx, section.NotebookID)
	if err != nil {
		return fmt.Errorf("move section %d: list sections: %w", id, err)
	}
	if err := s.sort.MoveNotebook(section.NotebookID, sectionIDs(sections), id, afterID); err != nil {
		return fmt.Errorf("move section %d: %w", id, err)
	}
	return nil
}

// MovePage 校验 SQLite 节点及父关系后，移动同一 Section 中的 Page。
func (s *LibraryService) MovePage(ctx context.Context, id, afterID int64) error {
	if err := validateMoveIDs("page", id, afterID); err != nil {
		return err
	}
	page, err := s.store.GetPage(ctx, id)
	if err != nil {
		return fmt.Errorf("move page %d: %w", id, err)
	}
	if afterID != 0 {
		after, err := s.store.GetPage(ctx, afterID)
		if err != nil {
			return fmt.Errorf("move page %d after %d: %w", id, afterID, err)
		}
		if after.SectionID != page.SectionID {
			return fmt.Errorf("move page %d: target page %d belongs to another section", id, afterID)
		}
	}

	pages, err := s.store.ListPages(ctx, page.SectionID)
	if err != nil {
		return fmt.Errorf("move page %d: list pages: %w", id, err)
	}
	if err := s.sort.MoveSection(page.SectionID, pageIDs(pages), id, afterID); err != nil {
		return fmt.Errorf("move page %d: %w", id, err)
	}
	return nil
}

func newSort() *store.Sort {
	return &store.Sort{
		Notebooks: make([]int64, 0),
		Sections:  make(map[int64][]int64),
		Pages:     make(map[int64][]int64),
	}
}

func cloneSort(source *store.Sort) *store.Sort {
	result := newSort()
	result.Notebooks = slices.Clone(source.Notebooks)
	for key, ids := range source.Sections {
		result.Sections[key] = slices.Clone(ids)
	}
	for key, ids := range source.Pages {
		result.Pages[key] = slices.Clone(ids)
	}
	return result
}

func isRecoverableSortError(err error) bool {
	if errors.Is(err, fs.ErrNotExist) {
		return true
	}

	var syntaxError *json.SyntaxError
	if errors.As(err, &syntaxError) {
		return true
	}

	var typeError *json.UnmarshalTypeError
	return errors.As(err, &typeError)
}

func mergeOrder(saved, current []int64) ([]int64, bool) {
	remaining := make(map[int64]struct{}, len(current))
	for _, id := range current {
		remaining[id] = struct{}{}
	}

	merged := make([]int64, 0, len(current))
	changed := false

	for _, id := range saved {
		if _, ok := remaining[id]; !ok {
			changed = true
			continue
		}

		merged = append(merged, id)
		delete(remaining, id)
	}

	for _, id := range current {
		if _, ok := remaining[id]; !ok {
			continue
		}

		merged = append(merged, id)
		delete(remaining, id)
		changed = true
	}

	return merged, changed
}

// moveAfter 只调整切片顺序，不访问数据库或文件。
func moveAfter(order []int64, id, afterID int64) ([]int64, bool, error) {
	if id == afterID && id != 0 {
		return nil, false, fmt.Errorf("cannot move node after itself")
	}

	idIndex := -1
	afterIndex := -1
	for i, current := range order {
		if current == id {
			idIndex = i
		}
		if current == afterID {
			afterIndex = i
		}
	}
	if idIndex == -1 {
		return nil, false, fmt.Errorf("node %d: %w", id, sql.ErrNoRows)
	}
	if afterID != 0 && afterIndex == -1 {
		return nil, false, fmt.Errorf("target node %d: %w", afterID, sql.ErrNoRows)
	}

	previousID := int64(0)
	if idIndex > 0 {
		previousID = order[idIndex-1]
	}
	changed := previousID != afterID
	if !changed {
		return slices.Clone(order), false, nil
	}

	result := make([]int64, 0, len(order))
	switch {
	case afterID == 0:
		result = append(result, id)
		result = append(result, order[:idIndex]...)
		result = append(result, order[idIndex+1:]...)
	case afterIndex < idIndex:
		result = append(result, order[:afterIndex+1]...)
		result = append(result, id)
		result = append(result, order[afterIndex+1:idIndex]...)
		result = append(result, order[idIndex+1:]...)
	case afterIndex > idIndex:
		result = append(result, order[:idIndex]...)
		result = append(result, order[idIndex+1:afterIndex+1]...)
		result = append(result, id)
		result = append(result, order[afterIndex+1:]...)
	}

	return result, true, nil
}

func validateMoveIDs(name string, id, afterID int64) error {
	if err := validateID(name, id); err != nil {
		return err
	}
	if afterID < 0 {
		return fmt.Errorf("target %s ID must not be negative", name)
	}
	if id == afterID {
		return fmt.Errorf("cannot move %s %d after itself", name, id)
	}
	return nil
}

func applyOrder[T any](items []T, order []int64, idOf func(T) int64) []T {
	byID := make(map[int64]T, len(items))
	for _, item := range items {
		byID[idOf(item)] = item
	}

	result := make([]T, 0, len(items))
	for _, id := range order {
		if item, ok := byID[id]; ok {
			result = append(result, item)
		}
	}
	return result
}

func notebookIDs(notebooks []domain.Notebook) []int64 {
	ids := make([]int64, 0, len(notebooks))
	for _, notebook := range notebooks {
		ids = append(ids, notebook.ID)
	}
	return ids
}

func sectionIDs(sections []domain.Section) []int64 {
	ids := make([]int64, 0, len(sections))
	for _, section := range sections {
		ids = append(ids, section.ID)
	}
	return ids
}

func pageIDs(pages []domain.Page) []int64 {
	ids := make([]int64, 0, len(pages))
	for _, page := range pages {
		ids = append(ids, page.ID)
	}
	return ids
}
