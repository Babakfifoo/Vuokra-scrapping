from bs4 import BeautifulSoup
from typing import Dict, List, Any
import re
import json
from icecream import ic
from datetime import date
import logging
# The add overview is like this: class="listing-overview"
# the containers for each table is: "class="listing-details""
# get the table title
# get each row information


def get_location_meta(soup: BeautifulSoup) -> Dict[str, str | None]:
    """extract metadata tages.
    This function extract the location from the metadata.
    The location is only available here. Therefore this function is necessary


    Parameters
    ----------
    soup : BeautifulSoup
        The bs4 object created from the html file

    Returns
    -------
    List[float|None]
        A list containing the lat and lon of the ad.
    """
    result_pt = dict()

    for val in ["latitude", "longitude"]:
        tag = soup.find("meta", {"property": f"place:location:{val}"})
        result_pt[val] = tag.get("content") if tag else None

    return result_pt


def get_script_json_data(soup: BeautifulSoup) -> List[Any]:
    """Extract script tags with type=application/ld+json

    These script tags contain information sent for the database. They contain some information that is not available in the metadata nor the ad tables.

    Parameters
    ----------
    soup : BeautifulSoup
        The bs4 object created from the html file

    Returns
    -------
    List[Any]
        A list of parsed JSON-LD objects (dicts) excluding common metadata types.
    """

    # Return parsed JSON-LD objects, excluding common non-data types
    return extract_jsonld_from_soup_filtered(soup)


def get_script_meta_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract script with `var otAsunnot` contents.
    This script extract and parse the json data nested as js script.
    The information is the clean version of most of the data obtained from the database.


    Parameters
    ----------
    soup : BeautifulSoup
        The bs4 object created from the html file

    Returns
    -------
    Dict[str,Any]
        A dictionary with the data as nested dict.
    """

    script_tag = soup.find("script", string=re.compile("var otAsunnot"))  # type: ignore

    if script_tag:
        script_content = script_tag.string.split("=", 1)[-1].split("};")[0] + "}"
    else:
        logging.info(f"No Meta found for this webpage.")
    return json.loads(
        script_content
    ).get("analytics")


def extract_jsonld_from_soup_filtered(
    soup: BeautifulSoup, exclude_types: List[str] | None = None
) -> List[Any]:
    """Extract JSON-LD objects from soup and filter out unwanted `@type` values.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML soup
    exclude_types : List[str] | None
        List of `@type` values to exclude (case-sensitive). Defaults to
        ['Organization', 'WebSite', 'BreadcrumbList'].

    Returns
    -------
    List[Any]
        List of parsed JSON objects (dicts) that do not have an excluded `@type`.
    """
    if exclude_types is None:
        exclude_types = ["Organization", "WebSite", "BreadcrumbList"]

    results: List[Any] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        text = (tag.string or tag.get_text() or "").strip()
        if not text:
            continue
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # try to recover concatenated objects like: "{}\n{}"
            fixed = re.sub(r"}\s*{", "},{", text)
            if (
                fixed.startswith("{")
                and fixed.endswith("}")
                and not fixed.startswith("[")
            ):
                fixed = f"[{fixed}]"
            try:
                parsed = json.loads(fixed)
            except Exception:
                parsed = None

        if parsed is None:
            continue

        objs = parsed if isinstance(parsed, list) else [parsed]
        for obj in objs:
            if not isinstance(obj, dict):
                # keep non-dict JSON values
                results.append(obj)
                continue
            if obj.get("@type") not in exclude_types:
                results.append(obj)

    return results


def get_table_htmls_sections(soup: BeautifulSoup) -> Dict:
    """Extract innerHTML tables.
    There are inner html objects that contain the tables.
    Each table has a header. The header is set as the key, and the inner HTML table bs4 object is the value.

    Parameters
    ----------
    soup : BeautifulSoup
        The bs4 object created from the html file

    Returns
    -------
    Dict[str, BeautifulSoup]
        A dictionary with table name as key and bs4 inner html object as value.
    """
    tables = soup.find_all("div", class_="listing-details")
    table_parsed = {}
    if not tables:
        return table_parsed

    for table in tables:
        table_parsed.update(generate_table_from_html(table))
    return table_parsed


def generate_table_from_html(table_div) -> Dict[str, Any]:
    """Clean HTML table
    This script converts the inner HTML bs4 object into a clean json file containing the information of the table.
    The table is generated by processing the <dd> and <dt> tags.

    Parameters
    ----------
    soup : BeautifulSoup
        innerHTML b4 objetc containing a table.

    Returns
    -------
    Dict[str, Any]
        a dictionary of the table.
    """
    """
    Parses a listing-details div and returns a dictionary of its rows.
    """
    results = {}
    title = table_div.find("h3", class_="heading--title-2")
    category_name = title.get_text(strip=True) if title else "Unknown Category"
    # Find all rows within this specific table container
    rows = table_div.find_all("div", class_="info-table__row")

    for row in rows:
        results.update(get_row_from_HTML(row))

    return {category_name: results}


def get_row_from_HTML(row):
    key_node = row.find("dt", class_="info-table__title")
    val_node = row.find("dd", class_="info-table__value")

    if key_node and val_node:
        # .strip() handles whitespace, .replace handles non-breaking spaces
        key = key_node.get_text(strip=True)
        val = (
            val_node.get_text(strip=True)
            .replace("\xa0", " ")
            .replace("\t", "")
            .replace("\n", " ")
        )
    return {key: val}


def get_ad_description(soup: BeautifulSoup) -> Dict[str, str | List[str]]:
    """Extracting overview text and caption
    This script converts bs4 object to a dictionary that contains the caption of the ad, and lis of paragraph texts in the add

    Parameters
    ----------
    soup : BeautifulSoup
        bs4 object of the whole webpage

    Returns
    -------
    Dict[str,str|List[str]]
        A dictionary containing the caption and the ad's text.
    """
    caption_div = soup.find("div", class_="listing-share__caption")

    if caption_div:
        text = caption_div.get_text(strip=True)

    description_txt = []
    listing_div = soup.find("div", class_="listing-overview")
    if listing_div:
        paragraphs = listing_div.find_all("p")

        # Loop through and print the text
        for p in paragraphs:
            description_txt.append(p.get_text(strip=True).replace("\t", ""))

    return {"caption": text, "overview": description_txt}


def compile_record_json(soup=BeautifulSoup) -> dict[str, Any]:
    result_data = {}
    result_data["description"] = get_ad_description(soup=soup)
    result_data["tables"] = get_table_htmls_sections(soup=soup)
    result_data["json_data"] = get_script_json_data(soup)
    result_data["metadata"] = get_script_meta_data(soup)
    result_data["location"] = get_location_meta(soup)
    result_data["AccessId"] = create_oiko_id(result_data)
    return result_data


def create_oiko_id(data: Dict["str", Any]) -> str:
    return str(date.today()) + "-" + str(data.get("metadata", {}).get('cardId', ""))
