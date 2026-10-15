package service

import (
	"context"
	"fmt"

	"github.com/aikwen/fyno/internal/domain"
)

// CreateSection 校验父 Notebook 后创建 Section。
func (s *LibraryService) CreateSection(ctx context.Context, notebookID int64, name, color string) (*domain.Section, error) {
	if err := validateID("notebook", notebookID); err != nil {
		return nil, err
	}

	name, err := normalizeText("section name", name)
	if err != nil {
		return nil, err
	}

	if _, err := s.store.GetNotebook(ctx, notebookID); err != nil {
		return nil, fmt.Errorf("create section: get notebook %d: %w", notebookID, err)
	}

	section, err := s.store.CreateSection(ctx, notebookID, name, color)
	if err != nil {
		return nil, fmt.Errorf("create section: %w", err)
	}

	return section, nil
}

// ListSections 校验父 Notebook，并返回按内存排序状态排列的 Section。
func (s *LibraryService) ListSections(ctx context.Context, notebookID int64) ([]domain.Section, error) {
	if err := validateID("notebook", notebookID); err != nil {
		return nil, err
	}

	if _, err := s.store.GetNotebook(ctx, notebookID); err != nil {
		return nil, fmt.Errorf("list sections: get notebook %d: %w", notebookID, err)
	}

	sections, err := s.store.ListSections(ctx, notebookID)
	if err != nil {
		return nil, fmt.Errorf("list sections for notebook %d: %w", notebookID, err)
	}

	order, err := s.sort.GetNotebookList(notebookID, sectionIDs(sections))
	if err != nil {
		return nil, err
	}

	return applyOrder(sections, order, func(section domain.Section) int64 {
		return section.ID
	}), nil
}

// UpdateSection 校验并更新 Section，不改变所属 Notebook。
func (s *LibraryService) UpdateSection(ctx context.Context, id int64, name, color string) error {
	if err := validateID("section", id); err != nil {
		return err
	}

	name, err := normalizeText("section name", name)
	if err != nil {
		return err
	}

	if err := s.store.UpdateSection(ctx, id, name, color); err != nil {
		return fmt.Errorf("update section %d: %w", id, err)
	}
	return nil
}

// DeleteSection 删除 Section 树，并尽力清理关联的正文文件。
func (s *LibraryService) DeleteSection(ctx context.Context, id int64) error {
	if err := validateID("section", id); err != nil {
		return err
	}

	pageIDs, err := s.store.DeleteSectionTree(ctx, id)
	if err != nil {
		return fmt.Errorf("delete section %d: %w", id, err)
	}

	for _, pageID := range pageIDs {
		_ = s.store.DeleteDocument(pageID)
	}
	return nil
}
