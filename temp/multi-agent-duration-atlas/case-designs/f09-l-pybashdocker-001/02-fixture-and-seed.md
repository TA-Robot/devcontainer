# F09-L-PYBASHDOCKER-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `orchestrator/worktrees.py` | agent/worktree naming and ownership | marker checked after path creation |
| `bin/container-run` | Docker bind/env construction | accepts newline/comma-bearing path |
| `orchestrator/credentials.py` | provider credential projection | scope metadata dropped |
| `orchestrator/cleanup.py` | PID/container/worktree cleanup | name/PID based without owner token |
| `scenarios/` | visible attack fixtures | partial |
| `THREAT-MODEL.md` | target human artifact | absent |
| `threat-model.json` | structured threats/controls/tests | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Seeded paths include worktree marker replacement between create/check, bind-option injection through an encoded path, cross-provider credential reuse after scope loss, and PID/name reuse causing peer cleanup. Controls must include ownership tokens and fail-safe lifecycle semantics.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Enumerate assets, actors, trust boundaries, lifecycle phases, and owners.
2. Reproduce each visible attack and derive preconditions/impact.
3. Build attack/control/test mappings, including control-bypass counterexamples.
4. Cover detection, containment, recovery, cleanup, and residual risk without claiming host isolation the fixture cannot prove.

## Private known-good outline

The model links four seeded attacks to boundary/lifecycle evidence, layered preventive and detective controls, ownership-token cleanup, scoped credential projection/rotation, incident recovery, and explicit external unknowns.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
