# %%
import logging
import time
import tomllib
from datetime import datetime
from typing import Any, Dict, List
import sqlite3
from uuid_extensions import uuid7str
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from . import LEDGER_FP, HTML_DIR, JSON_DIR, LEDGER_DB
from . import Storage, setupDriver
from app.services import DataExtractor
import json
import uuid6
from urllib.parse import unquote
with open("./app/utils/URLSettings.toml", "rb") as f:
    URL_SETTING: Dict[str, Any] = tomllib.loads(f.read().decode("utf-8"))["Oikotie"]


SELECTOR = ".cards-v3__card.ng-star-inserted"
VUAKRA_AD_TYPE: str | None = (
    URL_SETTING.get("Categories", {}).get("Vuokra", {}).get("Asunnot", None)
)


def load_site_config(path: str = "app/configs.toml") -> dict:
    """Configuration loader"""
    with open(path, "rb") as f:
        return tomllib.load(f)

def get_and_insert_listings(session_config: dict) -> None:
    """gathering and storing the links to listing based on the configurations

    Parameters
    ----------
    session_config : 
        A dictionary containing the configuration for the session, including the base URL and card type.
    """    
    last_links = get_last_two_links(card_type=session_config["cardType"])
    for page in range(1, 100):
        logging.info(f"Scraping page {page}")
        get_listings_page(driver = driver, page=page, session_config=session_config)
        time.sleep(2)
        links = extract_listing_links(driver)

        last_links = [link for link in last_links if link not in links]
        if len(last_links) == 0:
            print(f"All last links found on page {page}. Stopping.")
            insert_rows_to_ledger(links, page, session_config)
            break

        if len(links) == 0:
            print(f"No links found on page {page}. Stopping.")
            break
        insert_rows_to_ledger(links, page, session_config)

def get_listings_page(driver, page: int, session_config):
    """Get the listings page for a given page number."""
    config = load_site_config()
    url = session_config["base_url"].format(page=page)
    driver.get(url)
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    return 

def extract_listing_links(driver) -> List[str]:
    """Extracts listing links from the current page.

    Parameters
    ----------
    driver : selenium.webdriver.Chrome
        The Selenium WebDriver instance.

    Returns
    -------
    List[str]
        A list of extracted listing links.
    """
    elements = driver.find_elements(By.XPATH, "//a[@href]")
    links: List[str] = [
        elem.get_attribute("href")
        for elem in elements
        if elem.get_attribute("href") is not None
    ]  # type: ignore

    ads: List[str] = [s for s in links if s.split("/")[-1].isdigit()]
    return ads


def generate_row(link: str, page: int, date_time: str, session_config) -> dict:
    """Generate a row for the ledger table based on the given link.

    Parameters
    ----------
    link : str
        The listing link.
    page : int
        The page number.
    date_time : str
        The date and time of the extraction.

    Returns
    -------
    dict
        A dictionary representing a row for the ledger table.
    """
    return {
        "id": str(uuid6.uuid7()),
        "kunta": unquote(link.split("/")[-2]),
        "cardType": session_config["cardType"],
        "cardid": int(link.split("/")[-1]),
        "accessed_at": date_time,
        "page": page,
        "link": link,
        "parsed": 0,
    }

def insert_single_row(row: dict, db_path: str = "./app/data/listings.sqlite3") -> None:
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            INSERT INTO ledger (id, kunta, cardid,cardType, accessed_at, page, link, parsed)
            VALUES (:id, :kunta, :cardid, :cardType, :accessed_at, :page, :link, :parsed)
            ON CONFLICT(link) DO NOTHING
            """,
            {**row},
        )
        con.commit()

def insert_rows_to_ledger(links: List[str], page: int, session_config, db_path: str = "./app/data/listings.sqlite3") -> None:
    """Insert multiple rows into the ledger table based on the given links.

    Parameters
    ----------
    links : List[str]
        A list of listing links.
    page : int
        The page number from which the links were extracted.
    session_config : dict
        The configuration for the session.
    db_path : str, optional
        The path to the SQLite database file, by default "./app/data/listings.sqlite3".
    """
    with sqlite3.connect(db_path) as con:
        parsing_dt = datetime.now().isoformat()
        for link in links:
            row = generate_row(link, page, parsing_dt, session_config)
            con.execute(
                """
                INSERT INTO ledger (id, kunta, cardid, cardType, accessed_at, page, link, parsed)
                VALUES (:id, :kunta, :cardid, :cardType, :accessed_at, :page, :link, :parsed)
                ON CONFLICT(link) DO NOTHING
                """,
                {**row},
            )
        con.commit()



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

    def get_ads_and_update(self) -> None:
        """Get the apps and update the links ledger
        This function basically initiaates the scrapping process.
        It runs all necessary functions to scrap and store the links.
        # TODO This function needs to be moved to ingestion part. The pipeline is not clean here.

        """
        links: List[List[Any]] = self.get_todays_ads_links()

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
        # TODO: Add a dynamic datetime for each page.

        threshold: int = 1
        all_index: List[int] = []
        all_links: List[str] = []
        link1, link2 = get_first_two_links_from_yesterdays_ads()
        while threshold < 99:
            # WARNING: Do not store the links until the whole proces is completed
            # If the links are stored before reaching last checkpoints,
            # the next time the process is running will miss them.
            logging.info(f"Processing page {threshold}")
            obtained_links: List[str] = self.get_page_ads(page=threshold)
            all_index += [threshold] * len(obtained_links)
            all_links.extend(obtained_links)

            # TODO Make validation a function
            # The function gets the links, and All link list to generate index.
            # if the validation failes, it will bypass the return statement.
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
        with open("./app/data/cache/temp.html", mode="w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        elements: List[WebElement] = self.driver.find_elements(By.XPATH, "//a[@href]")
        # TODO make this a function for extracting ad links.
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

    def construct_ledger_df(self, links_idx_lst: List[List[Any]]) -> pd.DataFrame:
        link_df = pd.DataFrame({"page": links_idx_lst[0], "link": links_idx_lst[1]})
        link_df["accessed_at"] = datetime.now().strftime(format="%Y-%m-%d %H:%M:%S")
        link_df["cardid"] = link_df["link"].str.split("/").str[-1]
        link_df["id"] = [uuid7str() for _ in range(len(link_df))]
        link_df["parsed"] = False
        link_df["visibility_parsed"] = False
        return link_df[
            [
                "id",
                "cardid",
                "accessed_at",
                "page",
                "link",
                "parsed",
                "visibility_parsed",
            ]
        ]

    def append_link_table(self, links_idx_lst: List[List[Any]]) -> None:
        """Append the scrapped links to the links table
        This function adds the obtained links from the search pages.
        These links then stored to keep a ledger of all links, their processing
        stages and the checkpoints.

        Parameters
        ----------
        links_idx_lst : List[List[Any]]
            _description_
        """
        link_df: pd.DataFrame = self.construct_ledger_df(links_idx_lst)
        with sqlite3.connect(LEDGER_DB) as con:
            link_df.to_sql(name="ledger", con=con, if_exists="append", index=False)
        # validate if the table is there:

        return


def get_first_two_links_from_yesterdays_ads() -> List[str]:
    """get first two linkf of yesterday

    This function gets the first two links of last batch of processing.

    We use the last batch so itf the function is executed in the same day,
    it will only get the new links. Otherwise, execution in 24 hours interval will yield the same results.

    Parameters
    ----------
    None

    Returns
    -------
    List[str]
        two links
    """
    with sqlite3.connect(LEDGER_DB) as con:
        result: List[Any] = (
            pd.read_sql(
                """
                    SELECT * FROM ledger
                    ORDER BY accessed_at DESC, page ASC
                    LIMIT 2
                """,
                con,
            )
            .sort_values("id")
            .head(2)["link"]
            .to_list()
        )

    if len(result) < 2:
        logging.warning("Less than 2 links found for yesterday's ads.")
        return ["", ""]
    return result[:2]


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
    """

    missing_ledger: pd.DataFrame = Storage.get_unprocessed_rows()
    for i, row in missing_ledger.iterrows():
        # Process the link
        # Index 10 ensures that only date is extracted and no other information is in there.
        date_str = str(row.get("accessed_at", datetime.today().strftime("%Y-%m-%d")))[
            :10
        ]
        html_str = download_webpage(row["link"])
        if html_str:
            fname: str = date_str + "-" + row["link"].split("/")[-1]
            soup = BeautifulSoup(html_str, "html.parser")
            data = DataExtractor.compile_record_json(soup)

            with open(JSON_DIR / (fname + ".json"), mode="w") as f:
                f.write(json.dumps(data, ensure_ascii=False).replace("\t", ""))
                logging.debug(f"Stored {fname}")
                Storage.mark_as_processed(row["id"])

        time.sleep(0.1)


# %%
