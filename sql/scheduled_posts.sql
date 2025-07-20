    CREATE TABLE scheduled_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        video TEXT NOT NULL,
        script TEXT,
        scheduled_for TEXT NOT NULL,
        posted BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
