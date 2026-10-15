package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/aikwen/fyno/internal/atomicfile"
)

const (
	appDir        = "Fyno"
	versionDir    = "v2"
	configFile    = "config.json"
	DefaultWidth  = 1280
	DefaultHeight = 800
)

type Window struct {
	Width  int `json:"width"`
	Height int `json:"height"`
}

// Config 保存 Fyno 应用配置及上次使用状态。
type Config struct {
	RootDir        string `json:"root_dir"`
	ActiveNotebook int64  `json:"active_notebook"`
	ActiveSection  int64  `json:"active_section"`
	ActivePage     int64  `json:"active_page"`
	Window         Window `json:"window"`
}

// Default 返回 Fyno 的默认配置。
func Default() *Config {
	return &Config{
		Window: Window{
			Width:  DefaultWidth,
			Height: DefaultHeight,
		},
	}
}

// Load 从当前用户的配置目录读取 Fyno 配置。
// 文件不存在时只返回默认配置；JSON 损坏时保存并返回默认配置。
// 本方法不校验配置中的路径和 ID。
func Load() (*Config, error) {
	baseDir, err := os.UserConfigDir()
	if err != nil {
		return nil, fmt.Errorf("load config: get user config directory: %w", err)
	}

	path := filepath.Join(baseDir, appDir, versionDir, configFile)
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return Default(), nil
		}
		return nil, fmt.Errorf("load config: read file: %w", err)
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		defaultConfig := Default()
		if saveErr := Save(defaultConfig); saveErr != nil {
			return nil, fmt.Errorf("load config: recover invalid JSON: %w", saveErr)
		}
		return defaultConfig, nil
	}

	return &cfg, nil
}

// Save 将 Fyno 配置格式化后原子保存到当前用户的配置目录。
// 本方法只负责配置文件持久化，不初始化 RootDir，也不访问 SQLite。
func Save(cfg *Config) error {
	if cfg == nil {
		return fmt.Errorf("save config: config must not be nil")
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return fmt.Errorf("save config: marshal JSON: %w", err)
	}

	baseDir, err := os.UserConfigDir()
	if err != nil {
		return fmt.Errorf("save config: get user config directory: %w", err)
	}

	dir := filepath.Join(baseDir, appDir, versionDir)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("save config: create directory: %w", err)
	}

	path := filepath.Join(dir, configFile)
	if err := atomicfile.ReplaceV1(path, data); err != nil {
		return fmt.Errorf("save config: %w", err)
	}

	return nil
}
