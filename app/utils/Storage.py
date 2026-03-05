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
