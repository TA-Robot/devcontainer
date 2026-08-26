# F10-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `events/reader.py` | ledger I/O | reopens per query |
| `events/decode.py` | JSON decoding | called twice per line |
| `events/cache.py` | summary cache | identity-keyed miss |
| `bench.py` | workload harness | timing only, no component counters |
| `tests/` | correctness | passing |
| `instrumentation.py` | target instrumentation | skeleton |
| `performance.json` | target report | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Three candidates contribute, but under the supplied repeated-query workload the cache-key bug dominates total work; cold one-shot runs instead expose decode/I/O. The report must distinguish workload/cache state rather than name one universal bottleneck.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Add non-invasive counters for opens, bytes, decodes, cache hit/miss, and phase time.
2. Run cold one-shot and warm repeated-query blocks in rotated order.
3. Compare candidate contributions and validate counter consistency.
4. Report conditional bottlenecks, distributions, raw data, and optimization experiments.

## Private known-good outline

Non-invasive counters show cache miss/hit, open/bytes, and decode calls; rotated cold/warm blocks reveal cache-key dominance in repeated queries and secondary one-shot costs, with raw observations and output equivalence.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
