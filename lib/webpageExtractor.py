# %%
import requests
from selenium.webdriver.remote.webelement import WebElement
from . import setupDriver
from datetime import date, datetime, timedelta
import tomllib
from typing import List, Any, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json
import logging
import time

from icecream import ic

with open("lib/Settings.toml", "rb") as f:
    URL_SETTING: Dict[str, Any] = tomllib.loads(f.read().decode("utf-8"))["Oikotie"]


SELECTOR = ".cards-v3__card.ng-star-inserted"
TODAY = str(date.today())
VUAKRA_AD_TYPE: str | None = (
    URL_SETTING.get("Categories", {}).get("Vuokra", {}).get("Asunnot", None)
)



def store_ad_pages(ads: List[str]) -> None:
    for ad_url in ads:
        if len(ad_url) <= 40:
            continue
        with open(
            Path(f"data/htmls/{TODAY}-{ad_url.split('/')[-1]}.html"),
            mode="w",
            encoding="utf-8",
        ) as f:
            html_str = requests.get(ad_url).text
            f.write(html_str)
            # The scrip politeness
            time.sleep(0.1)
    return


class HTMLParser:
    def get_html_string(self, dp: str) -> str:
        # validating if the data path is a url:
        if "https:" in dp:
            return requests.get(dp).text
        else:
            with open(dp, mode="r", encoding="utf-8") as f:
                return f.read()

    def _get_meta(self, html_string: str):
        soup = BeautifulSoup(html_string, "html.parser")

        # Find the script tag that contains "var otAsunnot"
        script_tag = soup.find("script", string=re.compile("var otAsunnot"))  # type: ignore

        if script_tag:
            script_content = script_tag.string
        else:
            logging.info(f"No Meta found for this webpage.")
        return json.loads(
            script_content.split(";window")[0].split("=")[1]
        ).get("analytics")

    def get_published_date(self, dp) -> str:
        string = self.get_html_string(dp)
        return self._get_meta(string).get("published")


class webpageExtractor:
    def __init__(self, driver) -> None:
        self.driver: setupDriver.WebDriver = driver
        self.BaseURL: str = URL_SETTING.get("BaseURL", "")
        self.list_of_pages: List[str] = []
        self.HTMLParser = HTMLParser()
        # this is to make sure the if confing is properly set.
        self.ad_type: str = VUAKRA_AD_TYPE if VUAKRA_AD_TYPE else "vuokra-asunnot"

    def get_todays_ads_links(self, ad_type=None) -> List[str]:
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

        Raises
        ------
        ValueError
            If the published date string returned by HTMLParser.get_published_date cannot be parsed
            with the expected format ("%Y-%m-%d %H:%M:%S").

        Notes
        -----
        - The method relies on self.get_page_ads and self.HTMLParser.get_published_date.
        - Pagination is capped at 99 pages to avoid infinite loops.

        Example
        -------
        links = self.get_todays_ads_links()  # returns links for ads from today and yesterday
        """
        if not ad_type:
            ad_type:str = self.ad_type
            
        
        threshold: int = 1
        ad_links: List[str] = []
        while threshold < 100:
            obtained_links: List[str] = self.get_page_ads(
                page=threshold, ad_type=ad_type
            )
            last_page_date: str = self.HTMLParser.get_published_date(obtained_links[-1])
            dt_obj = datetime.strptime(last_page_date, "%Y-%m-%d %H:%M:%S")

            # 3. Extract just the date part (removes the time)
            input_date = dt_obj.date()
            ad_links += obtained_links
            # 4. Compare with today
            # Here we parse the ads util we reach the day before yesterday,
            # This is to obtain all ads published yesterday.
            if input_date < (date.today() - timedelta(days=1)):
                break
            # adding to the page
            threshold += 1

        return ad_links

    def get_page_ads(self, ad_type=None, page: int = 1) -> List[str]:
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

        if not ad_type:
            ad_type:str = self.ad_type
        
        self.driver.get(self.BaseURL.format(category=ad_type, page=page))
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
