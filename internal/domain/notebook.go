package domain

// Notebook 表示笔记本元数据。
// Section 通过 NotebookID 关联，排序由 meta/sort.json 管理。
type Notebook struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Color string `json:"color"`
}
