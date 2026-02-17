import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.services import DataExtractor


def Process_HTMLs():
    page_fp = [fp for fp in Path("./data/html").iterdir() if fp.suffix == ".html"]
    dest_dir = Path("./data/json")
    for fp in page_fp:
        with open(fp, mode="r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            data = DataExtractor.compile_record_json(soup)

        with open(dest_dir / (fp.stem + ".json"), mode="w") as f:
            f.write(json.dumps(data, ensure_ascii=False).replace("\t", ""))
