package store

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"

	"github.com/aikwen/fyno/internal/atomicfile"
)

// documentPath 校验 Document ID，并返回对应的正文文件路径。
func (s *Store) documentPath(id int64) (string, error) {
	if id <= 0 {
		return "", fmt.Errorf("document ID must be greater than zero")
	}

	filename := strconv.FormatInt(id, 10) + ".json"
	return filepath.Join(s.rootDir, dataDir, filename), nil
}

// LoadDocument 从 data 目录读取正文，只校验 JSON 语法。
// 本方法不查询 SQLite，也不会在文件不存在时创建默认正文。
func (s *Store) LoadDocument(id int64) (json.RawMessage, error) {
	path, err := s.documentPath(id)
	if err != nil {
		return nil, fmt.Errorf("load document %d: %w", id, err)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("load document %d: %w", id, err)
	}

	if !json.Valid(data) {
		return nil, fmt.Errorf("load document %d: invalid JSON", id)
	}

	return json.RawMessage(data), nil
}

// SaveDocument 使用原子替换保存正文，只校验 JSON 语法。
// 本方法不创建 data 目录，也不更新 SQLite Page 元数据。
func (s *Store) SaveDocument(id int64, content json.RawMessage) error {
	path, err := s.documentPath(id)
	if err != nil {
		return fmt.Errorf("save document %d: %w", id, err)
	}

	if !json.Valid(content) {
		return fmt.Errorf("save document %d: invalid JSON", id)
	}

	if err := atomicfile.ReplaceV1(path, content); err != nil {
		return fmt.Errorf("save document %d: %w", id, err)
	}

	return nil
}

// CreateDocumentIfAbsent 仅在正文文件不存在时安全创建，不覆盖已有内容。
// 本方法不创建 data 目录，也不修改 SQLite Page 元数据。
func (s *Store) CreateDocumentIfAbsent(id int64, content json.RawMessage) error {
	path, err := s.documentPath(id)
	if err != nil {
		return fmt.Errorf("create document %d if absent: %w", id, err)
	}

	if !json.Valid(content) {
		return fmt.Errorf("create document %d if absent: invalid JSON", id)
	}

	tmp, err := os.CreateTemp(filepath.Dir(path), ".document-*.tmp")
	if err != nil {
		return fmt.Errorf("create document %d if absent: create temporary file: %w", id, err)
	}

	tmpPath := tmp.Name()
	defer func() {
		_ = os.Remove(tmpPath)
	}()

	n, err := tmp.Write(content)
	if err != nil {
		_ = tmp.Close()
		return fmt.Errorf("create document %d if absent: write temporary file: %w", id, err)
	}
	if n != len(content) {
		_ = tmp.Close()
		return fmt.Errorf("create document %d if absent: write temporary file: %w", id, io.ErrShortWrite)
	}

	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return fmt.Errorf("create document %d if absent: sync temporary file: %w", id, err)
	}
	if err := tmp.Close(); err != nil {
		return fmt.Errorf("create document %d if absent: close temporary file: %w", id, err)
	}

	if err := os.Link(tmpPath, path); err != nil {
		return fmt.Errorf("create document %d if absent: publish file: %w", id, err)
	}

	return nil
}

// DeleteDocument 删除指定正文文件，不修改 SQLite Page 元数据。
func (s *Store) DeleteDocument(id int64) error {
	path, err := s.documentPath(id)
	if err != nil {
		return fmt.Errorf("delete document %d: %w", id, err)
	}

	if err := os.Remove(path); err != nil {
		return fmt.Errorf("delete document %d: %w", id, err)
	}

	return nil
}
