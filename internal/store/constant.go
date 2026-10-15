package store

// Fyno 数据根目录结构：
//
// rootDir/
// ├── fyno.db
// ├── meta/
// │   └── sort.json
// └── data/
//     └── <pageID>.json

const (
	databaseFile = "fyno.db"
	sortFile     = "sort.json"

	metaDir = "meta"
	dataDir = "data"
)
