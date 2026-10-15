package domain

// Section 表示 Notebook 下的笔记分区。
type Section struct {
	ID         int64  `json:"id"`
	NotebookID int64  `json:"notebook_id"`
	Name       string `json:"name"`
	Color      string `json:"color"`
}
