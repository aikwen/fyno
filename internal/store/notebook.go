package store

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/aikwen/fyno/internal/domain"
)

// CreateNotebook 创建 Notebook 元数据。
func (s *Store) CreateNotebook(ctx context.Context, name, color string) (*domain.Notebook, error) {
	result, err := s.db.ExecContext(ctx, `
		INSERT INTO notebooks (name, color)
		VALUES (?, ?)
	`, name, color)
	if err != nil {
		return nil, fmt.Errorf("create notebook: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("get created notebook ID: %w", err)
	}

	return &domain.Notebook{
		ID:    id,
		Name:  name,
		Color: color,
	}, nil
}

// GetNotebook 根据 ID 获取 Notebook 元数据。
func (s *Store) GetNotebook(ctx context.Context, id int64) (*domain.Notebook, error) {
	var notebook domain.Notebook

	err := s.db.QueryRowContext(ctx, `
		SELECT id, name, color
		FROM notebooks
		WHERE id = ?
	`, id).Scan(&notebook.ID, &notebook.Name, &notebook.Color)
	if err != nil {
		return nil, fmt.Errorf("get notebook %d: %w", id, err)
	}

	return &notebook, nil
}

// ListNotebooks 按 ID 升序列出全部 Notebook 元数据。
func (s *Store) ListNotebooks(ctx context.Context) ([]domain.Notebook, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, name, color
		FROM notebooks
		ORDER BY id ASC
	`)
	if err != nil {
		return nil, fmt.Errorf("list notebooks: %w", err)
	}
	defer func() {
		_ = rows.Close()
	}()

	notebooks := make([]domain.Notebook, 0)
	for rows.Next() {
		var notebook domain.Notebook
		if err := rows.Scan(&notebook.ID, &notebook.Name, &notebook.Color); err != nil {
			return nil, fmt.Errorf("scan notebook: %w", err)
		}
		notebooks = append(notebooks, notebook)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate notebooks: %w", err)
	}

	return notebooks, nil
}

// UpdateNotebook 更新 Notebook 可修改的元数据字段。
func (s *Store) UpdateNotebook(ctx context.Context, id int64, name, color string) error {
	result, err := s.db.ExecContext(ctx, `
		UPDATE notebooks
		SET name = ?, color = ?
		WHERE id = ?
	`, name, color, id)
	if err != nil {
		return fmt.Errorf("update notebook %d: %w", id, err)
	}

	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get updated notebook rows: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("update notebook %d: %w", id, sql.ErrNoRows)
	}

	return nil
}

// DeleteNotebookTree 在一个事务中删除 Notebook 及其全部 Section、Page。
// 本方法只处理 SQLite 元数据，并返回删除前按 ID 升序查询到的 Page ID。
func (s *Store) DeleteNotebookTree(ctx context.Context, id int64) ([]int64, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: begin transaction: %w", id, err)
	}
	defer func() {
		_ = tx.Rollback()
	}()

	var exists int
	if err := tx.QueryRowContext(ctx, `
		SELECT 1
		FROM notebooks
		WHERE id = ?
	`, id).Scan(&exists); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: check notebook: %w", id, err)
	}

	rows, err := tx.QueryContext(ctx, `
		SELECT p.id
		FROM pages AS p
		JOIN sections AS s ON p.section_id = s.id
		WHERE s.notebook_id = ?
		ORDER BY p.id ASC
	`, id)
	if err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: query page IDs: %w", id, err)
	}

	pageIDs := make([]int64, 0)
	for rows.Next() {
		var pageID int64
		if err := rows.Scan(&pageID); err != nil {
			_ = rows.Close()
			return nil, fmt.Errorf("delete notebook tree %d: scan page ID: %w", id, err)
		}
		pageIDs = append(pageIDs, pageID)
	}
	if err := rows.Err(); err != nil {
		_ = rows.Close()
		return nil, fmt.Errorf("delete notebook tree %d: iterate page IDs: %w", id, err)
	}
	if err := rows.Close(); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: close page rows: %w", id, err)
	}

	if _, err := tx.ExecContext(ctx, `
		DELETE FROM pages
		WHERE section_id IN (
			SELECT id FROM sections WHERE notebook_id = ?
		)
	`, id); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: delete pages: %w", id, err)
	}

	if _, err := tx.ExecContext(ctx, `
		DELETE FROM sections
		WHERE notebook_id = ?
	`, id); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: delete sections: %w", id, err)
	}

	if _, err := tx.ExecContext(ctx, `
		DELETE FROM notebooks
		WHERE id = ?
	`, id); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: delete notebook: %w", id, err)
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("delete notebook tree %d: commit transaction: %w", id, err)
	}

	return pageIDs, nil
}
