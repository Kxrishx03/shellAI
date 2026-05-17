import sqlite3
import json
import os
import re
import hashlib
import uuid
from datetime import datetime
from typing import Optional

from config import SHELLAI_DIR, DB_PATH, SEED_PATH, COMMANDS_JSON_PATH

# ── Memory cache ──────────────────────────────────────────────────────────────
# Keyed by (normalized_query, os_id) tuple
# Lives for duration of this process only — no expiry needed
_cache: dict = {}
_session_id = str(uuid.uuid4())[:8]

# Stop words stripped before keyword matching
STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "to", "in", "with",
    "of", "on", "at", "by", "from", "into", "how", "what", "my",
    "i", "me", "we", "it", "is", "are", "do", "does", "please",
    "can", "could", "would", "should", "want", "need", "set",
    "up", "just", "all", "new", "get", "some", "using", "make"
}


def _tokenize(text: str) -> list:
    """Extract meaningful keywords from a string."""
    words = re.findall(r'[a-z0-9]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def _normalize(query: str) -> str:
    """Normalize query for use as a cache key."""
    return " ".join(sorted(_tokenize(query)))


def _entry_hash(intent: str, os_id: str) -> str:
    """Stable 8-character hash ID for a command entry."""
    key = f"{intent.strip().lower()}:{os_id}"
    return hashlib.md5(key.encode()).hexdigest()[:8]


# ── Connection ────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    """
    Open a database connection with safe concurrent-access settings.
    WAL mode lets multiple readers access the database simultaneously
    without blocking each other — important when multiple shellai
    processes run at the same time.
    """
    os.makedirs(SHELLAI_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# ── Initialization ────────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables if they do not exist.
    Called automatically on first import.
    Safe to call multiple times.
    """
    conn = _connect()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS commands (
                id            TEXT PRIMARY KEY,
                intent        TEXT NOT NULL,
                tags          TEXT NOT NULL DEFAULT '[]',
                os            TEXT NOT NULL DEFAULT 'all',
                commands_json TEXT NOT NULL,
                summary       TEXT NOT NULL DEFAULT '',
                usage_count   INTEGER DEFAULT 0,
                last_used     TEXT,
                source        TEXT DEFAULT 'seed',
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pending (
                id             TEXT PRIMARY KEY,
                intent         TEXT NOT NULL,
                tags           TEXT NOT NULL DEFAULT '[]',
                os             TEXT NOT NULL DEFAULT 'all',
                commands_json  TEXT NOT NULL,
                summary        TEXT NOT NULL DEFAULT '',
                original_query TEXT,
                source         TEXT DEFAULT 'ollama',
                created_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usage_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT NOT NULL,
                query      TEXT NOT NULL,
                used_at    TEXT NOT NULL,
                session_id TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_commands_os
                ON commands(os);
            CREATE INDEX IF NOT EXISTS idx_commands_usage
                ON commands(usage_count DESC);
            CREATE INDEX IF NOT EXISTS idx_pending_created
                ON pending(created_at DESC);
        """)
        conn.commit()
    finally:
        conn.close()

    _maybe_seed()


def _maybe_seed() -> None:
    """
    Populate the database from seed files if it is empty.
    Checks seed.sql first, then falls back to commands.json.
    This gives new users a working database immediately.
    """
    conn = _connect()
    try:
        count = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
        if count > 0:
            return

        if os.path.exists(SEED_PATH):
            with open(SEED_PATH) as f:
                conn.executescript(f.read())
            conn.commit()
            return

        if os.path.exists(COMMANDS_JSON_PATH):
            with open(COMMANDS_JSON_PATH) as f:
                entries = json.load(f)
            _bulk_insert(conn, entries, source="seed")
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _bulk_insert(conn: sqlite3.Connection, entries: list, source: str = "seed") -> int:
    """Insert a list of entry dicts. Returns count of newly inserted rows."""
    inserted = 0
    now = datetime.now().isoformat()

    for entry in entries:
        intent = entry.get("intent", "").strip().lower()
        os_id = entry.get("os", "all")
        if not intent:
            continue

        entry_id = entry.get("id") or _entry_hash(intent, os_id)
        tags = json.dumps(entry.get("tags", _tokenize(intent)))
        commands = json.dumps(entry.get("commands", []))
        summary = entry.get("summary", "")

        try:
            conn.execute(
                """INSERT OR IGNORE INTO commands
                   (id, intent, tags, os, commands_json, summary, source, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (entry_id, intent, tags, os_id, commands, summary, source, now)
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                inserted += 1
        except sqlite3.Error:
            continue

    return inserted


# ── Search ────────────────────────────────────────────────────────────────────

def search(query: str, os_id: str = "ubuntu") -> Optional[dict]:
    """
    Search for commands matching a query.

    Checks memory cache first (Level 1).
    Falls through to SQLite keyword search (Level 2).
    Returns None if no confident match found.
    """
    if not query or not query.strip():
        return None

    cache_key = (_normalize(query), os_id)

    # Level 1: memory cache
    if cache_key in _cache:
        return _cache[cache_key]

    # Level 2: SQLite
    result = _db_search(query, os_id)

    if result:
        _cache[cache_key] = result
        _record_usage(result["_id"], query)

    return result


def _db_search(query: str, os_id: str) -> Optional[dict]:
    """
    Keyword-based search over the commands table.

    Scores each entry by how many query keywords appear in its
    intent and tags. Returns the highest-scoring entry above
    the SIMILARITY_THRESHOLD defined in config.py.
    """
    from config import SIMILARITY_THRESHOLD

    keywords = _tokenize(query)
    if not keywords:
        return None

    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT id, intent, tags, os, commands_json, summary, usage_count
               FROM commands
               WHERE os IN ('all', ?)
               ORDER BY usage_count DESC
               LIMIT 300""",
            (os_id,)
        ).fetchall()

        best_row = None
        best_score = 0.0

        for row in rows:
            intent_words = set(_tokenize(row["intent"]))
            tag_words = set()

            try:
                for tag in json.loads(row["tags"]):
                    tag_words.update(_tokenize(str(tag)))
            except (json.JSONDecodeError, TypeError):
                pass

            entry_words = intent_words | tag_words
            query_words = set(keywords)

            if not entry_words:
                continue

            overlap = query_words & entry_words
            base_score = len(overlap) / len(query_words)

            # Bonus for exact phrase match
            if query.lower().strip() in row["intent"]:
                base_score = min(1.0, base_score + 0.3)

            # Small popularity boost
            popularity = min(0.1, row["usage_count"] * 0.005)
            score = min(1.0, base_score + popularity)

            if score > best_score:
                best_score = score
                best_row = row

        if best_score < SIMILARITY_THRESHOLD or best_row is None:
            return None

        return {
            "_id":        best_row["id"],
            "commands":   json.loads(best_row["commands_json"]),
            "summary":    best_row["summary"],
            "source":     "database",
            "confidence": round(best_score, 2)
        }

    finally:
        conn.close()


def _record_usage(command_id: str, query: str) -> None:
    """Increment usage counter and log this query."""
    now = datetime.now().isoformat()
    try:
        conn = _connect()
        conn.execute(
            "UPDATE commands SET usage_count = usage_count + 1, last_used = ? WHERE id = ?",
            (now, command_id)
        )
        conn.execute(
            "INSERT INTO usage_log (command_id, query, used_at, session_id) VALUES (?,?,?,?)",
            (command_id, query, now, _session_id)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass

def save_to_pending(query: str, result: dict, os_id: str) -> bool:
    """
    Save an Ollama response to the pending table for later review.
    Returns True if saved, False if duplicate or empty.
    Called automatically after every Ollama response.
    """
    commands = result.get("commands", [])
    if not commands:
        return False

    intent = query.strip().lower()
    entry_id = _entry_hash(intent, os_id)
    now = datetime.now().isoformat()

    conn = _connect()
    try:
        existing_cmd = conn.execute(
            "SELECT id FROM commands WHERE id = ?", (entry_id,)
        ).fetchone()

        existing_pnd = conn.execute(
            "SELECT id FROM pending WHERE id = ?", (entry_id,)
        ).fetchone()

        if existing_cmd or existing_pnd:
            return False

        conn.execute(
            """INSERT INTO pending
               (id, intent, tags, os, commands_json, summary, original_query, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                intent,
                json.dumps(_tokenize(intent)),
                os_id,
                json.dumps(commands),
                result.get("summary", ""),
                query,
                result.get("source", "ollama"),
                now
            )
        )
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def approve_pending(entry_id: str) -> bool:
    """Move an entry from pending into the live commands table."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM pending WHERE id = ?", (entry_id,)
        ).fetchone()

        if not row:
            return False

        now = datetime.now().isoformat()
        conn.execute(
            """INSERT OR REPLACE INTO commands
               (id, intent, tags, os, commands_json, summary, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["id"], row["intent"], row["tags"], row["os"],
                row["commands_json"], row["summary"], "approved", now
            )
        )
        conn.execute("DELETE FROM pending WHERE id = ?", (entry_id,))
        conn.commit()

        _cache.pop((_normalize(row["intent"]), row["os"]), None)
        return True
    finally:
        conn.close()


def reject_pending(entry_id: str) -> bool:
    """Delete an entry from the pending table."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM pending WHERE id = ?", (entry_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_pending_entries() -> list:
    """Return all pending entries as a list of dicts."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM pending ORDER BY created_at DESC"
        ).fetchall()

        result = []
        for row in rows:
            result.append({
                "id":       row["id"],
                "intent":   row["intent"],
                "os":       row["os"],
                "commands": json.loads(row["commands_json"]),
                "summary":  row["summary"],
                "source":   row["source"],
                "added_at": row["created_at"][:10]
            })
        return result
    finally:
        conn.close()


def count_pending() -> int:
    """How many entries are waiting for review."""
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM pending").fetchone()[0]
    finally:
        conn.close()


def get_stats() -> dict:
    """Return database statistics."""
    conn = _connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM pending").fetchone()[0]
        cached = len(_cache)
        top = conn.execute(
            "SELECT intent, usage_count FROM commands ORDER BY usage_count DESC LIMIT 5"
        ).fetchall()

        return {
            "total_commands": total,
            "pending_review": pending,
            "memory_cache":   cached,
            "top_commands":   [(r["intent"], r["usage_count"]) for r in top]
        }
    finally:
        conn.close()


def export_seed_sql(output_path: str = None) -> str:
    """
    Export the commands table as SQL INSERT statements.
    Commit the output file to GitHub so new users get your entries.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__), "data", "seed.sql"
        )

    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT id, intent, tags, os, commands_json, summary, source, created_at
               FROM commands ORDER BY usage_count DESC"""
        ).fetchall()

        lines = [
            "-- ShellAI seed data",
            f"-- Generated: {datetime.now().isoformat()[:10]}",
            f"-- Entries: {len(rows)}",
            ""
        ]

        for row in rows:
            def esc(s):
                return str(s).replace("'", "''")

            lines.append(
                f"INSERT OR IGNORE INTO commands "
                f"(id, intent, tags, os, commands_json, summary, source, created_at) "
                f"VALUES ("
                f"'{esc(row['id'])}', "
                f"'{esc(row['intent'])}', "
                f"'{esc(row['tags'])}', "
                f"'{esc(row['os'])}', "
                f"'{esc(row['commands_json'])}', "
                f"'{esc(row['summary'])}', "
                f"'{esc(row['source'])}', "
                f"'{esc(row['created_at'])}'"
                f");"
            )

        sql = "\n".join(lines)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            f.write(sql)

        return output_path
    finally:
        conn.close()

init_db()