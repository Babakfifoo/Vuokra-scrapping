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


def Process_HTML_str(html_str):
    """
    Process a single HTML string and return the extracted data as a dictionary.
    """
    soup = BeautifulSoup(html_str, "html.parser")
    data = DataExtractor.compile_record_json(soup)

    return data


# WARNING: process the data with GDPR before storing it!
def Generate_tables(data):
    # Implement table generation logic here
    pass


def process_ad_description(data):
    # Implement data generation logic here
    pass
