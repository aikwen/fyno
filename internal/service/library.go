package service

import (
	"fmt"
	"strings"
	"unicode/utf8"

	"github.com/aikwen/fyno/internal/store"
)

const maxTextRunes = 50

// LibraryService 协调 Library 元数据、正文文件和辅助排序数据。
type LibraryService struct {
	store *store.Store
	sort  *SortService
}

// NewLibraryService 创建 Library 服务及其排序服务。
func NewLibraryService(s *store.Store) (*LibraryService, error) {
	sortService, err := NewSortService(s)
	if err != nil {
		return nil, fmt.Errorf("create library service: %w", err)
	}

	return &LibraryService{
		store: s,
		sort:  sortService,
	}, nil
}

// Close 停止排序服务并保存尚未持久化的最新排序。
func (s *LibraryService) Close() error {
	return s.sort.Close()
}

func validateID(name string, id int64) error {
	if id <= 0 {
		return fmt.Errorf("%s ID must be greater than zero", name)
	}
	return nil
}

func normalizeText(name, value string) (string, error) {
	value = strings.TrimSpace(value)
	if value == "" {
		return "", fmt.Errorf("%s must not be empty", name)
	}
	if utf8.RuneCountInString(value) > maxTextRunes {
		return "", fmt.Errorf("%s must not exceed %d characters", name, maxTextRunes)
	}
	return value, nil
}
