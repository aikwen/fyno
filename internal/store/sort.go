package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/aikwen/fyno/internal/atomicfile"
)

// Sort 保存 Notebook、Section 和 Page 的显示顺序。
// map 的键分别是 Notebook ID 和 Section ID。
type Sort struct {
	Notebooks []int64           `json:"notebooks"`
	Sections  map[int64][]int64 `json:"sections"`
	Pages     map[int64][]int64 `json:"pages"`
}

// LoadSort 从 meta 目录读取排序文件，只负责 JSON 反序列化。
// 本方法不查询 SQLite，也不补齐、清理或校验排序中的 ID。
func (s *Store) LoadSort() (*Sort, error) {
	path := filepath.Join(s.rootDir, metaDir, sortFile)

	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("load sort: %w", err)
	}

	var sort *Sort
	if err := json.Unmarshal(data, &sort); err != nil {
		return nil, fmt.Errorf("load sort: unmarshal JSON: %w", err)
	}

	return sort, nil
}

// SaveSort 将排序数据格式化后原子保存到 meta 目录。
// 本方法不创建 meta 目录，不检查 ID，也不修改 SQLite。
func (s *Store) SaveSort(sort *Sort) error {
	if sort == nil {
		return fmt.Errorf("save sort: sort must not be nil")
	}

	data, err := json.MarshalIndent(sort, "", "  ")
	if err != nil {
		return fmt.Errorf("save sort: marshal JSON: %w", err)
	}

	path := filepath.Join(s.rootDir, metaDir, sortFile)
	if err := atomicfile.ReplaceV1(path, data); err != nil {
		return fmt.Errorf("save sort: %w", err)
	}

	return nil
}
