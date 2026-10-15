package store

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/aikwen/fyno/internal/domain"
)

// CreatePage 创建 Page 元数据，不校验关联的 Section，也不创建正文文件。
func (s *Store) CreatePage(ctx context.Context, sectionID int64, title string) (*domain.Page, error) {
	result, err := s.db.ExecContext(ctx, `
		INSERT INTO pages (section_id, title)
		VALUES (?, ?)
	`, sectionID, title)
	if err != nil {
		return nil, fmt.Errorf("create page: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("get created page ID: %w", err)
	}

	return &domain.Page{
		ID:        id,
		SectionID: sectionID,
		Title:     title,
	}, nil
}

// GetPage 根据 ID 获取 Page 元数据。
func (s *Store) GetPage(ctx context.Context, id int64) (*domain.Page, error) {
	var page domain.Page

	err := s.db.QueryRowContext(ctx, `
		SELECT id, section_id, title
		FROM pages
		WHERE id = ?
	`, id).Scan(&page.ID, &page.SectionID, &page.Title)
	if err != nil {
		return nil, fmt.Errorf("get page %d: %w", id, err)
	}

	return &page, nil
}

// ListPages 按 ID 升序列出指定 Section 下的 Page 元数据。
func (s *Store) ListPages(ctx context.Context, sectionID int64) ([]domain.Page, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, section_id, title
		FROM pages
		WHERE section_id = ?
		ORDER BY id ASC
	`, sectionID)
	if err != nil {
		return nil, fmt.Errorf("list pages for section %d: %w", sectionID, err)
	}
	defer func() {
		_ = rows.Close()
	}()

	pages := make([]domain.Page, 0)
	for rows.Next() {
		var page domain.Page
		if err := rows.Scan(&page.ID, &page.SectionID, &page.Title); err != nil {
			return nil, fmt.Errorf("scan page: %w", err)
		}
		pages = append(pages, page)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate pages: %w", err)
	}

	return pages, nil
}

// UpdatePage 更新 Page 标题，不修改所属 Section 或正文文件。
func (s *Store) UpdatePage(ctx context.Context, id int64, title string) error {
	result, err := s.db.ExecContext(ctx, `
		UPDATE pages
		SET title = ?
		WHERE id = ?
	`, title, id)
	if err != nil {
		return fmt.Errorf("update page %d: %w", id, err)
	}

	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get updated page rows: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("update page %d: %w", id, sql.ErrNoRows)
	}

	return nil
}

// DeletePage 仅删除 Page 元数据，不删除正文文件。
func (s *Store) DeletePage(ctx context.Context, id int64) error {
	result, err := s.db.ExecContext(ctx, `
		DELETE FROM pages
		WHERE id = ?
	`, id)
	if err != nil {
		return fmt.Errorf("delete page %d: %w", id, err)
	}

	affected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("get deleted page rows: %w", err)
	}
	if affected == 0 {
		return fmt.Errorf("delete page %d: %w", id, sql.ErrNoRows)
	}

	return nil
}
