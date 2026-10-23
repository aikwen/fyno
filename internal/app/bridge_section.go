package app

import "github.com/aikwen/fyno/internal/domain"

// CreateSection 在指定 Notebook 中创建 Section。
func (a *App) CreateSection(notebookID int64, name, color string) (*domain.Section, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.CreateSection(a.ctx, notebookID, name, color)
}

// ListSections 返回指定 Notebook 中的 Section 列表。
func (a *App) ListSections(notebookID int64) ([]domain.Section, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.ListSections(a.ctx, notebookID)
}

// UpdateSection 更新指定 Section 的可编辑字段。
func (a *App) UpdateSection(id int64, name, color string) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.UpdateSection(a.ctx, id, name, color)
}

// DeleteSection 删除指定 Section 及其关联数据。
func (a *App) DeleteSection(id int64) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.DeleteSection(a.ctx, id)
}
