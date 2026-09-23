# F07-S-MD-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `agentctl.py` | CLI source of truth | working |
| `README.md` | documentation target | obsolete command and missing constraint |
| `tests/test_cli.py` | public parser behavior | passing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The README places `--workspace` before the subcommand even though the parser scopes it to `doctor`, and never states that the path must remain inside the current workspace. A separate `--json` example is already correct.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Inspect parser/help and existing tests.
2. Replay the documented and actual command forms.
3. Patch only the relevant README section with correct syntax and constraint.
4. Run link/command validation.

## Private known-good outline

The README shows `agentctl doctor --json --workspace .`, explains containment and rejection of outside paths, and preserves the already-correct JSON example/link.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
