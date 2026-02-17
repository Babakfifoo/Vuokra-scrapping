from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor


def get_unprocessed_rows(conn) -> List[Dict[str, Any]]:
    """Fetch all rows where processed status is NULL."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT accessed_at, link, parsed
            FROM links
            WHERE parsed IS NULL
            FOR UPDATE SKIP LOCKED
        """)
        return cur.fetchall()


def mark_as_processed(conn, success: bool = True):
    raise NotImplementedError("mark_as_processed function is not implemented yet.")
    """Update the processed status for a row."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE your_table_name
            SET processed = %s
            WHERE accessed_at = %s and link = %s
        """,
            (True,),
        )
    conn.commit()


def package_today_htmls():
    # TODO A function that puts all htmls files of today into a gz package.
    pass


def parse_jsons_to_pandas():
    # TODO A function to parse and convert all json files into rows of data for the database.
    pass


def insent_records():
    # TODO a function that insert the parsed rows.
    pass
