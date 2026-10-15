package service

import (
	"context"
	"fmt"

	"github.com/aikwen/fyno/internal/domain"
)

// CreateNotebook 校验并创建 Notebook。
func (s *LibraryService) CreateNotebook(ctx context.Context, name, color string) (*domain.Notebook, error) {
	name, err := normalizeText("notebook name", name)
	if err != nil {
		return nil, err
	}

	notebook, err := s.store.CreateNotebook(ctx, name, color)
	if err != nil {
		return nil, fmt.Errorf("create notebook: %w", err)
	}

	return notebook, nil
}

// ListNotebooks 返回按内存排序状态排列的 Notebook。
func (s *LibraryService) ListNotebooks(ctx context.Context) ([]domain.Notebook, error) {
	notebooks, err := s.store.ListNotebooks(ctx)
	if err != nil {
		return nil, fmt.Errorf("list notebooks: %w", err)
	}

	order, err := s.sort.GetRootList(notebookIDs(notebooks))
	if err != nil {
		return nil, err
	}

	return applyOrder(notebooks, order, func(notebook domain.Notebook) int64 {
		return notebook.ID
	}), nil
}

// UpdateNotebook 校验并更新 Notebook，不改变其 ID 和层级关系。
func (s *LibraryService) UpdateNotebook(ctx context.Context, id int64, name, color string) error {
	if err := validateID("notebook", id); err != nil {
		return err
	}

	name, err := normalizeText("notebook name", name)
	if err != nil {
		return err
	}

	if err := s.store.UpdateNotebook(ctx, id, name, color); err != nil {
		return fmt.Errorf("update notebook %d: %w", id, err)
	}
	return nil
}

// DeleteNotebook 删除 Notebook 树，并尽力清理关联的正文文件。
func (s *LibraryService) DeleteNotebook(ctx context.Context, id int64) error {
	if err := validateID("notebook", id); err != nil {
		return err
	}

	pageIDs, err := s.store.DeleteNotebookTree(ctx, id)
	if err != nil {
		return fmt.Errorf("delete notebook %d: %w", id, err)
	}

	for _, pageID := range pageIDs {
		_ = s.store.DeleteDocument(pageID)
	}

	return nil
}
