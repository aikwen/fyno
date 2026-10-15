package atomicfile

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)

// ReplaceV1 使用同目录临时文件和 os.Rename 替换目标文件。
//
// 实现流程：
//  1. 在目标文件所在目录创建随机临时文件。
//  2. 写入完整数据，并执行 Sync 和 Close。
//  3. 使用 os.Rename 将临时文件替换为目标文件。
//  4. 操作失败时返回错误，并尝试清理临时文件。
//
// 约束：
//   - 目标目录必须已经存在。
//   - 目标文件可以不存在，此时会创建新文件。
//   - 不负责多个写入者之间的并发控制。
//   - 不保证所有平台和文件系统上的替换原子性。
//   - 不保证断电情况下目录项的持久化。
//   - 替换失败不会主动删除原目标文件。
func ReplaceV1(path string, data []byte) error {
	dir := filepath.Dir(path)

	tmp, err := os.CreateTemp(dir, ".atomic-*.tmp")
	if err != nil {
		return fmt.Errorf("create temporary file: %w", err)
	}

	tmpPath := tmp.Name()

	defer func() {
		_ = os.Remove(tmpPath)
	}()

	n, err := tmp.Write(data)
	if err != nil {
		_ = tmp.Close()
		return fmt.Errorf("write temporary file: %w", err)
	}

	if n != len(data) {
		_ = tmp.Close()
		return fmt.Errorf("write temporary file: %w", io.ErrShortWrite)
	}

	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return fmt.Errorf("sync temporary file: %w", err)
	}

	if err := tmp.Close(); err != nil {
		return fmt.Errorf("close temporary file: %w", err)
	}

	if err := os.Rename(tmpPath, path); err != nil {
		return fmt.Errorf("replace file %s: %w", path, err)
	}

	return nil
}
