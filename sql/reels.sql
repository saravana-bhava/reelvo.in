CREATE TABLE IF NOT EXISTS reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    script TEXT NOT NULL,
    caption TEXT NOT NULL,
    video_path TEXT NOT NULL,
    audio_path TEXT,
    thumbnail_path TEXT,
    theme_name TEXT,
    lang TEXT DEFAULT 'en',
    is_scheduled BOOLEAN DEFAULT 0,
    scheduled_at DATETIME,
    posted_at DATETIME,
    platform TEXT DEFAULT 'instagram',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'posted', 'failed')),
    error_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_reels_user ON reels(user_id);
CREATE INDEX IF NOT EXISTS idx_reels_schedule ON reels(is_scheduled, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_reels_status ON reels(status);
