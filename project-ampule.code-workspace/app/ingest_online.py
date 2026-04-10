import hashlib
import re
import sqlite3
from datetime import datetime

try:
    from .config import CACHE_DIR, DB_PATH, DOCS_DIR
    from .sources.survival import iter_survival_documents
    from .sources.wikipedia import iter_medical_wikipedia_documents
except ImportError:
    from config import CACHE_DIR, DB_PATH, DOCS_DIR
    from sources.survival import iter_survival_documents
    from sources.wikipedia import iter_medical_wikipedia_documents

DOCS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        source TEXT,
        content TEXT,
        hash TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    return conn

def safe_filename(source_name):
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "_", source_name).strip("._")
    return sanitized or "document"

def write_raw_cache(source_name, text):
    cache_path = CACHE_DIR / f"{safe_filename(source_name)}.txt"
    cache_path.write_text(text, encoding="utf-8")
    return cache_path

def sync_local_documents(conn):
    for path in sorted(DOCS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            add_or_update_document(conn, f"local:{path.name}", text, cache_raw=False)

def add_or_update_document(conn, source_name, text, cache_raw=True):
    h = hash_text(text)
    if cache_raw:
        write_raw_cache(source_name, text)

    cur = conn.cursor()
    cur.execute("SELECT id, hash FROM documents WHERE source=?", (source_name,))
    row = cur.fetchone()
    if row:
        if row[1] != h:
            cur.execute("UPDATE documents SET content=?, hash=?, updated_at=? WHERE id=?",
                        (text, h, datetime.now(), row[0]))
            print(f"Updated {source_name}")
        else:
            print(f"Unchanged {source_name}")
    else:
        cur.execute("INSERT INTO documents (source, content, hash) VALUES (?, ?, ?)",
                    (source_name, text, h))
        print(f"Added {source_name}")
    conn.commit()

def main():
    conn = init_db()
    try:
        sync_local_documents(conn)

        for source_name, text in iter_survival_documents():
            add_or_update_document(conn, source_name, text)

        for source_name, text in iter_medical_wikipedia_documents():
            add_or_update_document(conn, source_name, text)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
