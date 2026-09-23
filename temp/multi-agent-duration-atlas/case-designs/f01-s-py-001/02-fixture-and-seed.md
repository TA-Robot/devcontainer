# F01-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `syncctl/cli.py` | argparse definition and dispatch | working implementation |
| `syncctl/paths.py` | normalization and marker validation | working implementation |
| `tests/test_cli.py` | public behavior | passing tests |
| `trace.json` | required answer | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The code is correct; the seeded failure is the absence of `trace.json`. Distractor helpers use similarly named `state_path` values but never receive the CLI flag.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Locate the exact parser action for `--state-dir`.
2. Follow the parsed value through dispatch and normalization.
3. Identify the ownership-marker validation and final consumer.
4. Write ordered nodes, edges, and evidence locations to `trace.json`.

## Private known-good outline

A six-node JSON DAG follows `build_parser -> Namespace.state_dir -> run_sync -> normalize_state_dir -> require_owner_marker -> StateStore`, with evidence paths and no legacy helper.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
