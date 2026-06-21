"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _size_matches(query: str, listing_size: str) -> bool:
    query = str(query)
    if re.search(r'\bone\s+size\b', listing_size, re.IGNORECASE):
        return True
    listing_tokens = {t.lower() for t in re.split(r'[\s/(),]+', listing_size) if t}
    query_tokens = [t.lower() for t in re.split(r'[\s/(),]+', query) if t]
    return all(qt in listing_tokens for qt in query_tokens)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    if not listings:
        return []

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size is not None:
        listings = [l for l in listings if _size_matches(size, l["size"])]

    if not listings:
        return []

    keywords = set(description.lower().split())
    scored = []
    for listing in listings:
        searchable = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            " ".join(listing.get("style_tags", [])),
            listing.get("category", ""),
            " ".join(listing.get("colors", [])),
            listing.get("brand", "") or "",
        ]).lower()
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((listing, score))

    if not scored:
        return []

    scored.sort(key=lambda x: x[1], reverse=True)
    return [listing for listing, _ in scored[:3]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    item_summary = (
        f"Title: {new_item.get('title', '')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Brand: {new_item.get('brand') or 'unbranded'}"
    )

    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            "You are a fashion stylist. A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Their wardrobe is currently empty. Give them general styling advice: "
            "what kinds of pieces pair well with this item, what overall vibe or aesthetic it suits, "
            "and how they could start building outfits around it."
        )
    else:
        wardrobe_lines = []
        for i, w in enumerate(items, 1):
            notes = f", notes: {w['notes']}" if w.get("notes") else ""
            wardrobe_lines.append(
                f"{i}. {w.get('name', '')} "
                f"(category: {w.get('category', '')}, "
                f"colors: {', '.join(w.get('colors', []))}, "
                f"tags: {', '.join(w.get('style_tags', []))}{notes})"
            )
        wardrobe_text = "\n".join(wardrobe_lines)

        prompt = (
            "You are a fashion stylist. A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Their existing wardrobe:\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1-2 complete outfit combinations using the new item paired with specific "
            "pieces from their wardrobe. Name the wardrobe pieces you're pairing it with."
        )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "No outfit suggestion was available — try expanding your wardrobe or refining your search to get a fit card."

    prompt = (
        "You are writing a casual, authentic OOTD (Outfit of the Day) caption for social media. "
        "A user just thrifted this item:\n\n"
        f"Item: {new_item.get('title', '')}\n"
        f"Price: ${new_item.get('price', '')}\n"
        f"Platform: {new_item.get('platform', '')}\n"
        f"Brand: {new_item.get('brand') or 'unbranded'}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n\n"
        f"Their outfit: {outfit}\n\n"
        "Write a 2–4 sentence caption that:\n"
        "- Feels casual and authentic, like a real OOTD post\n"
        "- Mentions the item name, price, and platform naturally (once each)\n"
        "- Captures the outfit vibe in specific terms\n"
        "Do not use hashtags. Do not sound like a product listing."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return response.choices[0].message.content
