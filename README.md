# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

## Milestone 1: Starter inspection

This is an AI-assisted setup and data record. Student review and the final
AI-use disclosure are still pending. The tools and planning loop are the
unchanged starter at this milestone.

- Read all six records `lst_001` through `lst_006` using `app.py listings --full -n 6`.
- Listing fields: `id` (str), `title` (str), `description` (str), `category` (str),
  `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float),
  `colors` (list[str]), `brand` (str or None), and `platform` (str).
- Wardrobe items use `id`, `name`, `category`, `colors`, `style_tags`, and optional
  `notes`. The supplied wardrobe has 10 items. The loader's empty wardrobe is
  `{"items": []}`; it removes the source JSON's documentation-only `_note`.
- Sizes include `S/M`, `M/L`, `L/XL`, `US 8.5`, and `W30 L30`. A substring check
  would incorrectly match `S` to `US 9` or `L` to `XL`; the next milestone needs
  an explicit size-matching contract. `brand` is null for some listings.
- Python 3.12.14 and a project `.venv` are in use. The original dependency bounds
  are unchanged. This cloud VM also needs `socksio` 1.0.0 for its existing proxy;
  it was installed locally without changing the project requirements.
- The official `python test.py` check passed all 10 checks, including a real
  model call. The starter query prints its expected unbuilt-loop message and
  reports zero model calls; this baseline is not a completed agent.

Actual command output, the six full listings, and the wardrobe schema are in
[results/milestone1_starter.txt](results/milestone1_starter.txt). No acceptance
results or independent student-authorship claims are recorded here.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

These contracts were drafted with AI assistance before implementation. They
remain subject to student review and revision.

### `search_listings`

- **What it does:** Load the supplied listings through `load_listings()`, apply
  optional size and inclusive price filters, and rank positive keyword matches.
- **Inputs:** `description` (str), `size` (str or None, default None), and
  `max_price` (float or None, default None).
- **Returns:** `list[dict]`, at most `config.SEARCH_RESULT_LIMIT` listing dictionaries.
  Every dictionary keeps the source fields `id`, `title`, `description`,
  `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and
  `platform`. Rank by count of distinct shared, case-insensitive word tokens
  across title, description, category, style tags, colors, and optional brand;
  ties keep source order. Apply size/price filters before ranking and limiting.
- **When it has nothing:** Return exactly `[]` for no positive matches, all
  candidates filtered out, or a description with no meaningful keywords.

**Size policy:** Match complete normalized size tokens, never substrings.
`S/M`, `M/L`, and `L/XL` accept either listed clothing size; parenthesized fit
notes do not change a tagged size. `small`, `medium`, `large`, `extra small`,
and `extra large` map to `S`, `M`, `L`, `XS`, and `XL`. A numeric request such
as `8` means `US 8`, and `8.5` never matches `8`. Waist/inseam tokens are
separate: `W30` accepts `W30 L30`, but requesting both requires both.
`One Size` listings match only an explicit one-size request, not every clothing
size. An unsupported explicit size remains a filter and can produce `[]`.

### `suggest_outfit`

- **What it does:** Ask the supplied `generate()` adapter for one or two outfit
  ideas using the selected listing and, when present, actual owned pieces.
- **Inputs:** `new_item` (dict, a listing with the fields above) and `wardrobe`
  (dict with `items: list[dict]`; each owned item uses `id`, `name`, `category`,
  `colors`, `style_tags`, and optional `notes`).
- **Returns:** A nonempty `str` of outfit suggestions. Listing and wardrobe JSON
  are treated as data; nullable brands are not assumed to exist.
- **When it has nothing:** An empty or missing wardrobe `items` list requests
  general styling advice for the new item and does not invent owned pieces.
  A blank model response raises `ModelUnavailable` instead of pretending that
  an outfit was generated; service failures remain distinct from an empty wardrobe.

### `create_fit_card`

- **What it does:** Ask the same adapter for a short postable caption grounded
  in the supplied outfit and listing.
- **Inputs:** `outfit` (str, the outfit suggestion) and `new_item` (dict, the
  selected listing with the source fields above).
- **Returns:** A nonempty `str`. The prompt asks for two to four sentences,
  the item type and an accurate detail, a specific styling detail from the
  outfit, and the item's price and platform once each. Model wording can vary.
- **When it has nothing:** An empty/whitespace-only outfit returns
  `No outfit suggestion was provided. Add an outfit before creating a fit card.`
  without a model call. A blank model response raises `ModelUnavailable`.

---

## Planning Loop

**Branch rule:** If `session["search_results"]` is empty after `search_listings`,
put an error in the session that suggests broader keywords, another size, or a
higher budget, then return without calling `suggest_outfit` or `create_fit_card`.
Otherwise, store the first result in `session["selected_item"]`, suggest an
outfit, create the fit card, and return the session.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** A deterministic regex parser will extract a price
ceiling from `under`, `below`, `up to`, `max`, or `at most` followed by an optional
`$` and a number, or from a standalone dollar amount. It will extract an explicit
`size` clause (including clothing, shoe, waist/inseam, one-size, and unsupported
sizes). The matched clauses and common request filler are removed from the
remaining description. Missing filters become None. The parsed values go into
`session["parsed"]`; parsing does not call the model.

**What moves through the session:** Start a fresh session for every query;
store `query` and `wardrobe`, then `parsed`, `search_results`, `selected_item`,
`outfit_suggestion`, and `fit_card`. Each next tool reads its actual inputs back
from that session. The no-match path leaves the three later result fields None.
A four-stage planning loop (`parse`, `search`, `suggest`, `card`) checks
`trace.check_iterations()` on each iteration and retains `config.MAX_ITERATIONS`.

These are planned contracts at Milestone 2. Implementation and real output are
recorded in the following milestones. No stretch feature is being declared.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
