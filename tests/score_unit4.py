"""Render scores from real evidence and explicit, separately reviewed grounding.

python -m tests.score_unit4 results/run_..._before.json results/unit4_before_grounding.json
The program never calls a model or infers semantic correctness from keywords.
"""

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path

import config

NAMES = ["Full three-tool run returns a fit card", "Empty search stops before tool 2",
         "Selected item reaches suggest_outfit unchanged", "Caption grounded in item and outfit",
         "Nonempty search respects the inclusive $20 ceiling"]
TARGETS = [4, 5, 5, 4, 5]


def score(number, record, grounding):
    if record["crashed"] or not record["session"]:
        return False
    session = record["session"]
    steps = record["steps"]
    names = [step["name"] for step in steps]
    if number == 1:
        tool_names = [n for n in names if n in ("search_listings (via MCP)", "suggest_outfit", "create_fit_card")]
        return tool_names == ["search_listings (via MCP)", "suggest_outfit", "create_fit_card"] and not session["error"] and bool((session["fit_card"] or "").strip())
    if number == 2:
        return session["search_results"] == [] and "suggest_outfit" not in names and "create_fit_card" not in names and "broader keywords" in (session["error"] or "")
    if number == 3:
        calls = [s for s in steps if s["name"] == "suggest_outfit"]
        item = session["selected_item"]
        return bool(item and calls and calls[0]["inputs"]["new_item"] == item and item.get("id"))
    if number == 4:
        return grounding["pass"]
    matches = session["search_results"]
    return bool(matches) and all(item["price"] <= 20 for item in matches)


def price_platform_once(record):
    """Supplemental inventory check; never changes an original criterion score."""
    session = record["session"] or {}
    text = session.get("fit_card") or ""
    item = session.get("selected_item") or {}
    if not text or not item:
        return None
    amounts = re.findall(r"\$\s*(\d+(?:\.\d{1,2})?)\b", text)
    platforms = re.findall(re.escape(item["platform"]), text, flags=re.IGNORECASE)
    return len(amounts) == 1 and Decimal(amounts[0]) == Decimal(str(item["price"])) and len(platforms) == 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("grounding", type=Path)
    args = parser.parse_args()
    data = json.loads(args.run.read_text(encoding="utf-8"))
    reviews = json.loads(args.grounding.read_text(encoding="utf-8"))
    assert data["tries"] == 5 and data["cache_enabled"] is False
    assert reviews["run"] == args.run.name
    assert [r["attempt"] for r in reviews["tries"]] == [1, 2, 3, 4, 5]
    cards = data["rows"][3]["tries"]
    for record, review in zip(cards, reviews["tries"]):
        assert isinstance(review["pass"], bool) and review["reason"]
        for quote in review["quotes"]:
            assert quote in record["session"]["fit_card"], "Review quote not in actual response"
    lines = ["| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
             "|---|---|---|---|---|---|---|---|"]
    scores = []
    for number, row in enumerate(data["rows"], 1):
        assert row["scenario"]["criterion"] == number and len(row["tries"]) == 5
        passed = [bool(score(number, record, reviews["tries"][i])) for i, record in enumerate(row["tries"])]
        count = sum(passed)
        verdict = f"{'MET' if count >= TARGETS[number-1] else 'MISSED'} ({count}/5)"
        scores.append({"criterion": number, "passes": passed, "verdict": verdict})
        cells = " | ".join("PASS" if value else "FAIL" for value in passed)
        lines.append(f"| {number}. {NAMES[number-1]} | {TARGETS[number-1]} of 5 | {cells} | {verdict} |")
    supplemental = [{"criterion": row["scenario"]["criterion"], "attempt": i,
                     "price_platform_once": price_platform_once(record)}
                    for row in data["rows"] for i, record in enumerate(row["tries"], 1)
                    if price_platform_once(record) is not None]
    prefix = config.RESULTS_DIR / f"unit4_{data['label']}_scores"
    prefix.with_suffix(".json").write_text(json.dumps({"source": args.run.name, "scores": scores,
                                                   "supplemental": supplemental}, indent=2) + "\n", encoding="utf-8")
    prefix.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"Supplemental price/platform once: {sum(s['price_platform_once'] for s in supplemental)}/{len(supplemental)}")


if __name__ == "__main__":
    main()
