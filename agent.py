"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json
import os

from dotenv import load_dotenv

from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client

load_dotenv()

MAX_LOOPS = os.environ.get("MAX_LOOPS")

if not MAX_LOOPS:
    raise ValueError("MAX_LOOPS not set. Add it to a .env file in the project root.")

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def _build_state_prompt(session: dict) -> str:
    """Build the LLM prompt that describes available tools and current session state."""
    parsed = session.get("parsed", {})
    selected = session.get("selected_item")
    search_count = len(session.get("search_results", []))
    return (
        "You are an AI fashion assistant agent. Decide which tool to call next.\n\n"
        "Available tools:\n"
        "- search_listings: Find clothing items matching the query. Call this first.\n"
        "- suggest_outfit: Suggest outfits for the selected item. Call after search_listings returns results.\n"
        "- create_fit_card: Generate an OOTD caption. Call after suggest_outfit returns a suggestion.\n"
        "- done: Stop the loop. Call when fit_card is complete or an error has occurred.\n\n"
        "Current state:\n"
        f"- Query: \"{session['query']}\"\n"
        f"- Parsed: description=\"{parsed.get('description', '')}\", "
        f"size={parsed.get('size')}, max_price={parsed.get('max_price')}\n"
        f"- Search results: {search_count} items found, "
        f"selected: \"{selected['title'] if selected else 'none'}\"\n"
        f"- Outfit suggestion: {'available' if session.get('outfit_suggestion') else 'none'}\n"
        f"- Fit card: {'available' if session.get('fit_card') else 'none'}\n"
        f"- Error: {session.get('error') or 'none'}\n\n"
        "Return ONLY a JSON object:\n"
        "{\"reasoning\": \"...\", "
        "\"action\": \"search_listings\"|\"suggest_outfit\"|\"create_fit_card\"|\"done\", "
        "\"params\": {\"description\": \"...\", \"size\": null, \"max_price\": null}}\n"
        "params is only used for search_listings — set to {} for all other actions."
    )


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # Initialize session
    session = _new_session(query, wardrobe)
    client = _get_groq_client()

    # Parse query before the loop (per Mermaid: LLM Parse Query → Planning Loop)
    parse_prompt = (
        "Extract the search parameters from this clothing query. "
        "Return ONLY a JSON object with exactly these three fields:\n"
        "- \"description\": the item description (string)\n"
        "- \"size\": alpha clothing size like S, M, L, XL, or null if not mentioned\n"
        "- \"max_price\": maximum price as a number, or null if not mentioned\n\n"
        f"Query: {query}\n\n"
        "Return only the JSON object, nothing else."
    )
    raw_parse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": parse_prompt}],
        temperature=0,
    ).choices[0].message.content.strip()

    try:
        session["parsed"] = json.loads(raw_parse)
    except (json.JSONDecodeError, ValueError):
        session["parsed"] = {"description": query, "size": None, "max_price": None}

    # Planning loop — LLM reasons about which tool to call each iteration
    for _ in range(int(MAX_LOOPS)):
        raw_decision = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _build_state_prompt(session)}],
            temperature=0,
        ).choices[0].message.content.strip()

        try:
            decision = json.loads(raw_decision)
        except (json.JSONDecodeError, ValueError):
            break

        action = decision.get("action", "done")

        if action == "done":
            break

        elif action == "search_listings":
            params = decision.get("params") or {}
            parsed = session["parsed"]
            description = params.get("description") or parsed.get("description") or query
            size = params.get("size") or parsed.get("size")
            max_price = params.get("max_price") or parsed.get("max_price")
            if max_price is not None:
                try:
                    max_price = float(max_price)
                except (TypeError, ValueError):
                    max_price = None

            results = search_listings(description=description, size=size, max_price=max_price)
            session["search_results"] = results
            if not results:
                session["error"] = (
                    "No listings matched your query. Try broadening your search — "
                    "use fewer filters or a more general description."
                )
                break
            session["selected_item"] = results[0]

        elif action == "suggest_outfit":
            if not session.get("selected_item"):
                session["error"] = "Cannot suggest outfit: no item selected yet."
                break
            session["outfit_suggestion"] = suggest_outfit(
                new_item=session["selected_item"],
                wardrobe=wardrobe,
            )

        elif action == "create_fit_card":
            if not session.get("outfit_suggestion"):
                session["error"] = "Cannot create fit card: no outfit suggestion yet."
                break
            session["fit_card"] = create_fit_card(
                outfit=session["outfit_suggestion"],
                new_item=session["selected_item"],
            )

        # All outputs filled — exit early
        if session["fit_card"]:
            break

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
