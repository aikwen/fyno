package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"

	"github.com/aikwen/fyno/internal/domain"
)

var defaultPageContent = json.RawMessage(`{"type":"doc","content":[]}`)

// CreatePage 校验父 Section，创建元数据和默认 Tiptap 正文。
func (s *LibraryService) CreatePage(ctx context.Context, sectionID int64, title string) (*domain.Page, error) {
	if err := validateID("section", sectionID); err != nil {
		return nil, err
	}

	title, err := normalizeText("page title", title)
	if err != nil {
		return nil, err
	}

	if _, err := s.store.GetSection(ctx, sectionID); err != nil {
		return nil, fmt.Errorf("create page: get section %d: %w", sectionID, err)
	}

	page, err := s.store.CreatePage(ctx, sectionID, title)
	if err != nil {
		return nil, fmt.Errorf("create page: %w", err)
	}

	if err := s.store.SaveDocument(page.ID, defaultPageContent); err != nil {
		return nil, fmt.Errorf("create page %d: save default content: %w", page.ID, err)
	}

	return page, nil
}

// ListPages 校验父 Section，并返回按内存排序状态排列的 Page。
func (s *LibraryService) ListPages(ctx context.Context, sectionID int64) ([]domain.Page, error) {
	if err := validateID("section", sectionID); err != nil {
		return nil, err
	}

	if _, err := s.store.GetSection(ctx, sectionID); err != nil {
		return nil, fmt.Errorf("list pages: get section %d: %w", sectionID, err)
	}

	pages, err := s.store.ListPages(ctx, sectionID)
	if err != nil {
		return nil, fmt.Errorf("list pages for section %d: %w", sectionID, err)
	}

	order, err := s.sort.GetSectionList(sectionID, pageIDs(pages))
	if err != nil {
		return nil, err
	}

	return applyOrder(pages, order, func(page domain.Page) int64 {
		return page.ID
	}), nil
}

// GetPage 同时读取 Page 元数据和 Tiptap 正文。
func (s *LibraryService) GetPage(ctx context.Context, id int64) (*domain.Page, json.RawMessage, error) {
	if err := validateID("page", id); err != nil {
		return nil, nil, err
	}

	page, err := s.store.GetPage(ctx, id)
	if err != nil {
		return nil, nil, fmt.Errorf("get page %d: %w", id, err)
	}

	content, err := s.store.LoadDocument(id)
	if err == nil {
		return page, content, nil
	}
	if !errors.Is(err, fs.ErrNotExist) {
		return nil, nil, fmt.Errorf("get page %d: load content: %w", id, err)
	}

	if err := s.store.CreateDocumentIfAbsent(id, defaultPageContent); err != nil && !errors.Is(err, fs.ErrExist) {
		return nil, nil, fmt.Errorf("get page %d: create missing content: %w", id, err)
	}

	content, err = s.store.LoadDocument(id)
	if err != nil {
		return nil, nil, fmt.Errorf("get page %d: load initialized content: %w", id, err)
	}
	return page, content, nil
}

// UpdatePage 校验并更新 Page 标题，不改变所属 Section。
func (s *LibraryService) UpdatePage(ctx context.Context, id int64, title string) error {
	if err := validateID("page", id); err != nil {
		return err
	}

	title, err := normalizeText("page title", title)
	if err != nil {
		return err
	}

	if err := s.store.UpdatePage(ctx, id, title); err != nil {
		return fmt.Errorf("update page %d: %w", id, err)
	}
	return nil
}

// DeletePage 删除 Page 元数据，并尽力清理正文文件。
func (s *LibraryService) DeletePage(ctx context.Context, id int64) error {
	if err := validateID("page", id); err != nil {
		return err
	}

	if err := s.store.DeletePage(ctx, id); err != nil {
		return fmt.Errorf("delete page %d: %w", id, err)
	}

	_ = s.store.DeleteDocument(id)

	return nil
}

// SavePageContent 在确认 Page 元数据存在后保存 Tiptap JSON 正文。
func (s *LibraryService) SavePageContent(ctx context.Context, id int64, content json.RawMessage) error {
	if err := validateID("page", id); err != nil {
		return err
	}

	if _, err := s.store.GetPage(ctx, id); err != nil {
		return fmt.Errorf("save page content %d: get page: %w", id, err)
	}

	if err := s.store.SaveDocument(id, content); err != nil {
		return fmt.Errorf("save page content %d: %w", id, err)
	}
	return nil
}
