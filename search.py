"""
fashion_detector/search.py
Product search via SerpAPI Google Shopping.
Given a detected fashion item dict, returns purchasable product results.
"""

import concurrent.futures
from serpapi import GoogleSearch


# Fields that are too vague to include in a search query
_SKIP_PATTERNS = {"solid", "other", "n/a"}
_SKIP_MATERIALS = {"n/a", "unknown"}
_SKIP_FITS = {"n/a", "regular", "fitted"}  # too generic, add noise


def build_query(item: dict) -> str:
    """
    Build a Google Shopping search query from a detected fashion item.
    Strategy: be specific but not so specific that zero results come back.
    Order: subtype → primary color → pattern (if not solid) → material (if distinctive)
    """
    parts = []

    # 1. Most specific garment name first
    subtype = item.get("item_subtype", "").strip()
    item_type = item.get("item_type", "").strip()
    parts.append(subtype if subtype and subtype != "n/a" else item_type)

    # 2. Primary color (first in list)
    colors = item.get("colors", [])
    if colors:
        parts.append(colors[0])

    # 3. Pattern only if distinctive (skip "solid")
    pattern = item.get("pattern", "")
    if pattern and pattern not in _SKIP_PATTERNS:
        parts.append(pattern)

    # 4. Material only if distinctive (skip cotton/fabric — too generic)
    material = item.get("material_guess", "")
    distinctive_materials = {"silk", "satin", "velvet", "denim", "leather",
                              "chiffon", "linen", "lace", "knit", "organza",
                              "georgette", "crepe", "brocade", "net"}
    if material and material.lower() in distinctive_materials:
        parts.append(material)

    # 5. First style tag if it's culturally specific (helps for Indian content)
    style_tags = item.get("style_tags", [])
    cultural_tags = {"traditional", "ethnic", "bridal", "festive", "saree",
                     "lehenga", "kurta", "anarkali", "indo-western"}
    for tag in style_tags:
        if tag.lower() in cultural_tags:
            parts.append(tag)
            break

    query = " ".join(parts)
    return query


def search_products(item: dict, api_key: str, num_results: int = 5,
                    country: str = "in") -> list[dict]:
    """
    Search Google Shopping for a given fashion item.
    Returns a list of product dicts with: title, price, image, link, retailer, query_used.
    """
    query = build_query(item)

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "gl": country,      # country: "in" = India, "us" = US
        "hl": "en",
        "google_domain": "google.co.in" if country == "in" else "google.com",
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        raw_products = results.get("shopping_results", [])

        products = []
        for p in raw_products[:num_results]:
            products.append({
                "title": p.get("title", ""),
                "price": p.get("price", "N/A"),
                "image": p.get("thumbnail", ""),
                "link": p.get("link", p.get("product_link", "")),
                "retailer": p.get("source", ""),
                "rating": p.get("rating"),
                "reviews": p.get("reviews"),
                "query_used": query,
            })

        return products

    except Exception as e:
        return [{"error": str(e), "query_used": query}]


def search_all_items(items: list[dict], api_key: str, num_results: int = 4,
                     country: str = "in", max_workers: int = 5,
                     min_confidence: float = 0.7) -> dict[int, list[dict]]:
    """
    Search products for all items in parallel.
    Skips items below min_confidence and non-shoppable types.
    Returns a dict keyed by item_id.
    """
    # Item types that aren't worth searching for
    non_shoppable = {"body art", "henna", "tattoo", "sindoor", "makeup",
                     "cosmetic", "hair", "hairstyle"}

    searchable = [
        item for item in items
        if item.get("confidence", 0) >= min_confidence
        and item.get("item_subtype", "").lower() not in non_shoppable
        and item.get("item_type", "").lower() not in non_shoppable
    ]

    results = {}

    def _search_one(item):
        return item["item_id"], search_products(item, api_key, num_results, country)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_search_one, item): item for item in searchable}
        for future in concurrent.futures.as_completed(futures):
            item_id, products = future.result()
            results[item_id] = products

    return results