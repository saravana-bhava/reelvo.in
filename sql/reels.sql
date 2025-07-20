CREATE TABLE reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    filename TEXT,
    script TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    theme TEXT,
    language TEXT,
    tts_used BOOLEAN,
    voice TEXT
);
