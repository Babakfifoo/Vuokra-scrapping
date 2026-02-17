from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver
from webdriver_manager.firefox import GeckoDriverManager



class VuokraOptions(Options):
    """Vuokra headless options
    This class is making a customised Option class for selenium driver that runs headless.
    Parameters
    ----------
    Options : Options
        This is a selenium Options class
    """

    def __init__(self) -> None:
        super().__init__()
        self.add_argument('--headless=new')
        self.add_argument('--no-sandbox')
        self.add_argument('--disable-dev-shm-usage')
        self.add_argument('--disable-gpu')
        self.add_argument('--window-size=1920,1080')
        self.add_argument('--disable-blink-features=AutomationControlled')
        self.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

def setup_driver() -> WebDriver:
    """Initiating the driver

    Returns
    -------
    Selenium Driver
        This is modified firefox selenium driver that runs headless for scrapping in servers.
    """
    chrome_options = VuokraOptions()
    # chrome_options.page_load_strategy = 'normal'
    driver: WebDriver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=chrome_options
    )
    return driver
