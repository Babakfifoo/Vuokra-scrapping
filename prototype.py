# %%
%load_ext autoreload
%autoreload 2
import json
import requests
from app.utils import setupDriver
import tomllib
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from typing import List
from datetime import datetime
import uuid6
import pandas as pd
import time
import sqlite3
import requests
from app.utils.webpageExtractor import (
    get_listings_page,
    extract_listing_links,
    insert_rows_to_ledger,
    load_site_config,
    download_webpage
)
import logging
# %%

driver = setupDriver.setup_driver()

# Initiate the Chromedriver by passing options as argument
# %%
def get_last_two_links(card_type, db_path: str = "app/data/listings.sqlite3") -> List[str]:
    with sqlite3.connect("./app/data/listings.sqlite3") as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT link FROM ledger
            WHERE page = 1 and cardType = '{card_type}'
            ORDER BY accessed_at DESC
            LIMIT 2
        """)
        links = [row[0] for row in cur.fetchall()]
    return links

def get_unparsed_links(db_path: str = "app/data/listings.sqlite3") -> List[str]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT link FROM ledger
            WHERE parsed = 0 
        """)
        links = [row[0] for row in cur.fetchall()]
    return links
# %%
config = load_site_config()

session_config = config["listing_types"]["Vuokrattavat"]["vuokra-asunnot"]




def download_webpage(url: str) -> str:
    """download webpage

    This function downloads the webpage from the given url.

    Parameters
    ----------
    url : str
        url of the webpage to download

    Returns
    -------
    str
        html content of the webpage
    """
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to download webpage: {e}")
        return ""
    return response.text

# %%
unparsed_links = get_unparsed_links()
for link in unparsed_links:
    html_str = download_webpage(link)
    with open(f"app/data/html/cache/{link.split('/')[-1]}.html", "w", encoding="utf-8") as f:
        f.write(html_str)

# %%
import os
import zipfile
from pathlib import Path

cache_dir = Path("app/data/html/cache/")
output_dir = Path("app/data/html")
output_dir.mkdir(parents=True, exist_ok=True)

zip_path = output_dir / f"{datetime.now().strftime('%Y%m%d')}.zip"

# 1. Create the zip from all html files in cache_dir
html_files = list(cache_dir.glob("*.html"))

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for html_file in html_files:
        zf.write(html_file, arcname=html_file.name)  # arcname avoids storing full path

print(f"Zipped {len(html_files)} files to {zip_path}")

# 2. Remove the original html files from cache_dir
for html_file in html_files:
    html_file.unlink()

print(f"Removed {len(html_files)} files from {cache_dir}")
# %%
