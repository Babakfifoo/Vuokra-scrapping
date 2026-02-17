import logging
import os
from datetime import date

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
today = date.today()
db_config = {
    "host": "localhost",
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": 5000,
}


def ingest_to_files():
    """Ingest data from Oikotie
    This script ingests data from Vuokra.fi and saves it to a file.
    """
    # Extract_links()
    # webpageExtractor.store_missing_html()
    DataProcessor.Process_HTMLs()


def Extract_links():
    extractor = webpageExtractor.webpageExtractor(driver=setupDriver.setup_driver())
    links = extractor.get_todays_ads_links()
    logging.info(len(links))

    link_df = pd.DataFrame({"page": links[0], "link": links[1]})
    link_df["accessed_at"] = today

    # Connect to database

    engine = create_engine(
        f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    link_df.to_sql(name="links", con=engine, if_exists="append", index=False)
    engine.dispose()
