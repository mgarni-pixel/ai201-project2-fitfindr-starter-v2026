# FitFindr Unit 4 milestone plan

Continue Part 1 at `71e616a2122be08e3e291dcf2c7abb7507ba9e11`, preserving all
history and the original `criteria.md`. The requested new destination is
`mgarni-pixel/ai201-project4-fitfindr-testing`, branch `codex/unit4-testing`.
The course asks for the previous URL; the new destination is a user-requested
exception, not a claim that this submission satisfies the same-URL rule.

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
- Preserve `How I Used AI` exactly. Its Unit 4 update belongs to the user.
- No stretch features, deployments, changes to other repositories, secret output,
  committed environments/caches, rewritten history or automatic submission.

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
   then commit and push the milestones. Leave AI reflection to the user.

## Ownership and acceptance

Astra owns implementation, validation, review, commits and delivery, as requested
by the user. Each milestone is validated and committed before the next begins.
Use the supplied setup check, Python unit tests, real MCP checks and relevant live
runs; `git diff --check` at each boundary. A blocked real run is recorded honestly,
never marked complete or replaced by invented evidence.
