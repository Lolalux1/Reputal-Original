"""
Database layer for Reputal.
Uses SQLite for simplicity — swap the connection string for Postgres later
if you outgrow it (the SQL here is close to standard, minimal changes needed).
"""
import sqlite3
from datetime import datetime, timezone

DB_PATH = "reviewpilot.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables if they don't already exist. Safe to run every startup."""
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tone TEXT DEFAULT 'warm and professional',
            zernio_account_id TEXT,
            auto_post INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            external_review_id TEXT NOT NULL,
            author_name TEXT,
            rating INTEGER,
            review_text TEXT,
            drafted_reply TEXT,
            status TEXT DEFAULT 'new',
            fetched_at TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id),
            UNIQUE(restaurant_id, external_review_id)
        );
        """
    )
    conn.commit()
    conn.close()


def now():
    return datetime.now(timezone.utc).isoformat()


def create_restaurant(name, email, password_hash):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO restaurants (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, now()),
    )
    conn.commit()
    restaurant_id = cur.lastrowid
    conn.close()
    return restaurant_id


def get_restaurant_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM restaurants WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_restaurant_by_id(restaurant_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    conn.close()
    return row


def update_restaurant_settings(restaurant_id, tone, auto_post):
    conn = get_db()
    conn.execute(
        "UPDATE restaurants SET tone = ?, auto_post = ? WHERE id = ?",
        (tone, int(auto_post), restaurant_id),
    )
    conn.commit()
    conn.close()


def set_zernio_account(restaurant_id, zernio_account_id):
    conn = get_db()
    conn.execute(
        "UPDATE restaurants SET zernio_account_id = ? WHERE id = ?",
        (zernio_account_id, restaurant_id),
    )
    conn.commit()
    conn.close()


def save_new_review(restaurant_id, external_review_id, author_name, rating, review_text):
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO reviews
               (restaurant_id, external_review_id, author_name, rating, review_text, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (restaurant_id, external_review_id, author_name, rating, review_text, now()),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def save_draft_reply(review_id, drafted_reply):
    conn = get_db()
    conn.execute(
        "UPDATE reviews SET drafted_reply = ?, status = 'drafted' WHERE id = ?",
        (drafted_reply, review_id),
    )
    conn.commit()
    conn.close()


def mark_posted(review_id):
    conn = get_db()
    conn.execute("UPDATE reviews SET status = 'posted' WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()


def get_reviews_for_restaurant(restaurant_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE restaurant_id = ? ORDER BY fetched_at DESC",
        (restaurant_id,),
    ).fetchall()
    conn.close()
    return rows


def get_review_by_id(review_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    return row


def get_all_restaurants_with_zernio():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM restaurants WHERE zernio_account_id IS NOT NULL"
    ).fetchall()
    conn.close()
    return rows
