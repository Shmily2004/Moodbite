from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any


RESTAURANT_KEYWORDS = [
    "nhà hàng",
    "nhà hàng hải sản",
    "nhà hàng gia đình",
    "nhà hàng món lẩu",
    "quán ăn",
    "quán",
    "quán cafe",
    "cafe",
    "coffee",
    "restaurant",
    "food",
    "eatery",
    "bar",
    "pub",
    "tea house",
    "bubble tea",
    "fast food",
    "buffet",
    "seafood",
    "phở",
    "bún",
    "miến",
    "bánh",
    "cà phê",
    "trà sữa",
]

EXCLUDED_KEYWORDS = [
    "khách sạn",
    "hotel",
    "resort",
    "cửa hàng",
    "siêu thị",
    "market",
    "grocery",
    "supermarket",
    "chăn nuôi",
    "pet",
    "farm",
    "motel",
    "homestay",
    "hostel",
    "apartment",
    "phòng trọ",
    "nhà nghỉ",
    "spa",
    "salon",
    "beauty",
    "clinic",
    "hospital",
    "pharmacy",
    "bakery",
    "tiệm bánh",
    "lò bánh",
    "bookstore",
    "stationery",
    "car wash",
    "garage",
    "repair",
    "school",
    "university",
    "người cung cấp thực phẩm",
    "nhà cung cấp thực phẩm",
    "cung cấp thực phẩm",
    "công ty",
    "công ty tnnh",
    "công ty tnhh",
    "chi nhánh",
    "viettel",
    "telecom",
    "company",
    "corp",
    "inc",
    "llc",
    "limited",
    "joint stock",
    "investment",
    "trading",
    "commercial",
]


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("\u00a0", " ")
    text = text.replace("-", " ")
    return text


def _iter_item_texts(item: ET.Element) -> List[str]:
    values: List[str] = []
    for tag in ["title", "categoryName", "categories", "description", "subTitle"]:
        node = item.find(tag)
        if node is not None and node.text:
            values.append(node.text)
    return values


def is_restaurant_item(item: ET.Element | Dict[str, Any]) -> bool:
    if isinstance(item, dict):
        texts = " | ".join(
            str(item.get(key) or "")
            for key in ["title", "categoryName", "categories", "description", "subTitle"]
        )
    else:
        texts = " | ".join(_iter_item_texts(item))

    normalized = _normalize(texts)

    if not normalized:
        return False

    if any(keyword in normalized for keyword in EXCLUDED_KEYWORDS):
        return False

    if any(keyword in normalized for keyword in RESTAURANT_KEYWORDS):
        return True

    return False


def filter_restaurant_items(xml_path: str | Path) -> List[Dict[str, Any]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results: List[Dict[str, Any]] = []

    for item in root.findall("item"):
        if not is_restaurant_item(item):
            continue

        record: Dict[str, Any] = {}
        for tag in [
            "title",
            "subTitle",
            "description",
            "price",
            "categoryName",
            "address",
            "neighborhood",
            "street",
            "city",
            "postalCode",
            "state",
            "countryCode",
            "phone",
            "phoneUnformatted",
            "location",
            "plusCode",
            "placeId",
            "categories",
            "fid",
            "cid",
            "reviewsCount",
            "imagesCount",
            "scrapedAt",
        ]:
            node = item.find(tag)
            if node is None:
                record[tag] = None
            elif tag == "location":
                record[tag] = {
                    "lat": node.findtext("lat"),
                    "lng": node.findtext("lng"),
                }
            else:
                record[tag] = node.text

        results.append(record)

    return results


def filter_restaurant_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [record for record in records if is_restaurant_item(record)]


def export_restaurants(input_path: str | Path, output_json: str | Path) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_json)

    if input_path.suffix.lower() == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        filtered = filter_restaurant_records(data)
    else:
        filtered = filter_restaurant_items(input_path)

    output_path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filter restaurant venues from raw XML or JSON data")
    parser.add_argument("input_path", help="Path to the source XML or JSON file")
    parser.add_argument("output_json", nargs="?", help="Path to save the filtered JSON")
    args = parser.parse_args()

    output = args.output_json or str(Path(args.input_path).with_suffix(".restaurants.json"))
    export_restaurants(args.input_path, output)
    print(f"Saved {output}")