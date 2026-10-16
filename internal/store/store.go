package store

import (
	"database/sql"
	_ "embed"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

//go:embed schema.sql
var schema string

// Store 统一管理 Fyno 的数据库和文件持久化。
type Store struct {
	rootDir string
	db      *sql.DB
}

// Open 初始化或校验 Fyno 数据根目录，并返回可用的 Store。
//
// 规则：
//   - RootDir 必须存在且为目录。
//   - 空目录或仅包含点号开头的项目时，初始化 Fyno 存储结构。
//   - 已有目录必须恰好包含 fyno.db、meta/ 和 data/。
//   - 已有数据库必须通过完整性检查，且包含三张业务表。
//   - 已有数据不会被覆盖，也不会自动修复。
func Open(rootDir string) (s *Store, err error) {
	candidate := &Store{rootDir: rootDir}
	s = candidate
	defer func() {
		if err != nil {
			_ = candidate.Close()
			s = nil
		}
	}()

	names, err := s.rootEntries()
	if err != nil {
		return nil, err
	}

	// 新目录：初始化 Fyno 存储环境。
	if len(names) == 0 {
		if err := s.initDirectories(); err != nil {
			return nil, err
		}
		if err := s.openDatabase(true); err != nil {
			return nil, err
		}
		return s, nil
	}

	// 已有目录：严格校验，不执行自动修复。
	if err := s.validateDirectories(names); err != nil {
		return nil, err
	}
	if err := s.openDatabase(false); err != nil {
		return nil, err
	}
	return s, nil
}

func (s *Store) rootEntries() ([]string, error) {
	info, err := os.Stat(s.rootDir)
	if err != nil {
		return nil, fmt.Errorf("stat root directory: %w", err)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("root path is not a directory: %s", s.rootDir)
	}

	entries, err := os.ReadDir(s.rootDir)
	if err != nil {
		return nil, fmt.Errorf("read root directory: %w", err)
	}

	var names []string
	for _, entry := range entries {
		if !strings.HasPrefix(entry.Name(), ".") {
			names = append(names, entry.Name())
		}
	}
	return names, nil
}

// initDirectories 创建全新的 Fyno 存储目录。
func (s *Store) initDirectories() error {
	for _, name := range []string{metaDir, dataDir} {
		path := filepath.Join(s.rootDir, name)

		if err := os.Mkdir(path, 0755); err != nil {
			return fmt.Errorf("create directory %s: %w", name, err)
		}
	}

	return nil
}

// validateDirectories 严格校验已有 Fyno 数据目录。
func (s *Store) validateDirectories(names []string) error {
	expected := map[string]bool{
		databaseFile: false,
		metaDir:      false,
		dataDir:      false,
	}

	for _, name := range names {
		if _, ok := expected[name]; !ok {
			return fmt.Errorf("%w: unexpected entry %s", ErrCorruptedData, name)
		}
		expected[name] = true
	}

	for name, exists := range expected {
		if !exists {
			return fmt.Errorf("%w: missing %s", ErrCorruptedData, name)
		}
	}

	// 校验数据库为普通文件，meta/data 为目录。
	for _, name := range []string{metaDir, dataDir} {
		path := filepath.Join(s.rootDir, name)

		info, err := os.Stat(path)
		if err != nil {
			return fmt.Errorf("stat %s: %w", name, err)
		}
		if !info.IsDir() {
			return fmt.Errorf("%w: %s is not a directory", ErrCorruptedData, name)
		}
	}

	dbPath := filepath.Join(s.rootDir, databaseFile)

	info, err := os.Stat(dbPath)
	if err != nil {
		return fmt.Errorf("stat database: %w", err)
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("%w: database is not a regular file", ErrCorruptedData)
	}

	return nil
}

// openDatabase 打开 SQLite 数据库。
// create 为 true 时初始化 Schema，否则仅校验已有数据库。
func (s *Store) openDatabase(create bool) error {
	path := filepath.Join(s.rootDir, databaseFile)

	// 已有数据库使用 mode=rw，禁止 SQLite 意外创建新文件。
	dsn := path
	if !create {
		dsn = "file:" + filepath.ToSlash(path) + "?mode=rw"
	}

	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return fmt.Errorf("open database: %w", err)
	}

	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)

	// sql.Open 不保证立即建立连接。
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return fmt.Errorf("connect database: %w", err)
	}

	if create {
		if _, err := db.Exec(schema); err != nil {
			_ = db.Close()
			return fmt.Errorf("initialize database schema: %w", err)
		}
	} else {
		if err := validateDatabase(db); err != nil {
			_ = db.Close()
			return err
		}
	}

	s.db = db
	return nil
}

// validateDatabase 检查数据库完整性及必要表结构。
func validateDatabase(db *sql.DB) error {
	var result string

	if err := db.QueryRow("PRAGMA quick_check").Scan(&result); err != nil {
		return fmt.Errorf("%w: database integrity check failed: %v",
			ErrCorruptedData, err)
	}

	if result != "ok" {
		return fmt.Errorf("%w: database integrity check: %s",
			ErrCorruptedData, result)
	}

	rows, err := db.Query(`
		SELECT name
		FROM sqlite_master
		WHERE type = 'table'
		  AND name IN ('notebooks', 'sections', 'pages')
	`)
	if err != nil {
		return fmt.Errorf("%w: query database schema: %v",
			ErrCorruptedData, err)
	}
	defer func() {
		_ = rows.Close()
	}()

	tables := make(map[string]bool)

	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return fmt.Errorf("scan database table: %w", err)
		}
		tables[name] = true
	}

	if err := rows.Err(); err != nil {
		return fmt.Errorf("iterate database tables: %w", err)
	}

	for _, name := range []string{
		"notebooks",
		"sections",
		"pages",
	} {
		if !tables[name] {
			return fmt.Errorf("%w: missing table %s", ErrCorruptedData, name)
		}
	}

	return nil
}

// Close 关闭 SQLite 数据库连接。
func (s *Store) Close() error {
	if s.db == nil {
		return nil
	}

	if err := s.db.Close(); err != nil {
		return fmt.Errorf("close database: %w", err)
	}

	s.db = nil
	return nil
}
