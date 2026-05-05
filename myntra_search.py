from urllib.parse import quote_plus


CATEGORY_SLUGS: dict[str, str] = {
    "top": "tops", "shirt": "shirts", "blouse": "tops",
    "t-shirt": "tshirts", "tshirt": "tshirts", "tank top": "tops",
    "crop top": "tops", "sweatshirt": "sweatshirts", "hoodie": "sweatshirts",
    "jeans": "jeans", "trousers": "trousers", "pants": "trousers",
    "shorts": "shorts", "skirt": "skirts", "leggings": "leggings",
    "dress": "dresses", "jumpsuit": "jumpsuits", "romper": "jumpsuits",
    "co-ord set": "co-ords", "co-ord": "co-ords",
    "jacket": "jackets", "blazer": "blazers", "coat": "coats",
    "cardigan": "sweaters", "sweater": "sweaters",
    "saree": "sarees", "sari": "sarees",
    "kurti": "kurtis", "kurta": "kurtas",
    "lehenga": "lehenga-cholis", "anarkali": "anarkalis",
    "salwar suit": "salwar-suits", "salwar": "salwar-suits",
    "dupatta": "dupattas", "sherwani": "sherwanis",
    "dhoti": "ethnic-wear", "sharara": "ethnic-wear",
    "sneakers": "sneakers", "shoes": "shoes", "heels": "heels",
    "sandals": "sandals", "boots": "boots", "flats": "flats",
    "loafers": "casual-shoes", "slippers": "flip-flops",
    "handbag": "handbags", "bag": "handbags", "tote": "handbags",
    "clutch": "clutches", "backpack": "backpacks",
    "sling bag": "sling-bags", "wallet": "wallets",
    "belt": "belts", "hat": "caps", "cap": "caps",
    "sunglasses": "sunglasses", "watch": "watches",
    "necklace": "necklaces", "earrings": "earrings",
    "bracelet": "bracelets", "ring": "rings",
    "scarf": "scarves", "stole": "scarves",
}

_SKIP_PATTERNS = {"solid", "other", "n/a"}
_DISTINCTIVE_MATERIALS = {
    "silk", "satin", "velvet", "denim", "leather", "chiffon", "linen",
    "lace", "knit", "organza", "georgette", "crepe", "brocade", "net",
    "handloom", "zari", "ikat", "chanderi", "banarasi",
}
_CULTURAL_TAGS = {
    "traditional", "ethnic", "bridal", "festive", "indo-western",
    "bohemian", "boho", "formal", "party wear",
}
_NON_SHOPPABLE = {
    "body art", "henna", "tattoo", "sindoor", "makeup", "cosmetic", "hair", "hairstyle",
}


def _get_slug(item: dict) -> str:
    return CATEGORY_SLUGS.get(item.get("item_type", "").strip().lower(), "fashion")


def _build_query(item: dict) -> str:
    parts = []

    subtype = item.get("item_subtype", "").strip()
    item_type = item.get("item_type", "").strip()
    parts.append(subtype if subtype and subtype.lower() not in ("n/a", "") else item_type)

    colors = item.get("colors", [])
    if colors:
        parts.append(colors[0])

    pattern = item.get("pattern", "").lower()
    if pattern and pattern not in _SKIP_PATTERNS:
        parts.append(pattern)

    material = item.get("material_guess", "").lower()
    if material and material in _DISTINCTIVE_MATERIALS:
        parts.append(material)

    for tag in item.get("style_tags", []):
        if tag.lower() in _CULTURAL_TAGS:
            parts.append(tag)
            break

    return " ".join(parts)


def build_myntra_url(item: dict) -> str:
    slug = _get_slug(item)
    query = _build_query(item)
    return f"https://www.myntra.com/{slug}?rawQuery={quote_plus(query)}"


def build_myntra_urls(items: list[dict], min_confidence: float = 0.6) -> dict[int, dict]:
    results = {}
    for item in items:
        if item.get("confidence", 0) < min_confidence:
            continue
        if item.get("item_type", "").lower() in _NON_SHOPPABLE:
            continue
        if item.get("item_subtype", "").lower() in _NON_SHOPPABLE:
            continue
        query = _build_query(item)
        slug = _get_slug(item)
        results[item["item_id"]] = {
            "url": f"https://www.myntra.com/{slug}?rawQuery={quote_plus(query)}",
            "query": query,
            "category": slug,
        }
    return results