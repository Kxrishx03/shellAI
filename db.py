import sqlite3
import json
import os
import re
import hashlib
import uuid
from datetime import datetime
from typing import Optional
from config import SHELLAI_DIR

DB_PATH   = os.path.join(SHELLAI_DIR, "commands.db")
SEED_PATH = os.path.join(os.path.dirname(__file__), "data", "seed.sql")

_cache: dict = {}
_session_id  = str(uuid.uuid4())[:8]  # unique ID for this run

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


def _entry_hash(intent: str, os_id: str) -> str:
    """Stable 8-char hash ID for a command entry."""
    key = f"{intent.strip().lower()}:{os_id}"
    return hashlib.md5(key.encode()).hexdigest()[:8]


def _normalize(query: str) -> str:
    """Normalize a query for cache key comparison."""
    return " ".join(_tokenize(query))

def _get_connection() -> sqlite3.Connection:
    """
    Get a database connection with good defaults.
    WAL mode allows multiple readers with one writer simultaneously —
    important when multiple shellai processes run at once.
    """
    os.makedirs(SHELLAI_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row      
    conn.execute("PRAGMA journal_mode=WAL") 
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL") 
    return conn


def init_db() -> None:
    """
    Create all tables if they do not exist.
    Called once on first import.
    Safe to call multiple times — CREATE IF NOT EXISTS.
    """
    conn = _get_connection()
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
                id            TEXT PRIMARY KEY,
                intent        TEXT NOT NULL,
                tags          TEXT NOT NULL DEFAULT '[]',
                os            TEXT NOT NULL DEFAULT 'all',
                commands_json TEXT NOT NULL,
                summary       TEXT NOT NULL DEFAULT '',
                original_query TEXT,
                source        TEXT DEFAULT 'ollama',
                created_at    TEXT NOT NULL
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
    Import seed.sql into the database if commands table is empty.
    This gives new users a populated database immediately.
    seed.sql is generated from your curated commands.json.
    """
    conn = _get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
        if count > 0:
            return  

        if os.path.exists(SEED_PATH):
            with open(SEED_PATH) as f:
                conn.executescript(f.read())
            conn.commit()
            return

        json_path = os.path.join(os.path.dirname(__file__), "data", "commands.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                entries = json.load(f)
            _bulk_insert(conn, entries, source="seed")
            conn.commit()
    finally:
        conn.close()


def _bulk_insert(conn: sqlite3.Connection, entries: list, source: str = "seed") -> int:
    """Insert multiple entries. Returns count of newly inserted rows."""
    inserted = 0
    now      = datetime.now().isoformat()

    for entry in entries:
        intent = entry.get("intent", "").strip().lower()
        os_id  = entry.get("os", "all")
        if not intent:
            continue

        entry_id = entry.get("id") or _entry_hash(intent, os_id)
        tags     = json.dumps(entry.get("tags", _tokenize(intent)))
        commands = json.dumps(entry.get("commands", []))
        summary  = entry.get("summary", "")

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

def search(query: str, os_id: str = "ubuntu") -> Optional[dict]:
    """
    Search for commands matching a query.

    Search order:
    1. Memory cache (instant, same process)
    2. SQLite keyword search (milliseconds)

    Returns None if no confident match found.
    Increments usage_count on a hit so we know what's popular.
    """
    cache_key = (_normalize(query), os_id)
    if cache_key in _cache:
        return _cache[cache_key]

    result = _db_search(query, os_id)

    if result:
        _cache[cache_key] = result

        _record_usage(result["_id"], query)

    return result


def _db_search(query: str, os_id: str) -> Optional[dict]:
    """
    Search SQLite using keyword scoring.

    How the scoring works:
    We extract keywords from the query and check how many appear
    in each entry's intent and tags. We compute a match ratio.
    Entries scoring above 0.35 are candidates. We return the best.

    Why not FTS5 MATCH?
    FTS5 is great but requires exact word matching. Developer queries
    like "init git" vs "initialize git repository" would miss.
    Our keyword scoring handles partial vocabulary overlap well.
    """
    keywords = _tokenize(query)
    if not keywords:
        return None

    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, intent, tags, os, commands_json, summary, usage_count
               FROM commands
               WHERE os IN ('all', ?)
               ORDER BY usage_count DESC
               LIMIT 200""",
            (os_id,)
        ).fetchall()

        best_row   = None
        best_score = 0.0

        for row in rows:
            intent_words = set(_tokenize(row["intent"]))
            tag_words    = set()

            try:
                tags = json.loads(row["tags"])
                for tag in tags:
                    tag_words.update(_tokenize(str(tag)))
            except (json.JSONDecodeError, TypeError):
                pass

            entry_words = intent_words | tag_words
            query_words = set(keywords)

            if not entry_words:
                continue

            overlap    = query_words & entry_words
            base_score = len(overlap) / len(query_words)

            # Bonus: exact phrase match in intent
            if query.lower().strip() in row["intent"]:
                base_score = min(1.0, base_score + 0.3)

            # Bonus: popular commands get a small nudge
            popularity = min(0.1, row["usage_count"] * 0.005)
            score      = min(1.0, base_score + popularity)

            if score > best_score:
                best_score = score
                best_row   = row

        if best_score < 0.35 or best_row is None:
            return None

        commands = json.loads(best_row["commands_json"])

        return {
            "_id":       best_row["id"],
            "commands":  commands,
            "summary":   best_row["summary"],
            "source":    "database",
            "confidence": round(best_score, 2)
        }

    finally:
        conn.close()


def _record_usage(command_id: str, query: str) -> None:
    """Record a cache hit and increment the usage counter."""
    now = datetime.now().isoformat()
    try:
        conn = _get_connection()
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
        pass  # usage tracking failures are non-critical


# ── Saving Ollama responses ───────────────────────────────

def save_to_pending(query: str, result: dict, os_id: str) -> bool:
    """
    Save an Ollama response to the pending table.
    Called automatically after every Ollama response.
    Returns True if saved, False if duplicate or empty.
    """
    commands = result.get("commands", [])
    if not commands:
        return False

    intent   = query.strip().lower()
    entry_id = _entry_hash(intent, os_id)
    now      = datetime.now().isoformat()

    conn = _get_connection()
    try:
        # Check if already in commands or pending
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
        return False  # race condition duplicate
    finally:
        conn.close()


def approve_pending(entry_id: str) -> bool:
    """
    Move an entry from pending to commands table.
    Returns True if successful.
    """
    conn = _get_connection()
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
                row["commands_json"], row["summary"],
                "approved", now
            )
        )
        conn.execute("DELETE FROM pending WHERE id = ?", (entry_id,))
        conn.commit()

        # Invalidate cache entry if it exists
        _cache.pop((_normalize(row["intent"]), row["os"]), None)

        return True
    finally:
        conn.close()


def reject_pending(entry_id: str) -> bool:
    """Delete an entry from the pending table."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM pending WHERE id = ?", (entry_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ── Review interface ──────────────────────────────────────

def get_pending_entries() -> list:
    """Return all pending entries as a list of dicts."""
    conn = _get_connection()
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
    conn = _get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    finally:
        conn.close()


# ── Export for seed.sql ───────────────────────────────────

def export_seed_sql(output_path: str = None) -> str:
    """
    Export the commands table as SQL INSERT statements.
    This is how you share your database improvements with other users.
    Commit the output to GitHub and new users get your entries.

    Usage: shellai --export-seed
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__), "data", "seed.sql"
        )

    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, intent, tags, os, commands_json, summary, source, created_at
               FROM commands
               ORDER BY usage_count DESC"""
        ).fetchall()

        lines = [
            "-- ShellAI seed data",
            f"-- Generated: {datetime.now().isoformat()[:10]}",
            f"-- Entries: {len(rows)}",
            ""
        ]

        for row in rows:
            # Escape single quotes in text fields
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


# ── Stats ─────────────────────────────────────────────────

def get_stats() -> dict:
    """Return database statistics for the --stats flag."""
    conn = _get_connection()
    try:
        total    = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
        pending  = conn.execute("SELECT COUNT(*) FROM pending").fetchone()[0]
        cached   = len(_cache)
        top_used = conn.execute(
            """SELECT intent, usage_count FROM commands
               ORDER BY usage_count DESC LIMIT 5"""
        ).fetchall()

        return {
            "total_commands": total,
            "pending_review": pending,
            "memory_cache":   cached,
            "top_commands":   [(r["intent"], r["usage_count"]) for r in top_used]
        }
    finally:
        conn.close()


# Initialize database on import
init_db()