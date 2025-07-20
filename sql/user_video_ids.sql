CREATE TABLE used_video_ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT, -- "pexels" or "pixabay"
    video_id INTEGER,
    theme TEXT,
    created_at TEXT
);
