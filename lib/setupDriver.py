from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


class VuokraOptions(Options):
    """Vuokra headless options
    This class is making a customised Option class for selenium driver that runs headless.
    Parameters
    ----------
    Options : Options
        This is a selenium Options class
    """

    def __init__(self):
        super().__init__()
        self.add_argument("--headless")
        self.add_argument("--no-sandbox")
        self.add_argument("--disable-gpu")
        self.add_argument("window-size=1920,1080")


def setup_driver():
    """Initiating the driver

    Returns
    -------
    Selenium Driver
        This is modified firefox selenium driver that runs headless for scrapping in servers.
    """
    options = VuokraOptions()
    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    return driver
