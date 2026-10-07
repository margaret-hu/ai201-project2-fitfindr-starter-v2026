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
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Tell the user what they could change, based on what they constrained."""
    tips = []
    if parsed["max_price"] is not None:
        tips.append(f"raise your ${parsed['max_price']:g} budget")
    if parsed["size"]:
        tips.append(f"try a different size than {parsed['size']}")
    tips.append("use broader keywords (e.g. 'jacket' instead of a specific style)")
    return (
        f"Nothing matched \"{parsed['description']}\". You could "
        + ", ".join(tips[:-1]) + (", or " if len(tips) > 1 else "") + tips[-1] + "."
    )


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

    count = 0
    while True:
        count += 1
        trace.check_iterations(count)

        # Parse (regex): description is the query minus the size and price phrases.
        session["parsed"] = _parse_query(session["query"])

        # Search — inputs read back out of the session.
        session["search_results"] = call_tool("search_listings", {
            "description": session["parsed"]["description"],
            "size": session["parsed"]["size"],
            "max_price": session["parsed"]["max_price"],
        })

        # THE BRANCH: nothing found — stop before suggest_outfit.
        if not session["search_results"]:
            session["error"] = _no_results_message(session["parsed"])
            return session

        # Choose: first (highest-scored) result.
        session["selected_item"] = session["search_results"][0]

        # Suggest, then caption.
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
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
