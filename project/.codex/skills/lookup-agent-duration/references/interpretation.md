# Interpreting duration evidence

## Time values

- Report exact milliseconds or a readable conversion derived from them.
- Call one observation a point, not an estimate or band.
- Call a repeated exact-case minimum/maximum an observed case range.
- Use a case-aware summary only when the query output includes it; do not calculate a flat cross-case median yourself.
- Do not emit p95, prediction intervals or family-wide typical values unless a future versioned aggregate explicitly contains a validated method and evidence state for them.

## Quality and censoring

Use `quality-pass-user-result` for successful planning evidence. Show failed and unknown terminal observations beside it rather than deleting them. Keep timeout/cancellation counts visible. Offline evaluator runtime is not user wait.

Do not infer first-artifact latency from final response time. `not-observed`, `not-applicable` and `unknown` are distinct.

## Comparisons

Compare only cells that differ on the dimension the user requested while showing other differing primary fields. State paired status only when the records identify a controlled paired block. Do not label a provider, model, effort, relation or participant count a winner or default.

The atlas is reference evidence. Project-specific routing remains a separate decision using the project's goals, risk, available time and review cost.

## Missing or stale evidence

For no exact match, return `unmeasured` and list only available filter values or adjacent cell identifiers. Never copy an adjacent duration into the answer. Treat a changed model identity, CLI/runtime surface, image or explicit study boundary as a separate series; do not silently present historical evidence as current.
