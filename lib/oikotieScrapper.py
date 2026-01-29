from bs4 import BeautifulSoup
from typing import Dict


# TODO: Make sure all parameters are sanitised
# The contact information must be removed.
# TODO: implement the texts.
# TODO: implement the building information scrappers. https://asunnot.oikotie.fi/talo
# TODO: implement the GDPR compliancy. Use th ecode you made before.

def convert_xml_row_to_dict(html_snippet: str, info_type: str) -> Dict[str, str] | None:
    try:
        soup = BeautifulSoup(html_snippet, 'html.parser')
        key = soup.find("dt", class_=f"{info_type}title").text.strip()
        value = (
            soup.find("dd", class_=f"{info_type}value")
            .get_text(strip=False)
            .replace("\xa0", "")
        )

        return {key: value}
    except Exception as e:
        print(e)
        pass


def get_detail_grids():
    # TODO get all information with the tag details-grid__item-value
    pass


def get_metadata():
    # TODO: makke a script that get the script with type="application/ld+json" tag
    # TODO: the "@type" key must have list value. Other meda scripts are useless.
    pass


def get_location_meta():
    # TODO: there is a meta tag with the coordinates. get them.
    pass


def get_paragraphs():
    # TODO: get the paragraph text information with tags like: paragraph paragraph--keep-formatting margined margined--v20
    pass


def sanitise_GDPR():
    # TODO this script shoudl remove any personal information there is.
    pass


def get_building_link():
    # TODO: you can find the link matching https://asunnot.oikotie.fi/talo
    pass


