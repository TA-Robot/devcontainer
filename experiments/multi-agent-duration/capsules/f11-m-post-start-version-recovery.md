# F11-M-BASH-001: version synchronization and restart recovery

Repair `initialize-host.sh` and `post-start.sh` while preserving the simulated `install-cli` contract.

Script arguments are public fixture contracts:

- `initialize-host.sh RAW_VERSION HOST_METADATA`
- `post-start.sh HOST_METADATA INSTALLED_VERSION READY_VERSION INSTALL_LEDGER`
- `install-cli DESIRED_VERSION INSTALLED_VERSION INSTALL_LEDGER`

Requirements:

- Accept exactly one version line. Strip a terminal CR and trailing spaces/tabs, then require `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
- Reject empty, leading-whitespace, embedded-whitespace, invalid-character, and multiline metadata. Never concatenate multiple lines into a valid version.
- Write canonical host metadata atomically.
- If installed and ready marker versions both equal the desired version, perform no installation.
- If installed differs, invoke the fixture installer once and verify its resulting version.
- Write the ready marker atomically only after installed-version verification. Its content is the verified version, not a boolean.
- A failed or wrong-version installation must not publish desired-version readiness. A later fresh process retries safely.
- Cleanup only script-owned `*.tmp.PID` files. Preserve host metadata, installed state, ledger, ready data for the last verified version, and peer sentinels.
- Do not replace comparison with unconditional reinstall or broad whitespace deletion.

Validation:

```bash
bash -n initialize-host.sh post-start.sh install-cli tests/lifecycle.sh
bash tests/lifecycle.sh
```

Return the normalization invariant, ready-marker commit point, restart behavior, and validation results.
