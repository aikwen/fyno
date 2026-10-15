package main

import (
	"embed"
	"log"

	"github.com/aikwen/fyno/internal/app"
	"github.com/aikwen/fyno/internal/config"
	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	// Create an instance of the app structure
	cfg, err := config.Load()
	if err != nil {
		log.Printf("load config: %v", err)
		return
	}
	application := app.NewApp(cfg)

	// Create application with options
	err = wails.Run(&options.App{
		Title:     "fyno",
		Width:     cfg.Window.Width,
		Height:    cfg.Window.Height,
		MinWidth:  960,
		MinHeight: 600,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{
			R: 232,
			G: 237,
			B: 241,
			A: 255,
		},
		OnStartup:     application.Startup,
		OnBeforeClose: application.BeforeClose,
		OnShutdown:    application.Shutdown,
		Bind: []interface{}{
			application,
		},
	})

	if err != nil {
		log.Printf("run wails: %v", err)
	}
}
