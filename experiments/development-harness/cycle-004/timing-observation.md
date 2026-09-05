# Separate submission and shutdown time in the next clock version

During the sealed Cycle 004 small comparison, the control session returned exit
code 0, no stop reason, and complete usage, but recorded `wall_seconds=1200.873`
against the 1,200-second budget. The existing admission rule therefore rejects
budget completion. Keep that machine decision and the original observation.

Code inspection establishes a measurement limitation: the frozen
`campaign.py:observe` calculates `wall_seconds` after its `finally` block calls
`transport.stop()`. Container shutdown is part of that elapsed time. Its duration
was not separately measured in this run, so an exact submission time cannot be
reconstructed by subtracting a guessed shutdown allowance. The last progress
observation is not an exact completion timestamp either.

Before the next prospective comparison, version the clock to record developer
completion/timeout observation, shutdown duration, and total controller duration
separately. Decide explicitly which duration admission charges. Calibrate normal
completion followed by slow shutdown, a developer timeout, recorder loss, and
shutdown failure. A shutdown failure must still prevent evaluation or another
launch until stop evidence is established. Preserve the old clock and records;
do not revise this pair's budgets or grade from the newly discovered limitation.

The current result measures the declared end-to-end interval, including
checkpoint pauses and shutdown. It must not be presented as an exact measure of
model computation or as a clean developer-submission deadline comparison.
