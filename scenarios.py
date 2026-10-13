"""Five scenarios mapped to the unchanged criteria.md; frozen before evaluation."""

SCENARIOS = [
    {"name": "matching query completes", "query": "vintage graphic tee under $30, size M",
     "wardrobe": "example", "criterion": 1, "mode": "agent"},
    {"name": "impossible query stops early", "query": "designer ballgown size XXS under $5",
     "wardrobe": "example", "criterion": 2, "mode": "agent"},
    {"name": "selected item reaches outfit tool", "query": "denim jacket under $50",
     "wardrobe": "example", "criterion": 3, "mode": "agent"},
    {"name": "caption grounded in fixed item and outfit", "query": "fixed caption inputs",
     "wardrobe": "example", "criterion": 4, "mode": "card", "item_id": "lst_002",
     "outfit": "Wear the baby tee with baggy straight-leg dark wash jeans and chunky white sneakers; add the black crossbody bag."},
    {"name": "inclusive price ceiling", "query": "vintage under $20",
     "wardrobe": "example", "criterion": 5, "mode": "search",
     "arguments": {"description": "vintage", "size": None, "max_price": 20}},
]


def validate() -> list[str]:
    """Reject incomplete or ambiguous criterion mappings before any live requests."""
    problems = []
    if [s.get("criterion") for s in SCENARIOS] != [1, 2, 3, 4, 5]:
        problems.append("provide exactly one scenario for each criterion, numbered 1 through 5")
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in ("example", "empty"):
            problems.append(f"scenario {i} has an unknown wardrobe")
        if scenario.get("mode") not in ("agent", "card", "search"):
            problems.append(f"scenario {i} has an unknown mode")
        if scenario.get("mode") == "card" and (not scenario.get("item_id") or not scenario.get("outfit", "").strip()):
            problems.append(f"scenario {i} needs an item and nonempty outfit")
        if scenario.get("mode") == "search" and not isinstance(scenario.get("arguments"), dict):
            problems.append(f"scenario {i} needs search arguments")
    return problems
