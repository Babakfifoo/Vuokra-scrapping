import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import closing

DB_PATH = "app/data/listings.sqlite3"

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the SQLite database file."""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def create_ledger_table(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id TEXT PRIMARY KEY,
            kunta TEXT NOT NULL,
            cardType INTEGER NOT NULL,
            cardid INTEGER NOT NULL,
            accessed_at TEXT NOT NULL,
            page INTEGER NOT NULL,
            link TEXT NOT NULL UNIQUE,
            parsed INTEGER NOT NULL CHECK (parsed IN (0, 1))
        );
    """)
    con.commit()


def insert_entry(
    con: sqlite3.Connection,
    cardid: int,
    page: int,
    link: str,
    parsed: bool = False,
    visibility_parsed: bool = False,
) -> None:
    """Insert one ledger row. Skips silently if link already exists (UNIQUE)."""
    con.execute(
        """
        INSERT INTO ledger (id, cardid, accessed_at, page, link, parsed, visibility_parsed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(link) DO NOTHING
        """,
        (
            str(uuid.uuid4()),
            cardid,
            datetime.now(timezone.utc).isoformat(),
            page,
            link,
            int(parsed),
            int(visibility_parsed),
        ),
    )
    con.commit()


def link_exists(con: sqlite3.Connection, link: str) -> bool:
    """Check whether a link is already in the ledger."""
    result = con.execute(
        "SELECT 1 FROM ledger WHERE link = ? LIMIT 1", (link,)
    ).fetchone()
    return result is not None


def mark_parsed(con: sqlite3.Connection, link: str, visibility: bool | None = None) -> None:
    """Mark a link as parsed, optionally also setting visibility_parsed."""
    if visibility is None:
        con.execute("UPDATE ledger SET parsed = 1 WHERE link = ?", (link,))
    else:
        con.execute(
            "UPDATE ledger SET parsed = 1, visibility_parsed = ? WHERE link = ?",
            (int(visibility), link),
        )
    con.commit()


if __name__ == "__main__":
    with closing(get_connection()) as con:
        create_ledger_table(con)
