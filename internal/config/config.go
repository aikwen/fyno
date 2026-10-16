package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sync"

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

// Data 保存 Fyno 应用配置及上次使用状态。
type Data struct {
	RootDir        string `json:"root_dir"`
	ActiveNotebook int64  `json:"active_notebook"`
	ActiveSection  int64  `json:"active_section"`
	ActivePage     int64  `json:"active_page"`
	Window         Window `json:"window"`
}

// Config 并发安全地管理运行时配置及其持久化。
type Config struct {
	mu   sync.RWMutex
	data Data
}

// Default 返回 Fyno 的默认配置数据。
func Default() Data {
	return Data{
		Window: Window{
			Width:  DefaultWidth,
			Height: DefaultHeight,
		},
	}
}

// New 使用配置数据创建运行时 Config。
func New(data Data) *Config {
	return &Config{data: data}
}

// Parse 从当前用户的配置目录解析 Fyno 配置数据。
// 文件不存在时返回默认数据；JSON 损坏时保存并返回默认数据。
func Parse() (Data, error) {
	baseDir, err := os.UserConfigDir()
	if err != nil {
		return Data{}, fmt.Errorf("parse config: get user config directory: %w", err)
	}

	path := filepath.Join(baseDir, appDir, versionDir, configFile)
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			return Default(), nil
		}
		return Data{}, fmt.Errorf("parse config: read file: %w", err)
	}

	var configData Data
	if err := json.Unmarshal(data, &configData); err != nil {
		defaultData := Default()
		if saveErr := saveData(defaultData); saveErr != nil {
			return Data{}, fmt.Errorf("parse config: recover invalid JSON: %w", saveErr)
		}
		return defaultData, nil
	}

	return configData, nil
}

// Get 返回当前内存配置的独立值副本。
func (c *Config) Get() Data {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.data
}

// Update 在写锁内更新内存配置并自动持久化。
// 持久化失败时，已更新的内存状态仍然保留。
// update 回调在持有写锁期间同步执行，只能修改传入的 Data；
// 不得在回调中调用同一 Config 的 Get、Update 或 Save，否则会因锁不可重入而死锁。
func (c *Config) Update(update func(*Data)) error {
	if c == nil {
		return fmt.Errorf("update config: config must not be nil")
	}
	if update == nil {
		return fmt.Errorf("update config: update function must not be nil")
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	next := c.data
	update(&next)
	c.data = next
	if err := c.save(); err != nil {
		return fmt.Errorf("update config: %w", err)
	}
	return nil
}

// Save 在写锁内将当前内存配置原子保存到用户配置目录。
func (c *Config) Save() error {
	if c == nil {
		return fmt.Errorf("save config: config must not be nil")
	}

	c.mu.Lock()
	defer c.mu.Unlock()
	return c.save()
}

// save 保存当前配置，不自行加锁。
// 调用方必须持有 Config 的写锁。
func (c *Config) save() error {
	return saveData(c.data)
}

func saveData(configData Data) error {
	data, err := json.MarshalIndent(configData, "", "  ")
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
