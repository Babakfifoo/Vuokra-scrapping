# %%
import logging
import os
import time
import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import psycopg2
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import create_engine

from . import Storage, setupDriver

with open("./Settings.toml", "rb") as f:
    URL_SETTING: Dict[str, Any] = tomllib.loads(f.read().decode("utf-8"))["Oikotie"]

HTML_DIR = Path("./data/html")
SELECTOR = ".cards-v3__card.ng-star-inserted"
VUAKRA_AD_TYPE: str | None = (
    URL_SETTING.get("Categories", {}).get("Vuokra", {}).get("Asunnot", None)
)


class webpageExtractor:
    """Ad links extractor.
    This object contains information and functionalities that allows for a smooth extraction of ad links for further processing.
    """

    def __init__(self, driver) -> None:
        self.driver: setupDriver.WebDriver = driver
        self.BaseURL: str = URL_SETTING.get("BaseURL", "")
        self.list_of_pages: List[str] = []
        # this is to make sure the if confing is properly set.
        self.ad_type: str = VUAKRA_AD_TYPE if VUAKRA_AD_TYPE else "vuokra-asunnot"
        # Connection string for the database, using environment variables for security
        self.conn_str: str = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:5000/{os.getenv('POSTGRES_DB')}"

    def get_ads_and_update(self) -> None:
        links = self.get_todays_ads_links()
        self.append_link_table(links)
        return

    def get_todays_ads_links(self) -> List[List[Any]]:
        """
        Retrieve ad links from paginated search results until ads older than yesterday are reached.

        Parameters
        ----------
        ad_type : str, optional
            The advertisement category to query (default "vuokra-asunnot").

        Returns
        -------
        List[str]
            A list of ad links collected from pages that contain ads published in past 24 hours

        Notes
        -----
        - The method relies on self.get_page_ads and self.HTMLParser.get_published_date.
        - Pagination is capped at 30 pages to avoid infinite loops.

        Example
        -------
        links = self.get_todays_ads_links()  # returns links for ads from today and yesterday
        """

        threshold: int = 1
        all_index: List[int] = []
        all_links: List[str] = []
        with psycopg2.connect(self.conn_str) as conn:
            link1, link2 = get_first_two_links_from_yesterdays_ads(conn=conn)
        while threshold < 99:
            logging.info(f"Processing page {threshold}")
            obtained_links: List[str] = self.get_page_ads(page=threshold)
            all_index += [threshold] * len(obtained_links)
            all_links.extend(obtained_links)
            # validate_link1
            link1_validated: bool = link1 in all_links
            link2_validated: bool = link2 in all_links

            if link1_validated and link2_validated:
                if all_links.index(link1) < (all_links.index(link2) - 1):
                    index = all_links.index(link2) - 1
                else:
                    index = all_links.index(link1) - 1
                return [all_index[:index], all_links[:index]]
            threshold += 1
        logging.warning(
            "Reached page limit without finding yesterday's ads. Returning collected links."
        )
        return [all_index, all_links]

    def get_page_ads(self, page: int = 1) -> List[str]:
        """
        Retrieve ad URLs from a listing page.
        Parameters
        ----------
        page : int
            Page number intended to fetch. (Note: the current implementation calls base_url.format(page=1),
            so the provided page value is ignored unless that call is changed.)
        Returns
        -------
        List[str]
            A list of advertisement URLs discovered on the page. An URL is considered an ad if its last
            path segment consists only of digits. If no links are found, a list containing an empty string
            ([""]) is returned and a warning is logged.
        Side effects
        ------------
        - Navigates the Selenium webdriver (self.driver) to the formatted base_url.
        - Waits until the page's document.readyState is "complete".
        - Extracts all <a> elements with an href attribute and filters them.
        Exceptions
        ----------
        May raise Selenium-related exceptions (e.g., TimeoutException, WebDriverException) if navigation
        or waiting fails. Requires that self.driver and base_url are defined on the instance.
        """

        self.driver.get(self.BaseURL.format(category=self.ad_type, page=page))
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.driver.implicitly_wait(10)
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)

        # Additional wait for complete rendering
        with open("test.html", mode="w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        elements: List[WebElement] = self.driver.find_elements(By.XPATH, "//a[@href]")
        links: List[str] = [
            elem.get_attribute("href")
            for elem in elements
            if elem.get_attribute("href") is not None
        ]  # type: ignore
        if links == []:
            logging.warning("No ads were found in this page")
            return [""]
        ads: List[str] = [s for s in links if s.split("/")[-1].isdigit()]
        return ads

    def append_link_table(self, links_idx_lst: List[List[Any]]) -> None:
        link_df = pd.DataFrame({"page": links_idx_lst[0], "link": links_idx_lst[1]})
        link_df["accessed_at"] = date.today()
        engine = create_engine(self.conn_str)
        link_df.to_sql(name="links", con=engine, if_exists="append", index=False)
        engine.dispose()
        return


def get_first_two_links_from_yesterdays_ads(conn) -> List[str]:
    """get first two linkf of yesterday

    This function gets the first two links of yesterday ads in order to scrap
    the ads that are published within the past 24 hours.

    Parameters
    ----------
    conn : psycopg2.extensions.connection
         a connection to the database where the links are stored

    Returns
    -------
    List[str]
        two links
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT link
        FROM links
        WHERE DATE(accessed_at) = CURRENT_DATE - INTERVAL '1 day'
        ORDER BY page ASC
        LIMIT 2
    """)
    result = [row[0] for row in cursor.fetchall()]
    if len(result) < 2:
        logging.warning("Less than 2 links found for yesterday's ads.")
        return ["", ""]
    return result


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


def store_missing_html() -> None:
    """store html

    This function stores the html content of the webpage in the database.

    Parameters
    ----------
    url : str
        url of the webpage to store
    """

    conn_params = {
        "host": "localhost",
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "port": 5000,
    }

    # Connect to database
    with psycopg2.connect(**conn_params) as conn:
        rows = Storage.get_unprocessed_rows(conn=conn)

    for row in rows:
        # Process the link
        date_str = row.get("accessed_at", datetime.today()).strftime("%Y-%m-%d")
        html_str = download_webpage(row["link"])
        if html_str:
            fname = date_str + "-" + row["link"].split("/")[-1]
            with open(HTML_DIR / f"{fname}.html", "w", encoding="utf-8") as f:
                f.write(html_str)
                logging.debug(f"Stored {fname}")
        time.sleep(0.1)
