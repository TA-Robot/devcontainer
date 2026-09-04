# Small 01: reject invalid orphan-recovery timing configuration

Status: selected from a provider-free reproduction while the large control was
running; not executed by a development model yet.

The current Supervisor constructor accepts AGENTCTL_ORPHAN_AFTER_SECONDS=nan,
inf, and 1e309. These values cannot define a usable finite orphan-recovery
threshold. Direct construction against a temporary state path reproduced all
three acceptances without starting a supervisor or provider. The existing
heartbeat interval parser already rejects non-finite values; do not broaden the
task into unrelated configuration cleanup.

## Development task

Fix the orphan threshold parsing in scripts/agentctl_supervisor.py so that
non-finite values, including overflow, raise AgentctlJobError with a useful
configuration error before any work is dispatched. Preserve the default,
finite values at or above the existing lower bound, and rejection below the
bound or of malformed strings. Add meaningful regressions and complete the
relevant mandatory repository checks. Keep the change focused. Do not weaken
existing checks, modify the development provider/model or start additional
agents. Leave reviewable source changes and report unexecuted checks honestly.

## Measurement

Use a fresh checkout of the same fixed starting source as large-01, plus only
the chosen harness intervention for the improved condition. Keep the task,
model, CLI and authority identical. One stage, 1,800 seconds and 20,000 observed
output tokens per condition are study-local cost/admission caps owned by the
primary; unknown usage is not zero. No retry without a recorded amendment.

This is a small real configuration bug. It is a different code path/input
surface from cycle-001's JSON validator but belongs to the related numeric
validation family. It therefore checks small-task overhead and regression of
the chosen harness intervention, not broad task diversity. Report it separately
from the sustained project lifecycle campaign. The outer evaluator and hashes
must be fixed before these live runs.
