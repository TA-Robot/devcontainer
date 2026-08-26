# Collaboration plan: <<short-name>>

Use only when delegation is available and allowed. Keep the plan proportional to the task; short inline answers are acceptable when they preserve the same decisions.

## Outcome

- decision / artifact: `<<what this collaboration must decide or produce>>`
- definition of done: `<<observable completion condition>>`
- solo alternative: `<<how primary would do this alone>>`

## Why multi-agent

- expected mechanism: `<<latency overlap | context partitioning | coverage | error decorrelation | empirical selection | evidence-producing refinement | temporal sampling | project-specific mechanism>>`
- why it should beat solo here: `<<task-specific causal explanation>>`
- binding constraint: `<<serialization | human review | wall-clock | quota | agentctl capacity | integration | context coupling | evaluator | late failure | other>>`
- failure signal / solo fallback: `<<evidence that collaboration is not paying for itself>>`

## Relation and lifecycle

- relation: `<<solo | delegate | consult | compete | verify | project-specific relation>>`
- lifecycle: `<<one-shot | bounded-exchange | event-triggered | scheduled | project-specific lifecycle>>`
- why this is the cheapest useful relation: `<<rationale>>`
- primary / synthesis owner: `<<owner>>`
- integration / external side-effect owner: `<<owner>>`

## Participant derivation

- participant basis: `<<non-overlapping artifacts | distinct evidence sources | meaningful approaches | independent failure probes>>`
- participants:
  - role: `<<role>>`
    bounded task / perspective: `<<assignment and why it is distinct>>`
    expected output: `<<artifact or advice result>>`
    evidence requirement: `<<required evidence>>`
    stop condition: `<<stop>>`
- capacity / wave effect: `<<how available capacity changes concurrency and wall-clock, without treating it as the ideal participant count>>`

## Shared input and independence

- shared facts / context paths: `<<facts and project-relative paths>>`
- independence policy: `<<isolated-blind | partitioned-context | artifact-shared | shared-context | sequential-handoff | other>>`
- policy rationale: `<<which bias, coverage, review, or coordination need this addresses>>`
- artifact flow: `<<who sends what to whom>>`
- claims / decisions that require evidence: `<<IDs or list>>`

## Execution boundary

- lane: `<<read | write | isolated>>`
- permission profile: `<<safe | trusted-fast | isolated-autonomous>>`
- base SHA: `<<full immutable SHA or not-applicable for read-only consultation>>`
- workspaces / allowed paths: `<<job IDs and paths>>`
- provider quota / rate-window impact: `<<impact or none known>>`
- human review / synthesis budget: `<<available reviewer attention and expected artifacts>>`

## Evaluation

- acceptance: `<<commands, files, measurements, manual checks>>`
- comparison rubric, if applicable: `<<correctness, safety, maintainability, performance, risk, migration cost>>`
- disconfirming evidence / tests: `<<what could overturn the preferred answer>>`
- evaluator capability evidence, if applicable: `<<why the evaluator can distinguish candidates>>`

## Parameters

Every numeric or boolean limit must declare its meaning. Add or remove rows as needed.

| parameter | value | role: hard guard / cost cap / planning prior / hypothesis | scope and rationale | invalidation evidence | update owner |
|---|---|---|---|---|---|
| `<<name>>` | `<<value>>` | `<<role>>` | `<<where it applies and why>>` | `<<what would change or remove it>>` | `<<owner>>` |

## Continue or stop

- continuation evidence: `<<new evidence, test, claim transition, or useful artifact required before another interaction>>`
- stop conditions:
  - `<<acceptance met / decisive evidence / no useful delta / measurement preferred / authority boundary / cost cap / expected value exhausted>>`
- partial-result behavior: `<<what is returned if a guard or cap stops the work>>`

## Recurring trigger guard (only for event-triggered / scheduled lifecycle)

- runtime availability verified: `<<yes/no>>`
- why deterministic CI / script / ordinary cron is insufficient: `<<evidence>>`
- trigger / timezone or event filter: `<<definition>>`
- enabled initially: `false`
- enable owner and explicit expiry: `<<owner and expiry>>`
- immutable input / dedupe key: `<<definition>>`
- overlap / admission policy: `<<policy and rationale>>`
- permission and side-effect boundary: `<<finite read report or candidate commit only>>`
- budget / backoff / circuit parameters: `<<rows in Parameters section>>`
- pause / disable / kill-switch owner: `<<owner>>`
- audit output and retention: `<<content-free trigger record and bounded result location>>`

## Synthesis and project-local learning

- decision / accepted artifact: `<<after execution>>`
- decisive evidence: `<<after execution>>`
- important disagreement and handling: `<<after execution>>`
- rejected alternatives and reasons: `<<after execution>>`
- remaining risks / follow-ups: `<<after execution>>`
- did collaboration change the outcome: `<<yes/no/unknown and evidence>>`
- review / integration cost worth paying: `<<yes/no/unknown and evidence>>`
- parameter or routing change for the next comparable task: `<<project-local update, including a return to solo when appropriate>>`
