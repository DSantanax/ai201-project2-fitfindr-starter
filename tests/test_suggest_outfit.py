from unittest.mock import MagicMock, patch

from tools import suggest_outfit

ITEM = {
    "id": "lst_001",
    "title": "Vintage Levi's Denim Jacket",
    "description": "Classic 90s denim jacket in light wash",
    "category": "outerwear",
    "style_tags": ["vintage", "denim", "90s"],
    "size": "M",
    "condition": "good",
    "price": 45.0,
    "colors": ["light blue"],
    "brand": "Levi's",
    "platform": "depop",
}

WARDROBE_WITH_ITEMS = {
    "items": [
        {
            "id": "w_001",
            "name": "Baggy straight-leg jeans, dark wash",
            "category": "bottoms",
            "colors": ["dark blue"],
            "style_tags": ["denim", "streetwear"],
            "notes": "High-waisted",
        },
        {
            "id": "w_002",
            "name": "White ribbed tank top",
            "category": "tops",
            "colors": ["white"],
            "style_tags": ["basics", "minimal"],
            "notes": None,
        },
    ]
}

EMPTY_WARDROBE = {"items": []}


def _mock_groq(response_text):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = response_text
    return mock_client


def test_empty_wardrobe_returns_string():
    with patch("tools._get_groq_client", return_value=_mock_groq("General styling advice here.")):
        result = suggest_outfit(ITEM, EMPTY_WARDROBE)

    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_empty_wardrobe_does_not_raise():
    with patch("tools._get_groq_client", return_value=_mock_groq("Some advice.")):
        try:
            result = suggest_outfit(ITEM, EMPTY_WARDROBE)
        except Exception as e:
            assert False, f"suggest_outfit raised an exception with empty wardrobe: {e}"

    assert result != ""


def test_nonempty_wardrobe_returns_string():
    with patch("tools._get_groq_client", return_value=_mock_groq("Outfit 1: pair it with your dark wash jeans.")):
        result = suggest_outfit(ITEM, WARDROBE_WITH_ITEMS)

    assert isinstance(result, str)
    assert len(result.strip()) > 0
