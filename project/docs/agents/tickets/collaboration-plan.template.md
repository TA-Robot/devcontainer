# Collaboration plan: <<short-name>>

## Goal

- decision / artifact: `<<what this collaboration must decide or produce>>`
- why multi-agent: `<<specific expected gain over solo work>>`
- definition of done: `<<observable completion condition>>`

## Mode and participants

- mode: `<<solo | dispatch | fanout | panel | critique | deliberation | variants | maker-checker | red-team | pipeline | sentinel | event-triggered>>`
- primary / synthesis owner: `<<owner>>`
- integration / external side-effect owner: `<<owner>>`
- participants:
  - role: `<<role>>`
    perspective / bounded task: `<<assignment>>`
    expected output: `<<artifact or advice result>>`
    stop condition: `<<stop>>`

## Shared input and independence

- shared facts / context paths: `<<facts and project-relative paths>>`
- independence: `<<first-round-blind | shared-context | sequential-handoff>>`
- artifact flow: `<<who sends what to whom>>`
- claims / decisions that require evidence: `<<IDs or list>>`

## Execution boundary

- lane: `<<read | write | isolated>>`
- permission profile: `<<safe | trusted-fast | isolated-autonomous>>`
- base SHA: `<<full immutable SHA or not-applicable for read-only consultation>>`
- workspaces / allowed paths: `<<job IDs and paths>>`

## Evaluation

- acceptance: `<<commands, files, manual checks>>`
- comparison rubric: `<<correctness, maintainability, performance, risk, migration cost>>`
- disconfirming evidence / tests: `<<what could overturn the preferred answer>>`

## Budgets and stop

- participants / concurrency: `<<limits>>`
- round budget: `<<normally 1; deliberation normally 2, max 3>>`
- elapsed-time budget: `<<duration>>`
- usage / quota budget: `<<provider-specific limit or capacity units>>`
- stop conditions:
  - `<<artifact complete / decisive evidence / no new evidence / user decision needed>>`

## Recurring trigger guard (only for sentinel / event-triggered)

- runtime availability verified: `<<yes/no>>`
- trigger / timezone or event filter: `<<definition>>`
- enabled initially: `false`
- dedupe key: `<<stable key>>`
- overlap policy: `forbid`
- max concurrent runs: `1`
- max runs / day: `<<limit>>`
- max wall time / attempts / usage: `<<hard limits>>`
- backoff / circuit breaker: `<<policy>>`
- pause / disable / kill-switch owner: `<<owner>>`
- output and retention: `<<bounded report location and count>>`

## Synthesis record

- consensus: `<<after execution>>`
- important disagreement: `<<after execution>>`
- decisive evidence: `<<after execution>>`
- decision and rejected alternatives: `<<after execution>>`
- remaining risks / follow-ups: `<<after execution>>`
