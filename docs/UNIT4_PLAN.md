# FitFindr Unit 4 milestone plan

Continue Part 1 at `71e616a2122be08e3e291dcf2c7abb7507ba9e11`, preserving all
history and the original `criteria.md`. Work initially went to the requested
new repository, `mgarni-pixel/ai201-project4-fitfindr-testing`. The final submission
uses the original `mgarni-pixel/ai201-project2-fitfindr-starter-v2026` repository
on `codex/unit4-submission`, satisfying the course's same-URL requirement.

## Contract and scope

- Keep the supplied data, Gemini model configuration, adapter, cache and pacing.
- Move only `search_listings(description, size=None, max_price=None)` to the
  existing stdio MCP boundary, preserving its list-of-dictionaries return.
- Retain the local `suggest_outfit` and `create_fit_card` implementations until
  the single evidence-driven improvement in milestone 5.
- Add actionable failure handling and complete step/input/output trace evidence.
- Keep five original criteria and thresholds; five fresh tries per criterion
  before and after one improvement, caching disabled. Never substitute mocks
  for recorded model trials. Test doubles are limited to labeled unit tests.
- Append only the user-approved Unit 4 paragraph to `How I Used AI`, and remove
  the outdated pending-review sentence as requested.
- No stretch features, deployments, changes to other repositories, secret output,
  committed environments/caches or automatic submission. The user authorized
  replacing milestone 6; milestones 1–5 and the entire Part 1 history stay intact.

## Dependency-ordered milestones

1. Register and call the search tool over MCP; compare it with the direct result,
   verify schema and a real end-to-end query, then commit.
2. Trigger empty search, empty wardrobe and model unavailable independently;
   record actionable messages and a complete successful trace, then commit.
3. Map scenarios exactly to original criteria and run five uncached attempts
   each. Save real outputs and the before table, then commit.
4. Apply original targets; diagnose every miss by step and mechanism. If all
   pass, acknowledge limited coverage and identify a stricter future criterion
   without changing current targets. Commit the diagnosis.
5. Make one change justified by the diagnosis. Freeze scenario/scoring definitions
   between runs, repeat all five criteria five times, compare honestly, and commit.
6. Finish remaining-limits and MCP write-up, verify evidence and preserved history,
   then commit and push the milestones with the approved AI-use update.

## Ownership and acceptance

Astra owns implementation, validation, review, commits and delivery, as requested
by the user. Each milestone is validated and committed before the next begins.
Use the supplied setup check, Python unit tests, real MCP checks and relevant live
runs; `git diff --check` at each boundary. A blocked real run is recorded honestly,
never marked complete or replaced by invented evidence.


## Completion record

Milestones 1–5 were validated and committed in dependency order. Milestone 6
finishes the limitations, reproduction instructions and delivery checks. All
original criteria were MET at 5/5 before and after; a separate once-each
price/platform check improved from 14/15 to 15/15 captions. The comparison records
50 scenario trials and 50 actual model requests in total. No stretch feature or
second application improvement was added. The approved AI-use paragraph is
appended; final course submission remains with the user.
