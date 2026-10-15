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
	appDir     = "Fyno"
	versionDir = "v2"
	configFile = "config.json"
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

// Load 从当前用户的配置目录读取 Fyno 配置。
// 配置文件不存在时返回零值配置，不创建文件，也不校验其中的路径和 ID。
func Load() (*Config, error) {
	baseDir, err := os.UserConfigDir()
	if err != nil {
		return nil, fmt.Errorf("load config: get user config directory: %w", err)
	}

	path := filepath.Join(baseDir, appDir, versionDir, configFile)
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return &Config{}, nil
		}
		return nil, fmt.Errorf("load config: read file: %w", err)
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("load config: unmarshal JSON: %w", err)
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
