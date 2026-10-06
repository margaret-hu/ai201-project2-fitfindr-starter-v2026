"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings

_TOKEN_RE = re.compile(r"\d+\.\d+|[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase and split into whole tokens, decimals kept intact.
    "S/M" -> {"s", "m"}; "US 8.5" -> {"us", "8.5"}.
    """
    return set(_TOKEN_RE.findall(text.lower()))


def _listing_tokens(listing: dict) -> set[str]:
    """Build the bag-of-words token set for one listing's searchable text."""
    fields = [
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        " ".join(listing.get("style_tags", [])),
    ]
    return _tokenize(" ".join(fields))


def _score(query_tokens: set[str], listing: dict) -> int:
    """Count how many query tokens appear in the listing's text."""
    return len(query_tokens & _listing_tokens(listing))


def _size_matches(query_tokens: set[str], listing_size: str) -> bool:
    """True if every token in query_tokens appears in listing_size's tokens."""
    return query_tokens.issubset(_tokenize(listing_size))


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()
    size_tokens = _tokenize(size) if size is not None else None

    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size_tokens is not None and not _size_matches(size_tokens, listing["size"]):
            continue
        filtered.append(listing)

    query_tokens = _tokenize(description)

    scored = []
    for listing in filtered:
        score = _score(query_tokens, listing)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    new_item_description = (
        f"{new_item.get('title', 'this item')} "
        f"({new_item.get('category', '')}, {', '.join(new_item.get('colors', []))})"
    )

    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            f"Suggest general styling ideas for this thrifted item:\n"
            f"{new_item_description}\n"
            "Provide one or two outfit suggestions. Be specific about why each "
            "works and how to style it. 2-3 sentences."
        )
    else:
        wardrobe_summary = "\n".join(
            f"- {item['name']} ({item['category']}, {', '.join(item['colors'])})"
            for item in items
        )
        prompt = (
            f"Given the following thrifted item:\n"
            f"{new_item_description}\n"
            f"And the user's wardrobe:\n"
            f"{wardrobe_summary}\n\n"
            "Provide one or two outfit combinations that include the thrifted "
            "item and specific pieces from the wardrobe, naming each piece. "
            "Be specific about why it works and how to style it. 2-3 sentences."
        )

    return generate(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return (
            "No outfit to write a fit card about yet. Get an outfit suggestion "
            "first, then try again."
        )

    title = new_item.get("title", "this item")
    price = new_item.get("price")
    price_text = f"${price:g}" if isinstance(price, (int, float)) else "an unlisted price"
    platform = new_item.get("platform", "a resale app")

    prompt = (
        "Write a short social media caption (2-4 sentences) for someone "
        "posting their second-hand find.\n"
        f"Item: {title}\n"
        f"Price: {price_text}\n"
        f"Platform: {platform}\n"
        f"How they'd wear it: {outfit}\n\n"
        "It should sound like a real person's post, not a product description. "
        "Mention the item, the price (written with digits, e.g. $24) and the "
        "platform once each, and be specific about the vibe. "
        "Plain text, no hashtags."
    )

    return generate(prompt)
