from typing import Dict, List, Optional

import pandas as pd
import pandera.pandas as pa
from pandera.typing.pandas import Index, DataFrame, Series


class InputSchema(pa.DataFrameModel):
    link: Series[str] = pa.Field(str_length={"max_value": 255})
    accessed_at: Series[pd.Timestamp]
    class Config:
        strict = True  



TABLE_COLNAMES: Dict[str, str] = {
    "Hinta": "hinta",
    "Muut maksut": "muut_maksut",
    "Perustiedot": "perustiedot",
    "Talon ja tontin tiedot": "talon_tontin_tiedot",
    "Tekniset tiedot": "tekniikka",
    "Tilat ja materiaalit": "tilat_materiaalit",
    "Valinnainen vuokratontti": "valinnainen_vuokratontti",
}