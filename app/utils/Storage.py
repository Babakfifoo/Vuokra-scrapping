from typing import Dict, List
import pandas as pd
from pathlib import Path
import json
import logging
import sqlite3
from . import JSON_DAY_DIR, LEDGER_DB

json_fps: list[Path] = [x for x in Path("app/data/json").iterdir()]


def get_unprocessed_rows() -> pd.DataFrame:
    with sqlite3.connect(LEDGER_DB) as con:
        ledger = pd.read_sql_query(
            sql="SELECT * FROM ledger WHERE parsed = 0", 
            con=con
            )

    return ledger


def mark_as_processed(row_id: str):
    with sqlite3.connect(LEDGER_DB) as con:
        con.execute(f"UPDATE ledger SET parsed = true WHERE id = '{row_id}';")
    return


import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import closing

DB_PATH = "listings.sqlite3"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the SQLite database file."""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def create_ledger_table(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id TEXT PRIMARY KEY,
            cardid INTEGER NOT NULL,
            accessed_at TEXT NOT NULL,
            page INTEGER NOT NULL,
            link TEXT NOT NULL UNIQUE,
            parsed INTEGER NOT NULL CHECK (parsed IN (0, 1)),
            visibility_parsed INTEGER NOT NULL CHECK (visibility_parsed IN (0, 1))
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

        insert_entry(
            con,
            cardid=123,
            page=1,
            link="https://example.com/listing/123",
            parsed=False,
            visibility_parsed=False,
        )

        for row in con.execute("SELECT * FROM ledger"):
            print(row)

def load_json_file(fp) -> Dict:
    with open(fp, mode="r", encoding="utf-8") as f:
        return json.load(f)


def store_json(fp, data) -> None:
    if fp.exists():
        data.append(load_json_file(fp))
    with open(fp, mode="w", encoding="utf-8") as f:
        f.write(json.dumps(data))

    return


def load_and_merge_jsons() -> None:
    json_fps: list[Path] = [x for x in Path("app/data/json").iterdir()]
    json_files_ledger = (
        pd.DataFrame({"fps": json_fps})
        .assign(fname=lambda df: df["fps"].apply(lambda fp: fp.name))
        .assign(access_dt=lambda df: df["fname"].str[:10])
        .assign(data_dict=lambda df: df["fps"].apply(load_json_file))
        .groupby("access_dt")
        .agg({"data_dict": list})
        .reset_index()
    )

    for i, row in json_files_ledger.iterrows():
        (
            store_json(
                fp=JSON_DAY_DIR / (row["access_dt"] + ".json"), data=row["data_dict"]
            )
        )
    remove_temp_json(json_fps)


def remove_temp_json(json_fps):
    logging.info("removing the temporary jsons")
    for fp in json_fps:
        fp.unlink(missing_ok=True)
