CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reel_id INTEGER NOT NULL,
    scheduled_for DATETIME NOT NULL,
    timezone TEXT DEFAULT 'Asia/Kolkata',
    retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'posted', 'failed')),
    error_log TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reel_id) REFERENCES reels(id)
);

CREATE INDEX IF NOT EXISTS idx_schedule_time ON schedules(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_schedule_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedule_user ON schedules(user_id);
