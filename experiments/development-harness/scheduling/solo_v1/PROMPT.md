Develop the strongest scheduling policy you can within the supplied development budget.
You are the sole developer. Do not use another model or agent, including invoking
Codex again from shell. Ordinary Python/shell experiments, algorithmic search,
multiple candidate implementations, self-review, redesign and tests are encouraged.

Read /public/TASK.md and /public/WORKLOAD.md. The public development cases,
reference target vector and starting FIFO policy are under /public. Your writable
workspace is /work. Start from /public/fifo.py or design your own implementation.

Run public tests with:
python3 /public/public_check.py --candidate /work/YOUR_POLICY.py --output /work/NEW_REPORT.json
Use a fresh output path each time. Reports include per-case traces. You may create
your own valid cases and pass --cases /work/YOUR_CASES.json for additional experiments.
Compare actual policies; do not stop after merely satisfying the interface.
Explore alternative strategies and investigate unsuccessful workload families.
The target is an attainable reference level, not an optimality guarantee.
Do not hard-code public cases; final assessment uses unseen qualification instances
from the declared domain. No hidden evaluation feedback will be provided.

When ready, save your selected single-file Python program to /work/submission.py
and give a concise final report of your experiments, selection and remaining weaknesses.
Only that file is the submission. Keep other candidates and test results as evidence.
You may submit early. You have 1800 seconds in total for development, tests and
selection, and an observed output allowance of 60000 tokens. Unknown final usage
or runtime failure prevents a difficulty conclusion. A last-minute partial file
is preserved but not silently promoted to a valid completed submission.
