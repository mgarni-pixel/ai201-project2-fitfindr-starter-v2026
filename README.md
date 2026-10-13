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
> All three tools are implemented. Search now runs through the local MCP server.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

## Unit 4: Testing continuation

This new repository preserves the complete Part 1 history from
[mgarni-pixel/ai201-project2-fitfindr-starter-v2026](https://github.com/mgarni-pixel/ai201-project2-fitfindr-starter-v2026),
through `71e616a2122be08e3e291dcf2c7abb7507ba9e11`. The original criteria were
committed at `73d22e2e521616fd5d3ed37285538ab7b6d7e70b` and remain unchanged.
A new repository was explicitly requested; the course asks for the original
URL, so this new destination is a submission deviation. The original repository
has not been changed. The **How I Used AI** section is reserved for the user's
Unit 4 update and retains its previous text.

**Milestone 1:** `search_listings` is the only MCP tool. `agent.py::run_agent`
uses `mcp_client.call_tool`; the two Gemini tools remain direct calls.
The real stdio tests compare entire returned dictionaries with the original
function for normal, empty, price-filtered and size-filtered searches.
No search results or ranking changed across the boundary.

Evidence: [registered schema](results/unit4_mcp_schema.txt),
[setup check](results/unit4_setup.txt),
[25 passing tests](results/unit4_milestone1_tests.txt), and
[real end-to-end query](results/unit4_milestone1_query.txt).
Environment: Python 3.13.14, google-genai 1.75.0, mcp 1.30.0; unchanged
requirements bounds, `gemini-3.5-flash-lite`, temperature 0.9.

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

**Milestone 3.** Command: `python run_eval.py --label before`. Five independent
attempts per criterion (25 scenario runs), cache off, unchanged original targets.
The run made 25 real Gemini requests: 10 for criterion 1, 10 for criterion 3,
5 for criterion 4, and none for the deterministic criteria 2 and 5.
Usage: 14,154 prompt tokens and 3,373 output tokens. No scored attempt was discarded.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item reaches suggest_outfit unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Caption grounded in item and outfit | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Nonempty search respects the inclusive $20 ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Rules were fixed in [UNIT4_SCORING.md](docs/UNIT4_SCORING.md) before the run.
Criterion 4 was read against the actual item and outfit, with supporting quotes
saved in [the grounding review](results/unit4_before_grounding.json).
The other four criteria are checked against full sessions and actual call snapshots.

[Raw run log](results/run_2026-10-13_032517_UTC_before.md) · [complete records](results/run_2026-10-13_032517_UTC_before.json) ·
[console and request counts](results/unit4_before_console.txt) · [32 passing tests](results/unit4_milestone3_tests.txt).

### Real output from one try per criterion

These are actual values from try 1 of each scenario, captured by
`run_eval.py::run_once`. No text was invented to fill the table.

**Criterion 1 — `agent.py::run_agent → tools.py::create_fit_card`**

```text
Score! Found this Y2K baby tee featuring a cute pink and purple butterfly graphic on Depop for $18. It has that classic fitted crop length and an early 2000s vibe. I'm styling it with baggy dark-wash jeans for an easy streetwear look.
```

**Criterion 2 — `agent.py::run_agent (empty-search branch)`**

```text
No matching listings. Try broader keywords, a different size, or a higher price ceiling.
```

**Criterion 3 — `agent.py::run_agent → tools.py::suggest_outfit (actual argument)`**

```text
selected_item = {"id": "lst_007", "title": "Denim Jacket — Light Wash, Cropped", "description": "Cropped denim jacket in a light wash. Great structured shoulders. Blank canvas — no patches or pins but would be perfect to customize.", "category": "outerwear", "style_tags": ["denim", "vintage", "classic", "streetwear"], "size": "S", "condition": "excellent", "price": 42.0, "colors": ["light blue"], "brand": "Wrangler", "platform": "poshmark"}
suggest_outfit.new_item = {"id": "lst_007", "title": "Denim Jacket — Light Wash, Cropped", "description": "Cropped denim jacket in a light wash. Great structured shoulders. Blank canvas — no patches or pins but would be perfect to customize.", "category": "outerwear", "style_tags": ["denim", "vintage", "classic", "streetwear"], "size": "S", "condition": "excellent", "price": 42.0, "colors": ["light blue"], "brand": "Wrangler", "platform": "poshmark"}
```

**Criterion 4 — `tools.py::create_fit_card (fixed item/outfit input)`**

```text
Item: Y2K Baby Tee — Butterfly Print
Outfit: Wear the baby tee with baggy straight-leg dark wash jeans and chunky white sneakers; add the black crossbody bag.
Caption: Scored this early 2000s white, pink, and purple baby tee on Depop for $18, and it features the cutest butterfly graphic. It gives off major retro vibes in excellent condition. Pair it with baggy straight-leg dark wash jeans and chunky sneakers for an easy, nostalgic fit.
```

**Criterion 5 — `mcp_server.py::search_listings → tools.py::search_listings`**

```text
[
  {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_012",
    "title": "Oversized Crewneck Sweatshirt — Vintage Navy",
    "description": "Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "basics",
      "oversized",
      "classic"
    ],
    "size": "XL (fits oversized)",
    "condition": "good",
    "price": 20.0,
    "colors": [
      "navy"
    ],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_014",
    "title": "Leather Belt — Brown, Braided",
    "description": "Genuine leather braided belt. Adjustable, multiple holes. Classic Western buckle. Can be dressed up or down.",
    "category": "accessories",
    "style_tags": [
      "vintage",
      "western",
      "classic",
      "earth tones"
    ],
    "size": "One Size (adjustable)",
    "condition": "excellent",
    "price": 12.0,
    "colors": [
      "brown"
    ],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_020",
    "title": "Henley Long Sleeve — Washed Burgundy",
    "description": "Soft washed henley in a rich burgundy. Three-button placket. Slightly shrunken/cropped fit. 100% cotton.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "basics",
      "earth tones",
      "classic"
    ],
    "size": "M",
    "condition": "excellent",
    "price": 16.0,
    "colors": [
      "burgundy",
      "wine"
    ],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_024",
    "title": "Vintage Polo Shirt — Forest Green",
    "description": "Classic polo in forest green. Short sleeve, ribbed collar. Slightly boxy. The kind of piece that goes with everything.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "preppy",
      "classic",
      "earth tones"
    ],
    "size": "M",
    "condition": "good",
    "price": 18.0,
    "colors": [
      "green",
      "forest green"
    ],
    "brand": "Ralph Lauren",
    "platform": "thredUp"
  },
  {
    "id": "lst_033",
    "title": "Vintage Band Tee — Faded Grey",
    "description": "Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "grunge",
      "band tee",
      "graphic tee",
      "streetwear"
    ],
    "size": "L",
    "condition": "fair",
    "price": 19.0,
    "colors": [
      "grey",
      "charcoal"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_034",
    "title": "Bucket Hat — Reversible, Brown Plaid",
    "description": "Reversible bucket hat — plaid on one side, solid tan on the other. Unstructured brim. One size fits most.",
    "category": "accessories",
    "style_tags": [
      "90s",
      "streetwear",
      "vintage",
      "accessories"
    ],
    "size": "One Size",
    "condition": "excellent",
    "price": 14.0,
    "colors": [
      "brown",
      "tan",
      "plaid"
    ],
    "brand": null,
    "platform": "thredUp"
  }
]
```

---

## Verdicts and Diagnoses

**Milestone 4.** The original criteria all met their targets. Nothing was
redefined or lowered after seeing the results.

| # | Original target | Before verdict | How the decision was made |
|---|---|---|---|
| 1 | 4 of 5 | MET (5/5) | Every actual trace calls MCP search, outfit, then card; each session returns a nonempty card without an error. |
| 2 | 5 of 5 | MET (5/5) | Every impossible search returns no listings and the actionable message; none invokes either model tool. |
| 3 | 5 of 5 | MET (5/5) | All five complete selected-item dictionaries equal the actual `new_item` input at `suggest_outfit`, including the ID. |
| 4 | 4 of 5 | MET (5/5) | Each caption identifies the baby tee, describes an accurate butterfly/crop/color detail, and recommends jeans or sneakers from the fixed outfit. Supporting phrases are in the grounding review. |
| 5 | 5 of 5 | MET (5/5) | All five MCP calls use `vintage`, no size filter and max_price 20; each returns a nonempty list with no price above 20. |

**Diagnosis of the observed defect.** No original criterion missed, but criterion
1, try 3 returned this caption from `tools.py::create_fit_card`:

```text
Scored this early 2000s baby tee featuring a sweet pink-and-purple butterfly graphic for just $18 on Depop! It has a fitted, cropped length that looks so good balanced with baggy dark-wash jeans. Such an easy y2k find for $18 on Depop.
```

The error occurs in the **model output at the final card step**. Search selected
the correct $18 Depop item and the session passed that item through unchanged.
The model repeats both facts in its last sentence even though the prompt says
"once each." The tool accepts any nonempty response; its prompt has no explicit
final check for this repetition. That is a prompt-adherence defect in an existing
Tool Inventory promise, not a failure of criterion 1's completion condition.

**Why all passes are limited.** Criteria 1 and 3 each use one matching query;
criterion 4 uses one tee and one fixed outfit. These targets check basic plumbing
and grounding, but miss repeated commercial details. A future stricter criterion
4 would also require the correct price and platform exactly once and test several
items. That proposed future rule has **not** replaced the original criterion.

**Counter-check of the verdicts.** A repeated price could make a caption worse,
but cannot turn criterion 1 into a failure: that original criterion asks whether
a card returns. Criterion 4 also does not require varied wording, exact sentence
count, price or platform. Adding those requirements now would score a different
test. Conversely, an empty search always returning `[]` cannot sneak through
criterion 5 because it requires a nonempty result.

**One improvement selected before the after-run.** Add a final self-check to
`create_fit_card`'s existing prompt: keep the price and platform exactly once,
including any closing sentence. Leave the model, temperature, adapter, data,
search, session, scenarios and original scoring rules unchanged.

**Supplemental measurement, separate from graded criteria.** Across the 15 actual
captions from criteria 1, 3 and 4, count a success only when there is exactly one
currency amount equal to the selected item's price and exactly one
case-insensitive occurrence of its platform. `tests/score_unit4.py::price_platform_once`
implements this same check for both logs. Before: **14/15**; the single failure
is criterion 1, try 3 above. This diagnostic never changes a five-criterion verdict.

---

## Loop Trace

**Milestone 2.** These are actual uncached CLI runs. Each tool input and output is
recorded in full, rather than the starter's truncated summaries. Trace snapshots
also preserve dictionaries for the state criterion; `--trace` controls printing.

**Happy path** — `agent.py::run_agent`, formatted by `trace.py::step`:

```text
Command: python app.py ask 'vintage graphic tee under $30, size M' '--trace'
AI201_CACHE=0; real CLI, no tool doubles.
[1] parse_query
      in:  "vintage graphic tee under $30, size M"
      out: {"description": "vintage graphic tee", "max_price": 30.0, "size": "M"}
[2] search_listings (via MCP)
      in:  {"description": "vintage graphic tee", "max_price": 30.0, "size": "M"}
      out: [{"brand": null, "category": "tops", "colors": ["white", "pink", "purple"], "condition": "excellent", "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.", "id": "lst_002", "platform": "depop", "price": 18.0, "size": "S/M", "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"], "title": "Y2K Baby Tee — Butterfly Print"}, {"brand": null, "category": "tops", "colors": ["black"], "condition": "excellent", "description": "Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.", "id": "lst_017", "platform": "depop", "price": 15.0, "size": "S/M", "style_tags": ["y2k", "grunge", "goth", "layering"], "title": "Mesh Long-Sleeve Top — Black"}, {"brand": null, "category": "bottoms", "colors": ["ivory", "dusty pink", "green"], "condition": "good", "description": "Delicate 90s slip dress in a muted floral print. Midi length, adjustable straps. Light snag on the side seam — not visible when worn.", "id": "lst_013", "platform": "depop", "price": 30.0, "size": "M", "style_tags": ["90s", "vintage", "feminine", "floral", "cottagecore"], "title": "90s Silk Slip Dress — Floral, Midi Length"}, {"brand": null, "category": "tops", "colors": ["burgundy", "wine"], "condition": "excellent", "description": "Soft washed henley in a rich burgundy. Three-button placket. Slightly shrunken/cropped fit. 100% cotton.", "id": "lst_020", "platform": "thredUp", "price": 16.0, "size": "M", "style_tags": ["vintage", "basics", "earth tones", "classic"], "title": "Henley Long Sleeve — Washed Burgundy"}, {"brand": "Ralph Lauren", "category": "tops", "colors": ["green", "forest green"], "condition": "good", "description": "Classic polo in forest green. Short sleeve, ribbed collar. Slightly boxy. The kind of piece that goes with everything.", "id": "lst_024", "platform": "thredUp", "price": 18.0, "size": "M", "style_tags": ["vintage", "preppy", "classic", "earth tones"], "title": "Vintage Polo Shirt — Forest Green"}, {"brand": null, "category": "tops", "colors": ["sage", "green"], "condition": "excellent", "description": "Loose silk (feel) button-down in sage green. Long sleeve, can be worn open as a layer or fully buttoned. Very flowy.", "id": "lst_029", "platform": "depop", "price": 28.0, "size": "M", "style_tags": ["vintage", "minimal", "earth tones", "cottagecore"], "title": "Silk Button-Down — Sage Green"}, {"brand": null, "category": "tops", "colors": ["brown", "cream", "tan"], "condition": "good", "description": "Classic argyle knit vest in brown and cream. Fits medium. V-neck. Ideal for the dark academia or preppy vintage aesthetic.", "id": "lst_030", "platform": "thredUp", "price": 25.0, "size": "M", "style_tags": ["vintage", "preppy", "knitwear", "dark academia", "earth tones"], "title": "Vintage Knit Vest — Argyle Brown/Cream"}, {"brand": null, "category": "outerwear", "colors": ["medium blue"], "condition": "good", "description": "Denim vest with silver stud detailing along the collar and pockets. Classic rock-inspired customization. Fits like a medium.", "id": "lst_038", "platform": "depop", "price": 27.0, "size": "M", "style_tags": ["grunge", "vintage", "denim", "customized", "rock"], "title": "Denim Vest — Medium Wash, Studded"}]
[3] select_item
      out: {"brand": null, "category": "tops", "colors": ["white", "pink", "purple"], "condition": "excellent", "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.", "id": "lst_002", "platform": "depop", "price": 18.0, "size": "S/M", "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"], "title": "Y2K Baby Tee — Butterfly Print"}
[4] suggest_outfit
      in:  {"new_item": {"brand": null, "category": "tops", "colors": ["white", "pink", "purple"], "condition": "excellent", "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.", "id": "lst_002", "platform": "depop", "price": 18.0, "size": "S/M", "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"], "title": "Y2K Baby Tee — Butterfly Print"}, "wardrobe": {"items": [{"category": "bottoms", "colors": ["dark blue", "indigo"], "id": "w_001", "name": "Baggy straight-leg jeans, dark wash", "notes": "High-waisted, sits above the hip", "style_tags": ["denim", "streetwear", "baggy"]}, {"category": "bottoms", "colors": ["khaki", "tan"], "id": "w_002", "name": "Wide-leg khaki trousers", "notes": null, "style_tags": ["earth tones", "minimal", "wide-leg"]}, {"category": "tops", "colors": ["white"], "id": "w_003", "name": "White ribbed tank top", "notes": "Goes with everything", "style_tags": ["basics", "minimal", "fitted"]}, {"category": "tops", "colors": ["grey", "charcoal"], "id": "w_004", "name": "Oversized grey crewneck sweatshirt", "notes": "Really oversized — drops below the hip", "style_tags": ["oversized", "basics", "cozy"]}, {"category": "tops", "colors": ["black"], "id": "w_005", "name": "Black cropped zip hoodie", "notes": null, "style_tags": ["athletic", "streetwear", "cropped"]}, {"category": "outerwear", "colors": ["black"], "id": "w_006", "name": "Vintage black denim jacket", "notes": "Slightly cropped", "style_tags": ["denim", "vintage", "classic"]}, {"category": "shoes", "colors": ["white"], "id": "w_007", "name": "Chunky white sneakers", "notes": null, "style_tags": ["sneakers", "chunky", "streetwear"]}, {"category": "shoes", "colors": ["black"], "id": "w_008", "name": "Black combat boots", "notes": "Lace-up, mid-ankle height", "style_tags": ["boots", "grunge", "classic"]}, {"category": "accessories", "colors": ["brown"], "id": "w_009", "name": "Brown leather belt", "notes": null, "style_tags": ["classic", "earth tones", "accessories"]}, {"category": "accessories", "colors": ["black"], "id": "w_010", "name": "Black crossbody bag", "notes": null, "style_tags": ["minimal", "accessories", "everyday"]}]}}
      out: "**Outfit 1: Y2K Streetwear**\n*   **New Item:** Y2K Baby Tee — Butterfly Print\n*   **Owned Pieces:** Baggy straight-leg jeans, dark wash (w_001), Vintage black denim jacket (w_006), Chunky white sneakers (w_007), Black crossbody bag (w_010)\n*   **Why it works:** The fitted, cropped cut of the baby tee balances the volume of the baggy dark wash jeans. Layering the slightly cropped vintage black denim jacket keeps the silhouette proportioned, while the chunky white sneakers and black crossbody bag lean into the Y2K streetwear aesthetic.\n\n**Outfit 2: Casual Contrast**\n*   **New Item:** Y2K Baby Tee — Butterfly Print\n*   **Owned Pieces:** Wide-leg khaki trousers (w_002), Black cropped zip hoodie (w_005), Chunky white sneakers (w_007)\n*   **Why it works:** Pairing the feminine, graphic-heavy baby tee with wide-leg khaki trousers creates an effortless mix of casual and polished styles. Wearing the black cropped zip hoodie unzipped over the tee lets the white, pink, and purple butterfly print pop against the earth tones."
[5] create_fit_card
      in:  {"new_item": {"brand": null, "category": "tops", "colors": ["white", "pink", "purple"], "condition": "excellent", "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.", "id": "lst_002", "platform": "depop", "price": 18.0, "size": "S/M", "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"], "title": "Y2K Baby Tee — Butterfly Print"}, "outfit": "**Outfit 1: Y2K Streetwear**\n*   **New Item:** Y2K Baby Tee — Butterfly Print\n*   **Owned Pieces:** Baggy straight-leg jeans, dark wash (w_001), Vintage black denim jacket (w_006), Chunky white sneakers (w_007), Black crossbody bag (w_010)\n*   **Why it works:** The fitted, cropped cut of the baby tee balances the volume of the baggy dark wash jeans. Layering the slightly cropped vintage black denim jacket keeps the silhouette proportioned, while the chunky white sneakers and black crossbody bag lean into the Y2K streetwear aesthetic.\n\n**Outfit 2: Casual Contrast**\n*   **New Item:** Y2K Baby Tee — Butterfly Print\n*   **Owned Pieces:** Wide-leg khaki trousers (w_002), Black cropped zip hoodie (w_005), Chunky white sneakers (w_007)\n*   **Why it works:** Pairing the feminine, graphic-heavy baby tee with wide-leg khaki trousers creates an effortless mix of casual and polished styles. Wearing the black cropped zip hoodie unzipped over the tee lets the white, pink, and purple butterfly print pop against the earth tones."}
      out: "Score this early 2000s white, pink, and purple butterfly graphic baby tee for just $18 on Depop! It has such a nostalgic Y2K vibe in excellent condition. Wear it with baggy dark wash jeans and chunky white sneakers for an effortless streetwear look."

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
*   **New Item:** Y2K Baby Tee — Butterfly Print
*   **Owned Pieces:** Baggy straight-leg jeans, dark wash (w_001), Vintage black denim jacket (w_006), Chunky white sneakers (w_007), Black crossbody bag (w_010)
*   **Why it works:** The fitted, cropped cut of the baby tee balances the volume of the baggy dark wash jeans. Layering the slightly cropped vintage black denim jacket keeps the silhouette proportioned, while the chunky white sneakers and black crossbody bag lean into the Y2K streetwear aesthetic.

**Outfit 2: Casual Contrast**
*   **New Item:** Y2K Baby Tee — Butterfly Print
*   **Owned Pieces:** Wide-leg khaki trousers (w_002), Black cropped zip hoodie (w_005), Chunky white sneakers (w_007)
*   **Why it works:** Pairing the feminine, graphic-heavy baby tee with wide-leg khaki trousers creates an effortless mix of casual and polished styles. Wearing the black cropped zip hoodie unzipped over the tee lets the white, pink, and purple butterfly print pop against the earth tones.

  Fit card: Score this early 2000s white, pink, and purple butterfly graphic baby tee for just $18 on Depop! It has such a nostalgic Y2K vibe in excellent condition. Wear it with baggy dark wash jeans and chunky white sneakers for an effortless streetwear look.

2 model calls this session, 1309 prompt + 324 output tokens
```

**Empty search** — the shorter trace ends before `suggest_outfit`:

```text
Command: python app.py ask 'designer ballgown size XXS under $5' '--trace'
AI201_CACHE=0; real CLI, no tool doubles.
[1] parse_query
      in:  "designer ballgown size XXS under $5"
      out: {"description": "designer ballgown", "max_price": 5.0, "size": "XXS"}
[2] search_listings (via MCP)
      in:  {"description": "designer ballgown", "max_price": 5.0, "size": "XXS"}
      out: []
[3] branch
      out: "No matching listings. Try broader keywords, a different size, or a higher price ceiling."
      →    empty search; stop before tool 2

  No matching listings. Try broader keywords, a different size, or a higher price ceiling.

0 model calls this session
```

**On the MCP move:** Search now crosses the local stdio protocol through
`mcp_client.call_tool`. The real round-trip tests preserved complete listing
values, order and empty results. Only search is registered on the server.

### Deliberate failures

The committed runner `python -m tests.unit4_failure_runs` triggers each failure
in a separate process with caching off. The invalid-key run changes one character
only in that child's environment; it verifies that the saved `.env` is unchanged.
No credentials are printed or committed. Real CLI failures are distinct from the
unit-test doubles in `tests/test_failures.py`.

| Trigger | Actual message / response | What a user can try |
|---|---|---|
| Impossible query | No matching listings. Try broader keywords, a different size, or a higher price ceiling. | Change keywords, size or budget. |
| Empty wardrobe | Your wardrobe is empty. Showing general styling ideas; retry without --empty-wardrobe to use the example wardrobe. | Remove the flag; general styling advice still returns. |
| Invalid model key | The model is unavailable at suggest_outfit. Check GEMINI_API_KEY in your .env file and your internet connection, then retry. If both are correct, wait a minute and try again. | Check the key/connection, then retry. |

Empty-wardrobe advice excerpt (actual output from `tools.py::suggest_outfit`):

```text
Here are two ways to style your Wrangler cropped denim jacket:

**1. Casual Streetwear**
*   **The Look:** Pair the jacket with high-waisted black or dark wash wide-leg cargo pants and a fitted white ribbed tank top.
*   **Footwear:** Retro sneakers (like Adidas Sambas).
*   **Accessories:** A black crossbody bag and silver hoop earrings.

**2. Off-Duty Denim (Double Denim)**
*   **The Look:** Layer the jacket over a basic grey crewneck t-shirt and pair with contrast-wash straight-leg jeans (darker blue or ecru to avoid matching shades too closely).
*   **Footwear:** Classic leather loafers or ankle boots.
*   **Accessories:** A simple leather belt and minimalist watch.
```

Full evidence: [empty wardrobe](results/unit4_empty_wardrobe.txt),
[invalid key](results/unit4_model_unavailable.txt),
[full trace](results/unit4_full_trace.txt), and
[28 passing tests](results/unit4_milestone2_tests.txt).
Review of the three messages finds a concrete next action in each; this is an
Astra review, not a claimed classroom or Claude conversation.

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
