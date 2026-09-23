# First collaboration episode observation

Date: 2026-08-26
Status: one episode; not a baseline or global prior

> このepisodeはzero-input ledger実装前にprimaryが手動で再構成した初期記録です。今後、人間へ同じ記録を要求しません。自動取得できないsemantic fieldは`unknown`として扱います。

## Goal

Grok 4.6とClaude Opus 5へ同じrepository contextとreview briefを渡し、multi-agent collaborationの思想、adaptive selection、interaction、recurring governance、repository toolingを独立に検討させる。

## Plan-derived fields

| field | observation |
|---|---|
| expected mechanism | option / assumption coverage、independent review、error decorrelation |
| binding constraint before run | wall-clock、provider tool contract、後段のhuman synthesis |
| relation | consult |
| lifecycle | one-shotを意図したが、artifact単位のbounded continuationへadaptiveに分割 |
| participants | 2。ユーザーがGrokとOpus 5を明示した結果で、推奨人数ではない |
| independence | separate worktrees、common base / brief、mutual output hidden |
| authority | primaryがbrief、budget、recovery、persistence、synthesis、integrationを所有 |
| side effects | provider専用temp docsのみ。source / schema / external publicationなし |

## Outcome

- Grok 4.6: 5 Markdown documents recovered.
- Claude Opus 5: 5 Markdown documents recovered.
- 10 documents were committed as raw independent review evidence.
- Both reviews rejected global fixed participant / round / variant counts.
- Both reviews deferred scheduler and compete automation until evidence gates are met.

## Operational evidence

### Grok

Initial headless runs completed analysis but did not persist files because the filesystem tool contract used by the invocation was unsuitable. Repeating the same write attempt did not help. A schema-constrained result was then requested, and the primary persisted the five returned Markdown fields.

Meaning: provider adapter / tool contract was the binding constraint, not intellectual output quality. Structured result plus primary-owned persistence is a useful fallback. It is not evidence that all Grok tasks should use this path.

### Opus 5

The initial five-document request reached its wall-time cost cap after producing three documents. A smaller continuation produced the fourth. The fifth was recovered as a bounded structured result.

Meaning: large compound deliverables can exceed one-run operational budgets even when useful partial artifacts exist. Retry should preserve artifacts and shrink remaining scope rather than restart everything. It is not evidence for a universal document count or duration.

## Human review

All ten documents were read by the primary before synthesis. Human review / synthesis remained the critical path after provider generation. Exact human minutes were not captured, so this episode cannot support a quantitative comparison with solo work.

## Stop reason

Stopped after:

- every required provider artifact existed,
- primary completed full review,
- strong agreement and material disagreements were identified,
- a revised model and staged tooling decision could be written,
- further provider exchange was not expected to change the immediate R0 decision.

## What this episode does not prove

- that two providers are optimal,
- that cross-provider consultation beats one provider,
- that five documents are an appropriate granularity,
- that any wall-time or effort setting should become a default,
- that the proposed modes, metrics, or scheduler guards improve production development,
- that the provider opinions are factually correct without project experiments.

## Follow-up

Use normal project tasks to test whether the revised brief is light enough to use and whether collaboration changes accepted outcomes after human review cost is included. Record only fields that are actually used in later decisions.
