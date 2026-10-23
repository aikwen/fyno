package app

import (
	"encoding/json"

	"github.com/aikwen/fyno/internal/domain"
)

// PageDetail 是 Page 元数据与正文内容的 Bridge 返回结构。
type PageDetail struct {
	Page    *domain.Page    `json:"page"`
	Content json.RawMessage `json:"content"`
}

// CreatePage 在指定 Section 中创建 Page。
func (a *App) CreatePage(sectionID int64, title string) (*domain.Page, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.CreatePage(a.ctx, sectionID, title)
}

// ListPages 返回指定 Section 中的 Page 列表。
func (a *App) ListPages(sectionID int64) ([]domain.Page, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.ListPages(a.ctx, sectionID)
}

// GetPage 返回指定 Page 的元数据及正文内容。
func (a *App) GetPage(id int64) (*PageDetail, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	page, content, err := a.library.GetPage(a.ctx, id)
	if err != nil {
		return nil, err
	}

	return &PageDetail{
		Page:    page,
		Content: content,
	}, nil
}

// UpdatePage 更新指定 Page 的标题。
func (a *App) UpdatePage(id int64, title string) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.UpdatePage(a.ctx, id, title)
}

// DeletePage 删除指定 Page 及其正文。
func (a *App) DeletePage(id int64) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.DeletePage(a.ctx, id)
}

// SavePageContent 保存指定 Page 的 JSON 正文。
func (a *App) SavePageContent(id int64, content json.RawMessage) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.SavePageContent(a.ctx, id, content)
}
