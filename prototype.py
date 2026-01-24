# %%
from lib import By, WebDriverWait, EC
import json
import requests
from lib.oikotieScrapper import convert_xml_row_to_dict
from lib import setupDriver


# %%
base_url = "https://asunnot.oikotie.fi/vuokra-asunnot?pagination={page}"
driver = setupDriver.setup_driver()

# Initiate the Chromedriver by passing options as argument
# %%


driver.get(base_url.format(page=2))
WebDriverWait(driver, 10).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
# %%
elements = driver.find_elements(By.XPATH, "//a[@href]")

links = [elem.get_attribute("href") for elem in elements]
# %%

ads = [s for s in links if s.split("/")[-1].isdigit()]

# %%
ad_url = ads[0]
with open(f"data/htmls/{ad_url.split('/')[-1]}.html", mode="w", encoding="utf-8") as f:
    html_str = requests.get(ad_url).text
    f.write(html_str)

# %%
driver.get(ad_url)
scripts = driver.find_elements(By.TAG_NAME, 'script')

# Iterate over all to find the one with the target start pattern
target_script_content = None
for script in scripts:
    content = script.get_attribute('innerHTML')
    if content.strip().startswith('var otAsunnot'):
        target_script_content = content
        break


# %%
metadata = json.loads(target_script_content.replace("var otAsunnot=", "").split(";")[0]).get("analytics")
# %%
rows = driver.find_elements(By.CLASS_NAME, "info-table__row")
table_dict = [
    convert_xml_row_to_dict(row.get_attribute("innerHTML"), info_type="info-table__")
    for row in rows[:-1]
]  # Last item is skkipped because by structure is errored.
table_dict = {i[0]: i[1] for i in table_dict if i is not None}

# Grid information is already in the tables.

grid_data = driver.find_elements(By.CLASS_NAME, "details-grid__item-text")
grid_dict = [
    convert_xml_row_to_dict(
        row.get_attribute("innerHTML"), info_type="details-grid__item-"
    )
    for row in grid_data
]
# %%