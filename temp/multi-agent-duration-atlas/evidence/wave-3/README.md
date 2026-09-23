# Wave 3 evidence disposition

Canonical performance/rejection evidence:

- `grok-f04-l-46-medium-20260827-r01.json`
- `grok-f04-l-46-high-20260827-r01.json`
- `grok-f04-l-46-xhigh-20260827-r01.json`
- `grok-f04-l-46-max-20260827-r03.json`
- `codex-f04-l-sol-medium-20260827-r01.json`
- `codex-f04-l-sol-high-20260827-r01.json`
- `codex-f04-l-sol-xhigh-20260827-r01.json`
- `codex-f04-l-sol-max-20260827-r01.json`
- `codex-f04-l-sol-ultra-20260827-r01.json`

Do not include in a performance or capability population:

- `grok-f04-l-46-max-20260827-r01.json`: instrumentation-invalid; provider rejection was incorrectly represented from pre-run session metadata.
- `grok-f04-l-46-max-20260827-r02`: no record exists; the provider rejected the value, then record finalization exposed a missing failure-class enum.

All accepted canonical rows are one observation per setting. No aggregation or typical band is authorized yet.
