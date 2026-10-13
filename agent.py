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
from tools import suggest_outfit, create_fit_card
from mcp_client import MCPError, call_tool
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


def run_agent(query: str, wardrobe: dict, *, traced: bool = False) -> dict:
    """Run parse/search/suggest/card stages, returning the visible session state.

    All tool results enter the session before downstream calls read them. The
    empty-search branch stops before either model-backed tool and leaves the
    later fields None. AI-assisted implementation; student review is pending.

    Trace actual inputs and outputs, including failures, without exposing
    provider exception text. The iteration guard stays active on every stage.
    """
    session = new_session(query, wardrobe)
    trace.start_trace(echo=traced)
    stage = "parse"
    iterations = 0

    while True:
        iterations += 1
        trace.check_iterations(iterations)

        if stage == "parse":
            session["parsed"] = _parse_query(session["query"])
            trace.step("parse_query", inputs=session["query"], returned=session["parsed"])
            stage = "search"
        elif stage == "search":
            try:
                session["search_results"] = call_tool("search_listings", session["parsed"])
            except MCPError:
                session["error"] = (
                    "Listing search could not be reached over MCP. Run python "
                    "mcp_client.py to check the local server, then retry."
                )
                trace.step("search_listings (via MCP)", inputs=session["parsed"],
                           returned={"error": session["error"]})
                return session
            trace.step("search_listings (via MCP)", inputs=session["parsed"],
                       returned=session["search_results"])
            if not session["search_results"]:
                session["error"] = (
                    "No matching listings. Try broader keywords, a different "
                    "size, or a higher price ceiling."
                )
                trace.step("branch", returned=session["error"], note="empty search; stop before tool 2")
                return session
            session["selected_item"] = session["search_results"][0]
            trace.step("select_item", returned=session["selected_item"])
            stage = "suggest"
        elif stage == "suggest":
            inputs = {"new_item": session["selected_item"], "wardrobe": session["wardrobe"]}
            try:
                session["outfit_suggestion"] = suggest_outfit(inputs["new_item"], inputs["wardrobe"])
            except ModelUnavailable:
                return _model_failure(session, "suggest_outfit", inputs)
            trace.step("suggest_outfit", inputs=inputs, returned=session["outfit_suggestion"],
                       note="empty wardrobe; general advice" if not wardrobe.get("items") else "")
            stage = "card"
        elif stage == "card":
            inputs = {"outfit": session["outfit_suggestion"], "new_item": session["selected_item"]}
            try:
                session["fit_card"] = create_fit_card(inputs["outfit"], inputs["new_item"])
            except ModelUnavailable:
                return _model_failure(session, "create_fit_card", inputs)
            trace.step("create_fit_card", inputs=inputs, returned=session["fit_card"])
            return session
        else:
            raise RuntimeError("Unknown planning stage: " + stage)


def _model_failure(session: dict, tool: str, inputs: dict) -> dict:
    session["error"] = (
        f"The model is unavailable at {tool}. Check GEMINI_API_KEY in your .env "
        "file and your internet connection, then retry. If both are correct, "
        "wait a minute and try again."
    )
    trace.step(tool, inputs=inputs, returned={"error": session["error"]})
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
