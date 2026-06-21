from unittest.mock import patch

from tools import search_listings

# Minimal listing factory to keep fixtures concise
def _listing(id, title, description, price, size, tags=None):
    return {
        "id": id,
        "title": title,
        "description": description,
        "category": "tops",
        "style_tags": tags or [],
        "size": size,
        "condition": "good",
        "price": price,
        "colors": [],
        "brand": None,
        "platform": "depop",
    }


CHEAP = _listing("lst_cheap", "Vintage Tee", "vintage graphic tee", 20.0, "M", ["vintage"])
EXPENSIVE = _listing("lst_exp", "Vintage Tee Expensive", "vintage graphic tee", 60.0, "M", ["vintage"])
SIZE_M = _listing("lst_m", "Graphic Tee M", "graphic tee", 25.0, "M", ["graphic"])
SIZE_XL = _listing("lst_xl", "Graphic Tee XL", "graphic tee", 25.0, "XL", ["graphic"])


def test_price_filter():
    with patch("tools.load_listings", return_value=[CHEAP, EXPENSIVE]):
        results = search_listings("vintage tee", max_price=30.0)

    assert all(item["price"] <= 30.0 for item in results)
    ids = [item["id"] for item in results]
    assert "lst_cheap" in ids
    assert "lst_exp" not in ids


def test_size_filter():
    with patch("tools.load_listings", return_value=[SIZE_M, SIZE_XL]):
        results = search_listings("graphic tee", size="M")

    assert all("M" in item["size"].upper() for item in results)
    ids = [item["id"] for item in results]
    assert "lst_m" in ids
    assert "lst_xl" not in ids


def test_output_assertions():
    # 1. Normal match: 5 listings → at most 3 returned, correct shape
    five_listings = [
        _listing(f"lst_{i}", "vintage tee item", "vintage graphic tee", 20.0, "M", ["vintage"])
        for i in range(5)
    ]
    with patch("tools.load_listings", return_value=five_listings):
        results = search_listings("vintage tee")

    assert isinstance(results, list)
    assert len(results) <= 3
    required_keys = {"id", "title", "description", "price", "size", "category", "style_tags", "colors", "brand", "platform"}
    for item in results:
        assert isinstance(item, dict)
        assert required_keys.issubset(item.keys())

    # 2. No keyword match → empty list
    no_match = [_listing("lst_no", "Summer Dress", "floral sundress", 15.0, "S", ["floral"])]
    with patch("tools.load_listings", return_value=no_match):
        results = search_listings("vintage tee")

    assert results == []

    # 3. Empty load → empty list
    with patch("tools.load_listings", return_value=[]):
        results = search_listings("vintage tee")

    assert results == []
