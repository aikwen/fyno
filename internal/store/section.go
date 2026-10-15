package store

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/aikwen/fyno/internal/domain"
)

// CreateSection 创建 Section 元数据，不校验关联的 Notebook。
func (s *Store) CreateSection(ctx context.Context, notebookID int64, name, color string) (*domain.Section, error) {
	result, err := s.db.ExecContext(ctx, `
		INSERT INTO sections (notebook_id, name, color)
		VALUES (?, ?, ?)
	`, notebookID, name, color)
	if err != nil {
		return nil, fmt.Errorf("create section: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("get created section ID: %w", err)
	}

	return &domain.Section{
		ID:         id,
		NotebookID: notebookID,
		Name:       name,
		Color:      color,
	}, nil
}

// GetSection 根据 ID 获取 Section 元数据。
func (s *Store) GetSection(ctx context.Context, id int64) (*domain.Section, error) {
	var section domain.Section

	err := s.db.QueryRowContext(ctx, `
		SELECT id, notebook_id, name, color
		FROM sections
		WHERE id = ?
	`, id).Scan(&section.ID, &section.NotebookID, &section.Name, &section.Color)
	if err != nil {
		return nil, fmt.Errorf("get section %d: %w", id, err)
	}

	return &section, nil
}

// ListSections 按 ID 升序列出指定 Notebook 下的 Section 元数据。
func (s *Store) ListSections(ctx context.Context, notebookID int64) ([]domain.Section, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, notebook_id, name, color
		FROM sections
		WHERE notebook_id = ?
		ORDER BY id ASC
	`, notebookID)
	if err != nil {
		return nil, fmt.Errorf("list sections for notebook %d: %w", notebookID, err)
	}
	defer func() {
		_ = rows.Close()
	}()

	sections := make([]domain.Section, 0)
	for rows.Next() {
		var section domain.Section
		if err := rows.Scan(&section.ID, &section.NotebookID, &section.Name, &section.Color); err != nil {
			return nil, fmt.Errorf("scan section: %w", err)
		}
		sections = append(sections, section)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate sections: %w", err)
	}

	return sections, nil
}

// UpdateSection 更新 Section 可修改的元数据字段，不修改所属 Notebook。
func (s *Store) UpdateSection(ctx context.Context, id int64, name, color string) error {
	result, err := s.db.ExecContext(ctx, `
		UPDATE sections
		SET name = ?, color = ?
		WHERE id = ?
	`, name, color, id)
	if err != nil {
		return fmt.Errorf("update section %d: %w", id, err)
	}

	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get updated section rows: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("update section %d: %w", id, sql.ErrNoRows)
	}

	return nil
}

// DeleteSectionTree 在一个事务中删除 Section 及其全部 Page。
// 本方法只处理 SQLite 元数据，并返回删除前按 ID 升序查询到的 Page ID。
func (s *Store) DeleteSectionTree(ctx context.Context, id int64) ([]int64, error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("delete section tree %d: begin transaction: %w", id, err)
	}
	defer func() {
		_ = tx.Rollback()
	}()

	var exists int
	if err := tx.QueryRowContext(ctx, `
		SELECT 1
		FROM sections
		WHERE id = ?
	`, id).Scan(&exists); err != nil {
		return nil, fmt.Errorf("delete section tree %d: check section: %w", id, err)
	}

	rows, err := tx.QueryContext(ctx, `
		SELECT id
		FROM pages
		WHERE section_id = ?
		ORDER BY id ASC
	`, id)
	if err != nil {
		return nil, fmt.Errorf("delete section tree %d: query page IDs: %w", id, err)
	}

	pageIDs := make([]int64, 0)
	for rows.Next() {
		var pageID int64
		if err := rows.Scan(&pageID); err != nil {
			_ = rows.Close()
			return nil, fmt.Errorf("delete section tree %d: scan page ID: %w", id, err)
		}
		pageIDs = append(pageIDs, pageID)
	}
	if err := rows.Err(); err != nil {
		_ = rows.Close()
		return nil, fmt.Errorf("delete section tree %d: iterate page IDs: %w", id, err)
	}
	if err := rows.Close(); err != nil {
		return nil, fmt.Errorf("delete section tree %d: close page rows: %w", id, err)
	}

	if _, err := tx.ExecContext(ctx, `
		DELETE FROM pages
		WHERE section_id = ?
	`, id); err != nil {
		return nil, fmt.Errorf("delete section tree %d: delete pages: %w", id, err)
	}

	if _, err := tx.ExecContext(ctx, `
		DELETE FROM sections
		WHERE id = ?
	`, id); err != nil {
		return nil, fmt.Errorf("delete section tree %d: delete section: %w", id, err)
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("delete section tree %d: commit transaction: %w", id, err)
	}

	return pageIDs, nil
}
