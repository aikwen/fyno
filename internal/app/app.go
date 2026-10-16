package app

import (
	"context"
	"fmt"
	"log"
	"sync"

	"github.com/aikwen/fyno/internal/config"
	"github.com/aikwen/fyno/internal/service"
	"github.com/aikwen/fyno/internal/store"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App 管理 Wails 生命周期并提供前端 Bridge 方法。
type App struct {
	ctx     context.Context
	config  *config.Config
	store   *store.Store
	library *service.LibraryService
	mu      sync.Mutex
}

// NewApp 使用解析后的配置数据创建 App。
func NewApp(data config.Data) *App {
	return &App{
		config: config.New(data),
	}
}

// Startup 在应用启动时保存 Wails context。
func (a *App) Startup(ctx context.Context) {
	a.ctx = ctx
}

// BeforeClose 在窗口仍然有效时记录普通状态下的窗口尺寸。
func (a *App) BeforeClose(ctx context.Context) bool {
	if a.config == nil || !runtime.WindowIsNormal(ctx) {
		return false
	}

	width, height := runtime.WindowGetSize(ctx)
	if width > 0 && height > 0 {
		if err := a.config.Update(func(data *config.Data) {
			data.Window.Width = width
			data.Window.Height = height
		}); err != nil {
			log.Printf("update window size: %v", err)
		}
	}
	return false
}

// Shutdown 先关闭 Workspace 资源，再保存完整配置。
func (a *App) Shutdown(ctx context.Context) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if err := a.closeWorkspace(); err != nil {
		log.Printf("close workspace on shutdown: %v", err)
	}

	if a.config == nil {
		return
	}
	if err := a.config.Save(); err != nil {
		log.Printf("save config on shutdown: %v", err)
	}
}

// Greet 返回指定名称的问候语。
func (a *App) Greet(name string) string {
	return fmt.Sprintf("Hello %s, It's show time!", name)
}
