package domain

type Page struct {
	ID        int64  `json:"id"`
	SectionID int64  `json:"section_id"`
	Title     string `json:"title"`
}
