CREATE TABLE IF NOT EXISTS reel_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    video TEXT NOT NULL,
    filename TEXT NOT NULL,
    script TEXT,
    caption TEXT,
    permalink TEXT,
    timestamp TEXT,
);
