"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_RE = re.compile(
    r"(?:(?:under|below|less than|up to|max(?:imum)?|at most|<=?)\s*\$?\s*|\$\s*)"
    r"(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE_RE = re.compile(r"\bsize\s+([A-Za-z0-9./-]+(?:\s*x\s*\d+)?)", re.IGNORECASE)


def _parse_query(query: str) -> dict:
    """Pull description, size and max_price out of a plain-language query."""
    text = query
    max_price = None
    size = None

    m = _PRICE_RE.search(text)
    if m:
        max_price = float(m.group(1))
        text = text[:m.start()] + " " + text[m.end():]

    m = _SIZE_RE.search(text)
    if m:
        size = m.group(1).strip()
        text = text[:m.start()] + " " + text[m.end():]

    text = re.sub(r"\b(looking for|i want|i need|find me|a|an)\b", " ", text, flags=re.IGNORECASE)
    description = re.sub(r"[\s,]+", " ", text).strip(" ,.")
    # Removing "size 99" / "under $5" can strand a connector word at either end.
    description = re.sub(
        r"^(?:in|for|with|and)\s+|\s+(?:in|for|with|and)$", "", description, flags=re.IGNORECASE
    )
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Tell the user what they could change, based on what they constrained."""
    message = (
        f"Nothing matched \"{parsed['description']}\". Try broader keywords first "
        f"(e.g. \"jacket\" instead of a specific style)."
    )
    limits = []
    if parsed["max_price"] is not None:
        limits.append(f"your ${parsed['max_price']:g} budget")
    if parsed["size"]:
        limits.append(f"size {parsed['size']}")
    if limits:
        message += (
            f" {' and '.join(limits).capitalize()} may also be ruling things out, "
            f"so loosen one at a time to see which."
        )
    return message


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    trace.start_trace()

    count = 0
    while True:
        count += 1
        trace.check_iterations(count)

        # Parse (regex): description is the query minus the size and price phrases.
        session["parsed"] = _parse_query(session["query"])
        trace.step("parse_query", inputs=session["query"], returned=session["parsed"])

        # Search — inputs read back out of the session.
        search_inputs = {
            "description": session["parsed"]["description"],
            "size": session["parsed"]["size"],
            "max_price": session["parsed"]["max_price"],
        }
        session["search_results"] = call_tool("search_listings", search_inputs)
        trace.step("search_listings (via MCP)", inputs=search_inputs,
                   returned=session["search_results"])

        # THE BRANCH: nothing found — stop before suggest_outfit.
        if not session["search_results"]:
            session["error"] = _no_results_message(session["parsed"])
            trace.step("branch: no results", note="stopping before suggest_outfit")
            return session

        # Choose: first (highest-scored) result.
        session["selected_item"] = session["search_results"][0]
        trace.step("select_item", inputs="first search result",
                   returned=session["selected_item"])

        # Suggest, then caption. Both call the model, which can be unreachable.
        try:
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            trace.step("suggest_outfit",
                       inputs={"item": session["selected_item"].get("title"),
                               "wardrobe_items": len(session["wardrobe"].get("items", []))},
                       returned=session["outfit_suggestion"])

            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            trace.step("create_fit_card",
                       inputs=session["selected_item"].get("title"),
                       returned=session["fit_card"])
        except ModelUnavailable as exc:
            session["error"] = str(exc)
            trace.step("branch: ModelUnavailable", note="stopping, error set on session")
        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
