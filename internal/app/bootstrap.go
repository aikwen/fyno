package app

import (
	"errors"
	"fmt"
	"io/fs"
	"log"
	"strings"

	"github.com/aikwen/fyno/internal/config"
	"github.com/aikwen/fyno/internal/service"
	"github.com/aikwen/fyno/internal/store"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// WorkspaceResult 描述前端应进入 Welcome 还是 Workspace。
type WorkspaceResult struct {
	Ready   bool   `json:"ready"`
	RootDir string `json:"rootDir"`
	Error   string `json:"error"`
}

// SelectDirectory 打开系统目录选择器，返回用户选择的目录。
func (a *App) SelectDirectory() (string, error) {
	return runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "选择 Fyno 工作目录",
	})
}

// GetStartupState 恢复配置中记录的工作目录。
func (a *App) GetStartupState() WorkspaceResult {
	a.mu.Lock()
	defer a.mu.Unlock()

	rootDir := a.config.Get().RootDir
	if rootDir == "" {
		return WorkspaceResult{}
	}
	if a.workspaceOpen() {
		return workspaceReady(rootDir)
	}

	workspaceStore, library, err := openService(rootDir)
	if err != nil {
		log.Printf("open startup workspace %q: %v", rootDir, err)
		return workspaceFailure(rootDir, workspaceErrorMessage(err, "工作目录加载失败"))
	}

	a.store = workspaceStore
	a.library = library
	return workspaceReady(rootDir)
}

// OpenService 初始化或打开指定工作目录，并替换当前 LibraryService。
func (a *App) OpenService(rootDir string) WorkspaceResult {
	if strings.TrimSpace(rootDir) == "" {
		return workspaceFailure(rootDir, "未选择工作目录")
	}

	a.mu.Lock()
	defer a.mu.Unlock()

	if a.workspaceOpen() && a.config.Get().RootDir == rootDir {
		return workspaceReady(rootDir)
	}

	workspaceStore, library, err := openService(rootDir)
	if err != nil {
		log.Printf("open workspace %q: %v", rootDir, err)
		return workspaceFailure(rootDir, workspaceErrorMessage(err, "工作目录初始化失败"))
	}

	oldStore := a.store
	oldLibrary := a.library
	a.store = workspaceStore
	a.library = library

	if err := closeWorkspaceResources(oldLibrary, oldStore); err != nil {
		log.Printf("close previous workspace after switching to %q: %v", rootDir, err)
	}

	configErr := a.config.Update(func(data *config.Data) {
		data.RootDir = rootDir
	})
	if configErr != nil {
		log.Printf("save workspace config %q: %v", rootDir, configErr)
	}

	result := workspaceReady(rootDir)
	if configErr != nil {
		result.Error = "配置保存失败"
	}
	return result
}

// openService 创建一套独立的 Store 和 LibraryService。
func openService(rootDir string) (*store.Store, *service.LibraryService, error) {
	workspaceStore, err := store.Open(rootDir)
	if err != nil {
		return nil, nil, fmt.Errorf("open workspace store: %w", err)
	}

	library, err := service.NewLibraryService(workspaceStore)
	if err != nil {
		if closeErr := workspaceStore.Close(); closeErr != nil {
			log.Printf("close workspace store %q after service failure: %v", rootDir, closeErr)
		}
		return nil, nil, fmt.Errorf("initialize workspace service: %w", err)
	}

	return workspaceStore, library, nil
}

// closeWorkspace 按 LibraryService、Store 的顺序关闭当前工作目录。
func (a *App) closeWorkspace() error {
	err := closeWorkspaceResources(a.library, a.store)
	a.library = nil
	a.store = nil
	return err
}

func closeWorkspaceResources(library *service.LibraryService, workspaceStore *store.Store) error {
	var firstErr error
	if library != nil {
		if err := library.Close(); err != nil {
			firstErr = fmt.Errorf("close library service: %w", err)
		}
	}
	if workspaceStore != nil {
		if err := workspaceStore.Close(); err != nil && firstErr == nil {
			firstErr = fmt.Errorf("close store: %w", err)
		}
	}
	return firstErr
}

func (a *App) workspaceOpen() bool {
	return a.store != nil && a.library != nil
}

func workspaceReady(rootDir string) WorkspaceResult {
	return WorkspaceResult{Ready: true, RootDir: rootDir}
}

func workspaceFailure(rootDir, message string) WorkspaceResult {
	return WorkspaceResult{RootDir: rootDir, Error: message}
}

func workspaceErrorMessage(err error, fallback string) string {
	switch {
	case errors.Is(err, fs.ErrNotExist):
		return "工作目录不存在"
	case errors.Is(err, fs.ErrPermission):
		return "目录访问权限不足"
	case errors.Is(err, store.ErrCorruptedData):
		return "工作目录结构或数据库异常"
	default:
		return fallback
	}
}
