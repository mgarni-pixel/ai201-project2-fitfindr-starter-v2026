# Acceptance criteria: FitFindr

Criteria 1 and 2 are supplied by the course. Criteria 3 through 5 and the reasons
below were drafted by AI at the student's request. They are not independently
student-authored and are pending student review and rework. This record does
not establish instructor approval or an extension. The criteria are committed
before tool implementation, tool tests, and agent acceptance results.

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card in at least 4 of 5 tries.

**Why this target:** This checks that `search_listings`, `suggest_outfit`, and
`create_fit_card` work together. A 4/5 target allows one failure from the
model-backed steps while still requiring reliable completion; 5/5 would demand
greater consistency from those steps.

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change in 5 of 5 tries.

**Why this target:** The empty-results branch in `run_agent` is deterministic.
All five attempts must pass because calling the next tool without an item or
leaving the user without a next step is avoidable; a lower rate would accept a
branch bug, and a stricter test would need more varied no-match inputs.

## 3. The selected listing reaches the next tool unchanged

Given a query with matching listings, inspect `selected_item` in the returned
session and the `new_item` argument passed to `suggest_outfit`. Both must contain
the same listing dictionary, including the same `id`, without asking the user
to enter the item again, in 5 of 5 tries.

**Why this target:** This checks that `run_agent` carries the selected item
through the session correctly. Passing data between steps is deterministic, so
a lower target would accept an avoidable state-handling bug; broader input
coverage would be a stricter test than these five attempts.

## 4. The caption is grounded in the item and outfit

Given an item and a nonempty outfit suggestion, `create_fit_card` returns a
caption that identifies the item by its type and at least one accurate
distinguishing detail, and includes at least one specific styling suggestion
from the supplied outfit, in at least 4 of 5 tries. The wording may vary.

**Why this target:** This checks whether `create_fit_card` produces useful,
item-specific text without requiring an exact sentence match. A 4/5 target
allows one weak model response; requiring 5/5 would demand greater consistency.

## 5. Search respects the inclusive price ceiling

Call `search_listings` with description `vintage`, no size filter, and
`max_price` of 20. In 5 of 5 tries, it must return at least one listing and every
returned listing's price must be 20 or less.

**Why this target:** The supplied data contains vintage items both below and
above this limit, so this checks that `search_listings` enforces the budget and
cannot pass by always returning `[]`. The filter is deterministic, so all five
attempts should pass; allowing an over-budget result defeats the limit, while
checking more price ceilings would make the test stricter.

---

For Unit 4, retain these original targets. If a criterion cannot be measured,
add a dated revision and its reason beneath the original instead of deleting
it. Do not lower a target just because a run missed it. No Unit 4 results have
been recorded here.
