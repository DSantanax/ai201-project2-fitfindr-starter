from unittest.mock import MagicMock, patch, call

from tools import create_fit_card

ITEM_A = {
    "id": "lst_001",
    "title": "Vintage Levi's Denim Jacket",
    "description": "Classic 90s denim jacket in light wash",
    "category": "outerwear",
    "style_tags": ["vintage", "denim"],
    "size": "M",
    "condition": "good",
    "price": 45.0,
    "colors": ["light blue"],
    "brand": "Levi's",
    "platform": "depop",
}

ITEM_B = {
    "id": "lst_002",
    "title": "Floral Slip Dress",
    "description": "Flowy 90s slip dress with floral print",
    "category": "tops",
    "style_tags": ["vintage", "feminine"],
    "size": "S",
    "condition": "excellent",
    "price": 28.0,
    "colors": ["pink", "white"],
    "brand": None,
    "platform": "poshmark",
}

OUTFIT_A = "Pair the jacket with your dark wash jeans and white tank for a classic streetwear look."
OUTFIT_B = "Layer the slip dress over a fitted white tee with platform shoes for a 90s vibe."


def _mock_groq(response_text):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = response_text
    return mock_client


def test_empty_outfit_returns_error():
    with patch("tools._get_groq_client") as mock_groq:
        result_empty = create_fit_card("", ITEM_A)
        result_whitespace = create_fit_card("   ", ITEM_A)
        mock_groq.assert_not_called()

    assert isinstance(result_empty, str) and len(result_empty) > 0
    assert isinstance(result_whitespace, str) and len(result_whitespace) > 0


def test_valid_outfit_returns_caption():
    expected = "Just thrifted this Levi's denim jacket on depop for $45 and I'm obsessed."
    with patch("tools._get_groq_client", return_value=_mock_groq(expected)) as mock_groq:
        result = create_fit_card(OUTFIT_A, ITEM_A)
        create_kwargs = mock_groq.return_value.chat.completions.create.call_args.kwargs
        assert create_kwargs.get("temperature") == 1.0

    assert isinstance(result, str) and len(result.strip()) > 0


def test_different_inputs_produce_different_outputs():
    caption_a = "Found this Levi's denim jacket on depop for $45 — obsessed."
    caption_b = "This slip dress from poshmark for $28 is giving everything I wanted."

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = caption_a

    with patch("tools._get_groq_client", return_value=mock_client):
        result_a = create_fit_card(OUTFIT_A, ITEM_A)

    mock_client.chat.completions.create.return_value.choices[0].message.content = caption_b

    with patch("tools._get_groq_client", return_value=mock_client):
        result_b = create_fit_card(OUTFIT_B, ITEM_B)

    assert result_a != result_b
