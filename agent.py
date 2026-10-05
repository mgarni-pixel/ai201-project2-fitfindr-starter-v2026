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
from tools import search_listings, suggest_outfit, create_fit_card
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


# ── query parsing ────────────────────────────────────────────────────────────

_PRICE_CLAUSE = re.compile(
    r"\b(?:under|below|up\s+to|max|at\s+most)\s*\$?\s*(-?\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
_DOLLAR_AMOUNT = re.compile(r"\$\s*(-?\d+(?:\.\d+)?)\b")
_SIZE_CLAUSE = re.compile(
    r"\b(?:in\s+)?size\s+(one\s+size|extra\s+(?:small|large)|"
    r"w\s*\d+(?:(?:\s*/\s*|\s+)l\s*\d+)?|"
    r"(?:us\s*)?\d+(?:\.\d+)?(?:\s*/\s*(?:us\s*)?\d+(?:\.\d+)?)*|"
    r"[a-z0-9.]+(?:\s*/\s*[a-z0-9.]+)*)\b(?!\.[a-z0-9]|/|\s*/)",
    re.IGNORECASE,
)
_REQUEST_WORDS = {
    "a", "an", "and", "find", "for", "i", "in", "looking", "look", "me",
    "of", "or", "please", "some", "something", "the", "to", "want", "with",
}


def _parse_query(query: str) -> dict:
    """Extract optional filters without a model; preserve unsupported sizes."""
    remaining = query
    price = _PRICE_CLAUSE.search(remaining) or _DOLLAR_AMOUNT.search(remaining)
    max_price = float(price.group(1)) if price else None
    if price:
        remaining = remaining[:price.start()] + " " + remaining[price.end():]

    size_match = _SIZE_CLAUSE.search(remaining)
    size = " ".join(size_match.group(1).split()).upper() if size_match else None
    if size_match:
        remaining = remaining[:size_match.start()] + " " + remaining[size_match.end():]

    words = re.findall(r"[a-z0-9]+", remaining, re.IGNORECASE)
    description = " ".join(word for word in words if word.casefold() not in _REQUEST_WORDS)
    return {"description": description, "size": size, "max_price": max_price}


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """Run parse/search/suggest/card stages, returning the visible session state.

    All tool results enter the session before downstream calls read them. The
    empty-search branch stops before either model-backed tool and leaves the
    later fields None. AI-assisted implementation; student review is pending.

    Unit 4 can add trace.step calls and a ModelUnavailable handler using the
    starter imports. The iteration guard is already active on every stage.
    """
    session = new_session(query, wardrobe)
    stage = "parse"
    iterations = 0

    while True:
        iterations += 1
        trace.check_iterations(iterations)

        if stage == "parse":
            session["parsed"] = _parse_query(session["query"])
            stage = "search"
        elif stage == "search":
            session["search_results"] = search_listings(
                description=session["parsed"]["description"],
                size=session["parsed"]["size"],
                max_price=session["parsed"]["max_price"],
            )
            if not session["search_results"]:
                session["error"] = (
                    "No matching listings. Try broader keywords, a different "
                    "size, or a higher price ceiling."
                )
                return session
            session["selected_item"] = session["search_results"][0]
            stage = "suggest"
        elif stage == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            stage = "card"
        elif stage == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            return session
        else:
            raise RuntimeError("Unknown planning stage: " + stage)


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
