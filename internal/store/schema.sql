
-- Notebook 元数据
CREATE TABLE IF NOT EXISTS notebooks (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     name TEXT NOT NULL,
     color TEXT NOT NULL
);

-- Section 元数据
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notebook_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    color TEXT NOT NULL
);

-- Page 元数据
CREATE TABLE IF NOT EXISTS pages (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     section_id INTEGER NOT NULL,
     title TEXT NOT NULL
);

-- 根据 Notebook ID 查询 Section
CREATE INDEX IF NOT EXISTS idx_sections_notebook_id
    ON sections(notebook_id);

-- 根据 Section ID 查询 Page
CREATE INDEX IF NOT EXISTS idx_pages_section_id
    ON pages(section_id);
