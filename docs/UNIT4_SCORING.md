# Measurement rules fixed before the before-run

Use `criteria.md` unchanged. Run every scenario independently five times with
the cache disabled. Do not share an agent run across criteria. A model response
can repeat even with the cache off; request counts establish fresh attempts.

1. Target **4/5**. Normal query: all three tool names occur in order in the actual
   trace, the session has no error, and a nonempty fit card returns.
2. Target **5/5**. Impossible query: empty search, no invocation of outfit/card,
   and the returned error explicitly names a change the user can make.
3. Target **5/5**. Normal query: compare the entire `selected_item` dictionary
   with the actual `new_item` argument recorded at `suggest_outfit`; also require
   the same ID and no user re-entry. Dictionary equality, not Python identity
   across serialization, is the criterion.
4. Target **4/5**. Call `create_fit_card` directly on the fixed `lst_002` listing
   and nonempty outfit in `scenarios.py`. Read each full response alongside both
   inputs: it must identify a tee/top, include at least one accurate listing
   detail (e.g. butterfly print or fitted/cropped cut), and at least one specific
   styling suggestion from that outfit (e.g. baggy dark wash jeans or chunky
   white sneakers). Record the supporting phrases per try. Price, platform,
   length and varied wording are not extra pass conditions for this criterion.
   The fixed outfit is test input, not a claimed fresh `suggest_outfit` response.
5. Target **5/5**. Call search through MCP with exactly description `vintage`,
   size `None`, max_price `20`; require a nonempty list and every price <=20.

Crashes/missing required outputs fail; do not discard/retry a scored attempt.
Count passes against the original target for MET/MISSED. Grounding is a textual
judgment reviewed by Astra, not an automated semantic-grade claim. Preserve
raw runs as generated; record scores and explanations separately.

The after-run reuses these scenarios and rules unchanged. Any additional
observation is labeled diagnostic and never replaces an original criterion.
