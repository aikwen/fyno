package app

import (
	"errors"

	"github.com/aikwen/fyno/internal/domain"
)

var errWorkspaceNotInitialized = errors.New("workspace is not initialized")

// CreateNotebook 在当前工作目录中创建 Notebook。
func (a *App) CreateNotebook(name, color string) (*domain.Notebook, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.CreateNotebook(a.ctx, name, color)
}

// ListNotebooks 返回当前工作目录中的 Notebook 列表。
func (a *App) ListNotebooks() ([]domain.Notebook, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return nil, errWorkspaceNotInitialized
	}

	return a.library.ListNotebooks(a.ctx)
}

// UpdateNotebook 更新指定 Notebook 的可编辑字段。
func (a *App) UpdateNotebook(id int64, name, color string) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.UpdateNotebook(a.ctx, id, name, color)
}

// DeleteNotebook 删除指定 Notebook 及其关联数据。
func (a *App) DeleteNotebook(id int64) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	if !a.workspaceOpen() {
		return errWorkspaceNotInitialized
	}

	return a.library.DeleteNotebook(a.ctx, id)
}
