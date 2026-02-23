from typing import Any, Dict, List

from . import LEDGER_FP
import pandas as pd
def get_unprocessed_rows() -> pd.DataFrame:
    
    ledger = pd.read_csv(LEDGER_FP)
    ledger_missing = ledger.query("~parsed")

    return ledger_missing


def mark_as_processed(ids: List[str]):
    ledger = pd.read_csv(LEDGER_FP)
    ledger.loc[ledger["id"].isin(ids), "parsed"] = True
    ledger.to_csv(LEDGER_FP)
