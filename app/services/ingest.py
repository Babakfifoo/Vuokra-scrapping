import logging
import os
from datetime import date, datetime

import dotenv
import pandas as pd
from sqlalchemy import create_engine

from app.services import DataProcessor
from app.utils import setupDriver, systemTools, webpageExtractor

dotenv.load_dotenv()
# %%
# This gets all links from 24 hours ago.

systemTools.setup_logging()
# Get today's date
today = datetime.now()

def ingest_to_files():
    """Ingest data from Oikotie
    This script ingests data from Vuokra.fi and saves it to a file.
    """
    Extract_links()
    webpageExtractor.store_missing_html()


def Extract_links():
    extractor = webpageExtractor.webpageExtractor(driver=setupDriver.setup_driver())
    links = extractor.get_todays_ads_links()
    logging.info(len(links))
    extractor.append_link_table(links)
