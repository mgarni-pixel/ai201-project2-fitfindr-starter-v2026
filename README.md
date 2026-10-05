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

FitFindr takes a clothing request like "vintage graphic tee under $30, size M" and searches a local mock catalog of thrift listings. The code pulls the size, price, and description out of the query, then filters listings on price and size and ranks the rest by how many words match. If nothing matches, it says so and stops. If something matches, it picks the top result and asks Gemini for outfit advice using that listing and your wardrobe, then turns the advice into a text caption.


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
sizes). Slash-separated numeric or waist/inseam constraints are preserved in full.
The matched clauses and common request filler are removed from the
remaining description. Missing filters become None. The parsed values go into
`session["parsed"]`; parsing does not call the model.

**What moves through the session:** Start a fresh session for every query;
store `query` and `wardrobe`, then `parsed`, `search_results`, `selected_item`,
`outfit_suggestion`, and `fit_card`. Each next tool reads its actual inputs back
from that session. The no-match path leaves the three later result fields None.
A four-stage planning loop (`parse`, `search`, `suggest`, `card`) checks
`trace.check_iterations()` on each iteration and retains `config.MAX_ITERATIONS`.

The contracts were committed at Milestone 2 before implementation. The parser
and four-stage loop are now implemented as described. No stretch feature has
been declared. Final student review, What This Does, and How I Used AI remain
for Milestone 6.

---

## Sample Run

**One full query**

Actual Milestone 5 happy-path output, using the supplied example wardrobe:

```text
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
*   **New Item:** Y2K Baby Tee — Butterfly Print
*   **Owned Pieces:** Baggy straight-leg jeans, dark wash (w_001), Vintage black denim jacket (w_006), Chunky white sneakers (w_007), Black crossbody bag (w_010)
*   **Why it works:** The fitted, cropped cut of the baby tee balances the voluminous silhouette of the high-waisted baggy jeans. Adding the slightly cropped black denim jacket and chunky white sneakers leans fully into the early 2000s streetwear aesthetic.

**Outfit 2: Casual Contrast**
*   **New Item:** Y2K Baby Tee — Butterfly Print
*   **Owned Pieces:** Wide-leg khaki trousers (w_002), Brown leather belt (w_009), Black combat boots (w_008)
*   **Why it works:** Pairing the feminine, pink-and-purple butterfly graphic tee with utility-inspired wide-leg khaki trousers creates a balanced high-low mix of Y2K and minimal earth tones. The brown belt and black combat boots ground the lighter colors of the top and bottoms.

  Fit card: Scored this adorable Y2K baby tee featuring a colorful pink and purple butterfly graphic on Depop for just $18. It has that classic fitted crop length and an effortless early 2000s vibe. I love styling it with baggy straight-leg jeans and chunky white sneakers for a total streetwear look.

2 model calls this session, 1304 prompt + 326 output tokens
```

The impossible-query branch also ran:

```text
$ python app.py ask 'designer ballgown size XXS under $5'

  No matching listings. Try broader keywords, a different size, or a higher price ceiling.

0 model calls this session
```

Five fresh matching runs with the existing `AI201_CACHE=0` override completed
all three tools and preserved the selected dictionary in the real downstream
arguments. Five no-match attempts made zero suggest/card calls, left the later
fields None, and returned an actionable message. Five budget-filter attempts
returned nonempty results, all at or below $20. AI-assisted inspection of the saved item/outfit/caption triples found all five
captions met criterion 4, with 3, 4, 3, 3, and 3 sentences and correct price and
platform once each. This coverage uses one item (`lst_002`) and one matching
query; student review and broader testing remain pending.

Full state/input evidence: [results/milestone5_trials.json](results/milestone5_trials.json).
Commands/check output: [results/milestone5_agent.txt](results/milestone5_agent.txt).


**The three tools, tested one at a time**

Actual terminal commands and output from Milestone 4, before wiring `run_agent`:

### Search tool

```text
$ python -c 'from tools import search_listings; print(search_listings("graphic tee", max_price=30))'
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

### Outfit tool

```text
$ python -c 'from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))'
**Outfit 1: Casual Streetwear**
* **New Item:** Levi's Vintage Levi's 501 Jeans — Medium Wash
* **Owned Pieces:** White ribbed tank top, Chunky white sneakers, Black crossbody bag

**Why it works:** The fitted white ribbed tank balances the straight-leg cut of the Levi's 501s, while the chunky white sneakers and black crossbody bag lean into the jeans' streetwear aesthetic for an effortless, classic casual look.

---

**Outfit 2: Coozy Layered**
* **New Item:** Levi's Vintage Levi's 501 Jeans — Medium Wash
* **Owned Pieces:** Oversized grey crewneck sweatshirt, Black combat boots, Brown leather belt

**Why it works:** Tucking the hem of the oversized grey crewneck into the Levi's 501s creates a balanced proportion. The brown leather belt adds a polished anchor, and the black combat boots give the vintage denim a subtle grunge edge.
```

### Fit-card tool

```text
$ python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card("jeans and white sneakers", load_listings()[0]))'
Scored these vintage Levi's 501s on Depop for just $38! They’ve got the best medium wash with natural knee fading that gives them that effortless streetwear vibe. Style them with white sneakers for an easy, everyday look.
```

### Extra checks and repeated captions

The empty wardrobe produced general styling advice in a live model call. A
blank outfit returned the documented message without calling the model. All
15 deterministic tool checks passed; their model doubles test control flow
and prompt construction, not model quality.

Three calls to `create_fit_card` on the same item and outfit returned identical
text. The adapter reported three cache hits and zero new requests in that
repeat command, with `CACHE_ENABLED=True` and `TEMPERATURE=0.9`. This is expected
building-cache behavior. Genuine variation needs the existing cache override
for evaluation; the cache and pacing implementation have not been changed.

Complete commands and actual outputs, including all three repeated captions:
[results/milestone4_tools.txt](results/milestone4_tools.txt).

---

## How I Used AI

I asked Codex to build the three tools and planning loop and test the implementation. It produced the code, specifications, sample outputs, and five milestone commits. My code review and further revisions are still pending.

I also asked Codex to check that the README included a full query/output and three individual tool tests. It compared those examples with the saved logs and confirmed they were already present. I supplied the four-sentence app description, which Codex inserted without changing my wording.

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
