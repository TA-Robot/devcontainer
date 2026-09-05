Complete the independent-verification workflow for unattended use and distribution,
preserving all earlier behavior and state compatibility.

Prevent overlapping checkers for the same attempt. Acquire ownership before any
command side effect; a second checker must fail promptly without executing its
commands or publishing a successful report. Different attempts can be checked
independently. `checks` must make in-progress/incomplete verification visible and
`validate --require-checks` must refuse it.

Handle ordinary interruption such as SIGTERM: terminate the command process group,
preserve bounded evidence and leave verification incomplete/failed, never passed.
Abrupt checker death or container interruption must not leave a reusable passing
record. Do not claim a process survives container restart. Document how an operator
can establish that an old execution has stopped and safely start an explicit
new check; do not reset the budget or silently rerun old commands.

Complete the deployed workflow: a fresh user in the shipped devcontainer can
create/run a job with the existing interface, independently check its immutable
task commands, inspect fresh/stale evidence, and validate with `--require-checks`.
Package any new runtime module in the image; never rely on a mounted source tree
to supply an installed dependency. Update operational docs with executable usage,
failure diagnosis, the legacy/independent distinction and bounded evidence policy.

Verify fake-provider jobs in a real built image without mounting this checkout.
Also verify migration from the earlier stages' actual states. Exercise concurrent
checks, a failed command after a previous pass, interruption and recheck, corrupt
evidence, a user's source change, ordinary successful validation, and required
repository regressions. Run the applicable normal/frozen container checks.
Use only owned temporary fixtures/resources, with no external messages or pushes.
