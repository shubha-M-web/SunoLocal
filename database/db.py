import sqlite3
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config

def get_db_connection():
    """Returns a SQLite connection with row factory configured for dict-like access."""
    db_path = Config.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _migrate_columns(conn):
    """Adds new columns to databases created before this upgrade. Safe to run repeatedly."""
    additions = {
        "user_preferences": {
            "profile_name": "TEXT DEFAULT 'Demo User'",
            "state": "TEXT DEFAULT 'Karnataka'",
            "user_type": "TEXT DEFAULT 'student'",
            "alert_prefs": "TEXT DEFAULT '{\"news\": true, \"deadlines\": true, \"schemes\": true}'",
        },
        "opportunities": {
            "who_can_benefit": "TEXT",
            "last_updated_date": "TEXT",
        },
        "news_articles": {
            "subcategory": "TEXT",
            "is_sample": "INTEGER DEFAULT 1",
            "fetched_at": "TEXT",
            "source_class": "TEXT DEFAULT 'demonstration'",
        },
    }
    for table, columns in additions.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, declaration in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
    conn.commit()


def init_db(force_recreate=False):
    """Initializes tables and indices."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_recreate:
        cursor.executescript("""
            DROP TABLE IF EXISTS notifications;
            DROP TABLE IF EXISTS recently_viewed_news;
            DROP TABLE IF EXISTS saved_news;
            DROP TABLE IF EXISTS news_articles;
            DROP TABLE IF EXISTS recently_viewed;
            DROP TABLE IF EXISTS saved_opportunities;
            DROP TABLE IF EXISTS opportunities;
            DROP TABLE IF EXISTS user_preferences;
            DROP TABLE IF EXISTS users;
        """)

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            location TEXT NOT NULL DEFAULT 'Mysuru',
            language TEXT NOT NULL DEFAULT 'English',
            interests TEXT NOT NULL DEFAULT '["Scholarships", "Internships", "Jobs"]',
            education_level TEXT NOT NULL DEFAULT 'Undergraduate (PUC / Diploma / Degree)',
            profile_name TEXT DEFAULT 'Demo User',
            state TEXT DEFAULT 'Karnataka',
            user_type TEXT DEFAULT 'student',
            alert_prefs TEXT DEFAULT '{"news": true, "deadlines": true, "schemes": true}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            kannada_title TEXT,
            category TEXT NOT NULL,
            organization TEXT NOT NULL,
            location TEXT NOT NULL,
            short_description TEXT NOT NULL,
            full_description TEXT NOT NULL,
            kannada_description TEXT,
            eligibility TEXT,
            requirements TEXT,
            deadline TEXT,
            publication_date TEXT,
            source_name TEXT,
            source_url TEXT,
            how_to_apply TEXT,
            who_can_benefit TEXT,
            last_updated_date TEXT,
            is_sample INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,
            last_checked_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS saved_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, opportunity_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS recently_viewed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            original_headline TEXT NOT NULL,
            publisher_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            publication_date TEXT NOT NULL,
            publication_time TEXT DEFAULT '10:00 AM IST',
            last_updated_date TEXT,
            location TEXT NOT NULL,
            is_official_government INTEGER DEFAULT 0,
            verification_status TEXT DEFAULT 'Source on record',
            original_language TEXT DEFAULT 'English',
            multilingual_content TEXT NOT NULL,
            subcategory TEXT,
            is_sample INTEGER DEFAULT 1,
            fetched_at TEXT,
            source_class TEXT DEFAULT 'demonstration',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS saved_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            news_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, news_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (news_id) REFERENCES news_articles (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS recently_viewed_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            news_id INTEGER NOT NULL,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (news_id) REFERENCES news_articles (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            link TEXT,
            ref_key TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ref_key),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    _migrate_columns(conn)

    # Ensure default demo user exists
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (id, username, name) VALUES (1, 'demo_student', 'Mysuru Student')")
        cursor.execute("""
            INSERT INTO user_preferences (user_id, location, language, interests, education_level)
            VALUES (1, 'Mysuru', 'English', ?, 'Undergraduate (PUC / Diploma / Degree)')
        """, (json.dumps(["Scholarships", "Internships", "Skill development"]),))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
