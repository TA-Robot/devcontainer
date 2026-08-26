# Grok 4.6 independent review brief

You are an independent experimental-design reviewer. Do not edit files, do not run live agent/provider experiments, and do not browse the web. Read these local documents completely:

- `temp/multi-agent-duration-atlas/README.md`
- `temp/multi-agent-duration-atlas/01-objective-and-reference-output.md`
- `temp/multi-agent-duration-atlas/02-size-model-and-task-corpus.md`
- `temp/multi-agent-duration-atlas/03-experimental-dimensions.md`
- `temp/multi-agent-duration-atlas/04-measurement-and-data-contract.md`
- `temp/multi-agent-duration-atlas/05-sampling-and-analysis.md`
- `temp/multi-agent-duration-atlas/06-execution-waves-and-safety.md`
- `temp/multi-agent-duration-atlas/07-implementation-roadmap.md`
- `docs/agents/collaboration-observation.md`
- `docs/agents/representative-scenarios.md`

## Objective you must preserve

The product is a concrete empirical duration reference: for a task family, structural S/M/L size, provider/model/reasoning configuration, collaboration shape, context/cache/environment, show observed time-to-first-useful, time-to-accepted-result, worker time, synthesis/validation tail, variance, failure, and evidence maturity.

It must **not** output a global rule choosing solo vs multi-agent or a winning provider. Each target project will combine the reference measurements with its own goals, risk, schedule, and constraints.

Humans should not have to maintain forms, ratings, or stopwatch annotations. The study is finite and manually started, not an unbounded scheduler.

## Review task

Try to falsify the plan's claim of sufficient coverage. Focus especially on whether it adequately separates and measures:

1. exact model identity and mutable aliases;
2. reasoning/effort settings, including unsupported or provider-specific settings;
3. provider/CLI/runtime version and server-side drift;
4. prompt/task-envelope effects and session/context state;
5. task family, structural size, ambiguity, oracle strength, decomposability, language, artifact type, and environment;
6. orchestration topology, participant width, dialogue depth, primary synthesis, validation, and retries;
7. within-run, within-case, between-case, time-window, and environment variance;
8. meaningful concrete minute-range estimates without false precision;
9. first-useful and accepted-result measurement without human input;
10. feasibility, rate-window safety, privacy, leakage, and reproducibility.

Also look for dimensions not listed above. In particular, distinguish variables that must become separate atlas strata from variables that should merely be recorded as covariates, because an exhaustive factorial experiment is impossible.

## Required response, in Japanese Markdown

1. `結論`: whether the plan is ready, conditionally ready, or missing critical foundations.
2. `重大な欠落`: ordered by impact; cite the exact local document/section affected.
3. `Model / effort設計`: a concrete representation and experiment strategy for model, reasoning effort, server drift, and unsupported combinations.
4. `追加すべきdimension`: classify each as primary stratum, blocking factor/covariate, or diagnostic-only.
5. `時間referenceの統計`: how to publish useful minute ranges while sample sizes grow, including censored failures and model updates.
6. `計測不能・識別不能なもの`: what the harness must leave unknown rather than infer.
7. `修正提案`: precise changes to the eight planning documents, with Must / Should / Later.
8. `最小pilot`: not a fixed universal default, but the smallest experiment structure that can expose a broken design before broader measurement.

Do not praise broadly. Prioritize concrete omissions, confounders, and changes. Any suggested count, threshold, or cap must state its role (statistical precision, coverage, safety, or example) and must not be presented as a universal agent/round default.
