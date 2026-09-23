# F10-L-PYBASH-001: execution and analysis plan

## Finite execution block

- C0/fresh/automatic-permissionでCodex Sol、Grok 4.6、再認証済みClaudeのprovider seriesを分離して観測する。
- 各providerでnormal-depth候補のmediumとdeep候補のxhighを同一case revisionへ実行し、順序を観測blockごとに反転する。
- unsupported/rejected settingは短いcapability probeで確定し、task duration sampleへ混ぜない。
- rubricがquality差を識別した後、Codexはhigh/max/ultra、GrokとClaudeはadvertisedかつapplied確認可能なhigh/max相当も同一identity blockへ追加する。

requested effortはapplied effortの証拠ではない。Codex、Claude、Grokのsetting namespaceを分離し、providerが確認できた値だけをapplied seriesへ置く。`xhigh`、`max`、Codexの`ultra`はtaskが深い場合の候補から除外せず、unsupportedはtask failureでなくcapability evidenceとして残す。

## Collaboration eligibility

- C0 baseline is required.
- CP can separate instrumentation/accounting, width experiments, and causal counterfactuals; primary owns one bottleneck model.
- CC compares independent diagnoses from the same raw ledgers.
- CV recomputes metrics and runs counterfactual scenarios.
- CS stages instrumentation, experiments, diagnosis, and verification.

agent数やdialogue round数はdefault化しない。caseのdecomposabilityと未解決claimに適合する点だけをfinite paired blockとして追加し、exact participant count、dispatch、worker terminal、synthesisを計測する。

## Timing and caps

- case timeout safety cap: 125 minutes
- provider start前にcredential freshness、runtime identity、sandbox、network policyを確認する。
- T0/T1/T6、online validation V0/V1、offline scoring S0/S1を分離する。
- timeout、rate limit、provider rejection、harness failureを成功sampleから消さない。
- orderはblock間でrotateし、fresh contextを基本にする。warm/cache treatmentは別seriesにする。

## Interpretation questions

- Which stage of the diagnostic task dominates agent time?
- Does sharding experiments shorten wall time or consume more simulator resources?
- Which depth avoids wall/aggregate/critical-path conflation?
- How much verifier work changes causal attribution?

単一runはraw observationでありtypical bandではない。同一case repeatとisomorphic variantは別々に集計し、family promotion条件を満たすまで`single-observation`または`same-case-repeat`に留める。
