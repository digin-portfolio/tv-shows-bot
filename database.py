import os
import psycopg2
import psycopg2.extras
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def _get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_id TEXT NOT NULL UNIQUE,
            file_type TEXT DEFAULT 'video',
            size_mb REAL DEFAULT 0,
            season INTEGER DEFAULT 0,
            episode INTEGER DEFAULT 0,
            added_by BIGINT DEFAULT 0,
            added_at TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT NOW(),
            last_active TIMESTAMP DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS pending_search (
            user_id BIGINT PRIMARY KEY,
            query TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_file(title, filename, file_id, file_type="video", size_mb=0, season=0, episode=0, added_by=0):
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO files (title, filename, file_id, file_type, size_mb, season, episode, added_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_id) DO UPDATE SET
                title=EXCLUDED.title, filename=EXCLUDED.filename,
                size_mb=EXCLUDED.size_mb, season=EXCLUDED.season, episode=EXCLUDED.episode
        """, (title, filename, file_id, file_type, size_mb, season, episode, added_by))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def search_files(query, limit=8):
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    like = f"%{query.strip().lower()}%"
    cur.execute("""
        SELECT * FROM files WHERE LOWER(title) LIKE %s OR LOWER(filename) LIKE %s
        ORDER BY season, episode LIMIT %s
    """, (like, like, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def get_file_by_id(file_db_id):
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM files WHERE id=%s", (file_db_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def get_all_files():
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM files ORDER BY added_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def delete_file(file_db_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE id=%s", (file_db_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True

def upsert_user(user_id, username="", first_name=""):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_active=NOW()
    """, (user_id, username or "", first_name or ""))
    conn.commit()
    cur.close()
    conn.close()

def get_all_user_ids():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def get_stats():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM files")
    files = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"total_files": files, "total_users": users}

def set_pending_search(user_id, query):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pending_search (user_id, query)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET query=EXCLUDED.query, created_at=NOW()
    """, (user_id, query))
    conn.commit()
    cur.close()
    conn.close()

def pop_pending_search(user_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT query FROM pending_search WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM pending_search WHERE user_id=%s", (user_id,))
        conn.commit()
    cur.close()
    conn.close()
    return row[0] if row else None
# ------------------ PENDING FILE STORAGE ------------------

_pending_files = {}

def set_pending_file(user_id, file_id):
    _pending_files[user_id] = file_id

def get_pending_file(user_id):
    return _pending_files.get(user_id)
