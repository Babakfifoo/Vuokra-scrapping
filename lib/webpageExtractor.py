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

SELECTOR = ".cards-v3__card.ng-star-inserted"
TODAY =  str(date.today())
with open("lib/Settings.toml", "rb") as f:
    URL_SETTING: Dict[str, Any] = tomllib.loads(f.read().decode("utf-8"))["Oikotie"]


# %%
def get_ad_data(url: str) -> Dict:
    return {}

def store_ad_pages(ads: List[str]) -> None:
    for ad_url in ads:
        if len(ad_url) <= 40:
            continue
        with open(Path(f"data/htmls/{TODAY}-{ad_url.split('/')[-1]}.html"), mode="w", encoding="utf-8") as f:
            html_str = requests.get(ad_url).text
            f.write(html_str)
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
            script_content.replace("var otAsunnot=", "").split(";")[0]
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

    def get_todays_ads_links(self, ad_type="vuokra-asunnot") -> List[str]:
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
            if input_date < (date.today() - timedelta(days=1)):
                break
            # adding to the page
            threshold += 1

        return ad_links

    def get_page_ads(self, ad_type="vuokra-asunnot", page: int = 1) -> List[str]:
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

        self.driver.get(self.BaseURL.format(category=ad_type, page=page))
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.driver.implicitly_wait(10)
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)

        # Additional wait for complete rendering
        with open("test.html", mode = "w", encoding="utf-8") as f:
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
