from typing import List, Dict
from app.utils import GDPRCompliance


def process(entry: Dict) -> Dict:
    # Key addition processes
    entry["ad_type"] = extract_type(entry)
    entry["ad_name"] = extract_name(entry)
    entry["floor_size"] = extract_floorsize(entry)
    entry["property_condiction"] = extract_condition(entry)
    entry = process_address(entry)
    entry = process_the_geo(entry)
    entry = process_offers_entry(entry)
    # key removal processes
    entry = remove_redundant_info(entry)

    # TODO: implement key validation. If extra keys are added, migrate the database and warn the developer.
    return entry

def remove_redundant_info(entry: Dict) -> Dict:
    """Removing keys that their value is not useful

    Here is the list of keys:
    `image` -> The thumbnail image of the ad
    `brand` -> Information is the duplicate of `offers`
    `offers` -> Data is already extracted
    `floorSize` -> Data is already extracted
    `@type` -> Data is already extracted
    `@context` -> Data is already extracted
    `itemCondition` -> Data is already extracted
    """
    for k in ["image", "brand", "offers", "floorSize", "@type", "name", "@context", "itemCondition"]:
        entry.pop(k, None)
    return entry


def extract_type(entry: Dict) -> str:
    """Extracting the `@type` entry of json_data"""
    return ",".join([s for s in entry.get("@type", []) if s != "Product"])


def extract_name(entry: Dict) -> str:
    """Processing the 'name' entry of json_data"""
    return entry.get("name", "").split("|")[0].strip()


def extract_floorsize(entry: Dict) -> float | None:
    """Extract the floor size from json_data

    The nested dictionary contains information that is identical across all entries.
    Therefore, only the floor area is extracted.
    """
    return entry.get("floorSize", {}).get("value")


def extract_number_of_rooms(entry) -> int:
    """Extract the count of rooms"""
    return entry.get("numberOfRooms")


def extract_pet_permission(entry: Dict) -> str:
    """Extract the pet permission string

    The information is in string format with explaination.
    INFO: Further processing is needed to make the data usable for analysis.
    """
    return entry.get("petsAllowed", "")


def process_address(entry: Dict) -> Dict:
    """processing the nested address

    The address is in nested dictionary.

    The address is flattened and porcessed accordingly
    The `locality`is the list of localities in the string.
    """
    address_dict: Dict = entry.get("address", {})
    entry["country"] = address_dict.get("addressCountry", None)
    entry["region"] = address_dict.get("addressRegion", None)
    entry["postal_code"] = address_dict.get("postalCode", None)
    entry["street_address"] = address_dict.get("streetAddress", None)
    entry["locality"] = [
        s.strip() for s in address_dict.get("addressLocality", "").split(",")
    ]
    entry.pop("address", None)

    return entry


def extract_condition(entry:Dict) -> str:
    return entry.get("itemCondition", {}).get("name")

def process_the_geo(entry: Dict) -> Dict:
    """Extract the coordinates of the data."""
    entry["latitude"] = entry.get("geo", {}).get("latitude")
    entry["longitude"] = entry.get("geo", {}).get("longitude")
    entry.pop("geo", None)
    return entry


def process_offers_entry(entry: Dict) -> Dict:
    """Processing Offer information
    
    """
    
    offer_info: Dict = entry.get("offers", {})

    entry: Dict = process_seller(entry)
    entry["price"] = offer_info.get("price", None)
    entry["price_currency"] = offer_info.get("priceCurrency", None)

    return entry


def process_seller(entry: Dict) -> Dict:
    """
    List of removed info:
    - seller type
    - seller phone
    - org type
    - org log
    - org url
    - org phone

    GDPR Processed:

    - seller name
    - seller job titles


    seller_name <- seller.get('name', '') # FIX: GDPR
    jobTitle <- seller.get('jobTitle', '') # FIX: GDPR

    """

    seller_info: Dict = entry.get("offer", {}).get("seller", {})
    entry["seller_name"] = GDPRCompliance.GDPRCleaner(seller_info.get("name", ""))
    entry["jobtitle"] = process_seller_job_title(seller_info.get("jobTitle", ""))
    entry["seller_company"] = seller_info.get("worksFor", {}).get("name")
    entry["seller_company_add"] = seller_info.get("worksFor", {}).get("address")
    return entry


def process_seller_job_title(jobtitle_str: str | None) -> List[str] | None:
    if jobtitle_str is None:
        return
    jobtitle_str = (
        jobtitle_str.replace("/\n", "/").replace(  # correcting the slash
            "\n", ","
        )  # spliting the new lines
    )
    if jobtitle_str == "":
        return
    return [GDPRCompliance.GDPRCleaner(s).strip() for s in jobtitle_str.split(",")]
