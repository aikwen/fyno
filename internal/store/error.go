package store

import "errors"

// ErrCorruptedData 表示已有 Fyno 数据结构不符合预期。
var ErrCorruptedData = errors.New("corrupted Fyno source data")
