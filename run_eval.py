#!/usr/bin/env python3
"""
Run your scenarios repeatedly and write the results down. ← UNIT 4

    python run_eval.py --label before      five tries, the default
    python run_eval.py --label after       after your improvement
    python run_eval.py --tries 10          more tries

This does the mechanical half of unit 4 for you. It runs every scenario in
`scenarios.py` five separate times, **with caching off** so you get five real
answers, captures the trace and the session for each, and writes it all into
`results/` in the table format the submission asks for.

Five, because your criteria are written out of five — "4 of 5 tries", "5 of 5
tries". One column per try means you count the passes and read the verdict
straight off the row, with no arithmetic in between.

⚠️ What it does NOT do is decide whether a try passed.

That judgment is yours, and it has to be, because it depends on criteria you
wrote. The Verdict column comes out blank and you fill it in from the output
underneath. Deciding what counts as a pass is the lesson — a scorer handed to
you would teach you nothing.

**Two of your three tools call a model, so tries will legitimately differ.**
That is expected here, unlike pair 1. If all five tries come back identical
on a criterion that involves the fit card, check that you're really in test
mode — caching is what usually explains it.
"""

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys

import config
import scenarios as scenario_module


def run_once(scenario, use_trace=True):
    """One scenario, one try. Returns everything worth recording."""
    from agent import new_session, run_agent
    from mcp_client import call_tool
    from tools import create_fit_card
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings
    import generate
    import trace as trace_module

    wardrobe = (
        get_empty_wardrobe() if scenario["wardrobe"] == "empty" else get_example_wardrobe()
    )

    if use_trace:
        trace_module.start_trace(echo=False)

    record = {"error": None, "session": None, "trace": "", "crashed": None}
    calls_before = generate.call_count()
    tokens_before = generate.token_counts()
    try:
        mode = scenario["mode"]
        if mode == "agent":
            record["session"] = run_agent(scenario["query"], wardrobe)
        elif mode == "card":
            session = new_session(scenario["query"], wardrobe)
            session["selected_item"] = next(item for item in load_listings() if item["id"] == scenario["item_id"])
            session["outfit_suggestion"] = scenario["outfit"]
            inputs = {"outfit": session["outfit_suggestion"], "new_item": session["selected_item"]}
            session["fit_card"] = create_fit_card(**inputs)
            trace_module.step("create_fit_card", inputs=inputs, returned=session["fit_card"])
            record["session"] = session
        elif mode == "search":
            session = new_session(scenario["query"], wardrobe)
            session["parsed"] = scenario["arguments"]
            session["search_results"] = call_tool("search_listings", scenario["arguments"])
            trace_module.step("search_listings (via MCP)", inputs=scenario["arguments"], returned=session["search_results"])
            record["session"] = session
        else:
            raise ValueError("Unknown scenario mode")
    except Exception as exc:  # noqa: BLE001 — a crash is a result worth logging
        record["crashed"] = type(exc).__name__
        record["error"] = "Scenario failed; exception type recorded without private provider details."

    if use_trace:
        record["trace"] = trace_module.get_trace()
        record["steps"] = trace_module.get_steps()
    record["model_calls"] = generate.call_count() - calls_before
    record["tokens"] = {key: value - tokens_before[key] for key, value in generate.token_counts().items()}

    return record


def main():
    parser = argparse.ArgumentParser(description="Run the scenarios and log the results.")
    parser.add_argument("--tries", "--trials", type=int, default=5, dest="tries",
                        help="tries per scenario (default 5, matching your criteria)")
    parser.add_argument("--label", default="", choices=["", "before", "after"],
                        help="a name for this run, e.g. 'before'")
    args = parser.parse_args()

    problems = scenario_module.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    if not scenario_module.SCENARIOS:
        print("scenarios.py is empty. Milestone 3 starts by filling it in.", file=sys.stderr)
        sys.exit(1)

    if args.tries < 1:
        parser.error("tries must be positive")
    if args.tries < 5:
        print(f"⚠️  {args.tries} tries. Your criteria are written out of five.\n")

    # Caching off. Five tries have to be five real answers.
    config.CACHE_ENABLED = False
    print("Cache is OFF for this run — that's deliberate.\n")

    rows = []
    for scenario in scenario_module.SCENARIOS:
        print(f"{scenario['name']}  ({scenario['wardrobe']} wardrobe)")
        print(f"  query: {scenario['query']}")

        tries = []
        for attempt in range(1, args.tries + 1):
            record = run_once(scenario)
            tries.append(record)

            if record["crashed"]:
                print(f"  try {attempt}: CRASHED — {record['crashed']}")
            else:
                session = record["session"] or {}
                if session.get("error"):
                    print(f"  try {attempt}: stopped early — {str(session['error'])[:60]}")
                else:
                    card = (session.get("fit_card") or "")
                    print(f"  try {attempt}: completed — fit card {len(card)} chars")

        rows.append({"scenario": scenario, "tries": tries})
        print()

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%S_UTC")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"
    source_files = ["agent.py", "tools.py", "mcp_server.py", "mcp_client.py", "generate.py",
                    "config.py", "trace.py", "scenarios.py", "criteria.md", "run_eval.py",
                    "docs/UNIT4_SCORING.md", "data/listings.json", "data/wardrobe_schema.json"]
    evidence = {
        "label": args.label, "when_utc": now.isoformat(), "tries": args.tries,
        "model": config.MODEL, "temperature": config.TEMPERATURE,
        "cache_enabled": config.CACHE_ENABLED,
        "head_before_run": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {name: hashlib.sha256((config.ROOT / name).read_bytes()).hexdigest()
                          for name in source_files},
        "rows": rows,
    }
    path.with_suffix(".json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    n = args.tries
    headers = " | ".join(f"Try {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Loop: `agent.py::run_agent` · tools: `tools.py`",
        f"- Tries per scenario: {n}, caching off",
        f"- Temperature: {config.TEMPERATURE}",
        f"- Model: {config.MODEL}",
        f"- When (UTC): {now.isoformat()}",
        f"- Complete sessions, actual input snapshots and request counts: `{path.with_suffix('.json').name}`",
        "",
        "Paste the table below into your README. Fill in the Criterion and",
        "Target columns from `criteria.md`, then mark each try PASS or FAIL",
        "from the output underneath and count them for the Verdict.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        # A scenario with "criterion": None is a diagnostic run, not one of
        # your five. It's marked so you don't paste an unnumbered row into a
        # table the README asks you to number 1-5.
        label_text = (
            f"{number}. {scenario['name']}"
            if number
            else f"{scenario['name']} _(diagnostic — not one of your five)_"
        )
        lines.append(f"| {label_text} |  | {' | '.join([' '] * n)} |  |")

    lines += [
        "",
        "> The Try and Verdict columns are blank on purpose. Whether a try",
        "> passed depends on the criterion you wrote, so it's yours to decide.",
        "> Count the passes, then read that count against your target: a row",
        "> targeting 4 of 5 with three PASS cells is MISSED (3/5).",
        "",
        "---",
        "",
        "## What actually happened",
        "",
        "Real output, as text. Paste the relevant parts into your README —",
        "the rubric asks for output, not a description of it.",
        "",
    ]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", "",
                  f"- Query: `{scenario['query']}`",
                  f"- Wardrobe: {scenario['wardrobe']}", ""]

        for i, record in enumerate(row["tries"], 1):
            lines.append(f"**Try {i}**")
            lines.append("")

            if record["crashed"]:
                lines += ["Crashed:", "", "```", record["crashed"], "```", ""]
                continue

            session = record["session"] or {}
            item = session.get("selected_item") or {}
            lines += [
                f"- stopped early: {'yes — ' + str(session.get('error')) if session.get('error') else 'no'}",
                f"- selected_item: {item.get('title', '(none)')}"
                + (f" (${item.get('price')}, {item.get('platform')})" if item else ""),
                f"- search_results: {len(session.get('search_results') or [])}",
                f"- actual model requests: {record['model_calls']}; tokens: {record['tokens']}",
                "",
            ]
            if session.get("outfit_suggestion"):
                lines += ["Outfit suggestion:", "", "```",
                          str(session["outfit_suggestion"]), "```", ""]
            if session.get("fit_card"):
                lines += ["Fit card:", "", "```", str(session["fit_card"]), "```", ""]
            if record["trace"]:
                lines += ["Trace:", "", "```", record["trace"], "```", ""]

    path.write_text("\n".join(line.rstrip() for line in lines).rstrip() + "\n", encoding="utf-8")

    import generate

    print(f"Wrote {path.relative_to(config.ROOT)}")
    print(generate.usage())
    print("\nCommit this file. It's the evidence the test actually happened.")

    if not any(r["tries"][0]["trace"] for r in rows):
        print(
            "\nNote: no trace was captured. You haven't added trace.step() calls\n"
            "to run_agent() yet — that's Milestone 2, and the trace is required\n"
            "evidence worth a point."
        )


if __name__ == "__main__":
    main()
