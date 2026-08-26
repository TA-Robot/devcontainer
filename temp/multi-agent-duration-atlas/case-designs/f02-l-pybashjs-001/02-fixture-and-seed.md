# F02-L-PYBASHJS-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `change.diff` | cross-stack review surface | three seeded defects |
| `scripts/provider-wrapper` | environment/event boundary | forwards unbounded payload |
| `bridge/store.py` | redaction and atomic state | redacts before normalization and truncation |
| `extension/world.js` | restart state handling | replays stale transient as active |
| `scripts/cleanup.sh` | resource cleanup | matches prefix without owner marker |
| `tests/` | public happy paths | passing |
| `review.json` | required review | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The wrapper permits multiline oversized event values that bypass pre-normalization redaction, restart resurrects stale `working` state, and cleanup can delete a peer resource with the same prefix. Each has a fixture reproducer; cosmetic CSS and comment changes are distractors.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Build a lifecycle model for input, persistence, restart, render, and cleanup.
2. Reproduce payload/redaction ordering across Bash/Python.
3. Reproduce stale transient after extension restart.
4. Reproduce cleanup prefix collision, rank all findings, and identify shared ownership assumptions.

## Private known-good outline

Three ranked findings include exact fixture reproducers, cross-stack source chains, lifecycle ownership implications, and bounded remediation constraints; no distractor is elevated.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
