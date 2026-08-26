#!/usr/bin/env python3
"""Render the primary-owned six-document design set for all duration cases."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from _case_design_data import CASES


ROOT = Path(__file__).resolve().parent
DOC_NAMES = (
    "01-profile-and-question.md",
    "02-fixture-and-seed.md",
    "03-task-and-artifact-contract.md",
    "04-oracle-and-quality-rubric.md",
    "05-execution-and-analysis.md",
    "06-implementation-handoff.md",
)
PLACEHOLDER = re.compile(r"\b(?:TBD|TODO|FIXME)\b", re.IGNORECASE)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def profile_table(case: dict[str, object]) -> str:
    rows = [
        ("case ID", case["case_id"]),
        ("family", case["family"]),
        ("size", case["size"]),
        ("profile ID", case["profile_id"]),
        ("ambiguity", case["ambiguity"]),
        ("oracle", case["oracle"]),
        ("decomposability", case["decomposability"]),
        ("artifact", case["artifact_type"]),
        ("risk", case["risk"]),
        ("lane", case["lane"]),
        ("environment", case["environment"]),
        ("knowledge", case["knowledge"]),
        ("stack", ", ".join(case["stack"])),
    ]
    return "\n".join(["| Axis | Value |", "| --- | --- |", *[f"| {key} | `{value}` |" for key, value in rows]])


def render_profile(case: dict[str, object]) -> str:
    descriptors = case["descriptors"]
    return f"""# {case['case_id']}: profile and measurement question

## Scenario

{case['scenario']}

## Measurement question

{case['measurement_question']}

{profile_table(case)}

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | {descriptors['context_surface']} |
| artifact surface | {descriptors['artifact_surface']} |
| coupling | {descriptors['coupling']} |
| validation depth | {', '.join(descriptors['validation_depth'])} |
| environment setup | {descriptors['environment_setup']} |
| failure distance | {descriptors['failure_distance']} |
| statefulness | {descriptors['statefulness']} |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

{bullets(case['reveals'])}

## Scope boundary

{bullets(case['non_goals'])}

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
"""


def render_fixture(case: dict[str, object]) -> str:
    file_rows = "\n".join(
        f"| `{item['path']}` | {item['role']} | {item['initial']} |"
        for item in case["files"]
    )
    return f"""# {case['case_id']}: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
{file_rows}

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

{case['seed']}

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

{numbered(case['work_path'])}

## Private known-good outline

{case['known_good']}

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
"""


def render_task(case: dict[str, object]) -> str:
    return f"""# {case['case_id']}: task and artifact contract

## Agent-visible task

{case['task']}

## Required result

{bullets(case['requirements'])}

## Allowed work

{bullets(case['allowed'])}

## Forbidden work

- network、親directory、control directory、hidden/gold artifactを読むこと。
- commit、push、remote追加、credential探索、別caseの参照。
- public checkやproduction behaviorを削除・skip・緩和してpassさせること。
- 契約外pathの変更。必要性を発見した場合は成果物へunknown/blockerとして残す。

## Public validation

{bullets(case['public_checks'])}

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
"""


def render_oracle(case: dict[str, object]) -> str:
    hidden_rows = "\n".join(
        f"| `{item['id']}` | {item['criterion']} | {item['signal']} |"
        for item in case["hidden"]
    )
    return f"""# {case['case_id']}: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
{hidden_rows}

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

{bullets(case['mutants'])}

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

{case['rubric_boundary']}

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
"""


def render_execution(case: dict[str, object]) -> str:
    return f"""# {case['case_id']}: execution and analysis plan

## Finite execution block

{bullets(case['execution'])}

requested effortはapplied effortの証拠ではない。Codex、Claude、Grokのsetting namespaceを分離し、providerが確認できた値だけをapplied seriesへ置く。`xhigh`、`max`、Codexの`ultra`はtaskが深い場合の候補から除外せず、unsupportedはtask failureでなくcapability evidenceとして残す。

## Collaboration eligibility

{bullets(case['collaboration'])}

agent数やdialogue round数はdefault化しない。caseのdecomposabilityと未解決claimに適合する点だけをfinite paired blockとして追加し、exact participant count、dispatch、worker terminal、synthesisを計測する。

## Timing and caps

- case timeout safety cap: {case['timeout']}
- provider start前にcredential freshness、runtime identity、sandbox、network policyを確認する。
- T0/T1/T6、online validation V0/V1、offline scoring S0/S1を分離する。
- timeout、rate limit、provider rejection、harness failureを成功sampleから消さない。
- orderはblock間でrotateし、fresh contextを基本にする。warm/cache treatmentは別seriesにする。

## Interpretation questions

{bullets(case['analysis'])}

単一runはraw observationでありtypical bandではない。同一case repeatとisomorphic variantは別々に集計し、family promotion条件を満たすまで`single-observation`または`same-case-repeat`に留める。
"""


def render_handoff(case: dict[str, object]) -> str:
    family_code = case["case_id"][:3].lower()
    return f"""# {case['case_id']}: implementation handoff

## Exclusive implementation scope

- recipe module: `scripts/agent_duration_cases/{family_code}.py`
- catalog fragment: `experiments/multi-agent-duration/catalog/families/{family_code}.json`
- capsule: `{case['capsule_path']}`
- focused test: `scripts/test-agent-duration-case-{family_code}.py`

同familyの3 sizeは一つのmodule/fragment/testへまとめてよい。共有registry、schema、aggregate `cases.json`、generic fixture runner、reporterは変更しない。

## Implementation requirements

{bullets(case['implementation'])}

## Definition of Done

{numbered(case['definition_of_done'])}

## Stop and return to primary when

- 現行recipe interfaceではrubricを安全に表現できない。
- hidden evaluatorをagent workspaceへ見せないと評価できない。
- network、host credential、shared Docker socket、親workspace writeが必要になる。
- case wording、profile、criterionを変えないとknown-good calibrationが通らない。
- 同family外または共有fileの変更が必要になる。

返却時は変更file、校正結果、実行したtest、残るriskを簡潔に報告する。case設計の再解釈やglobal recommendationはprimaryが担当する。
"""


RENDERERS = (
    render_profile,
    render_fixture,
    render_task,
    render_oracle,
    render_execution,
    render_handoff,
)


def audit_data() -> None:
    if len(CASES) != 36:
        raise ValueError(f"expected 36 cases, found {len(CASES)}")
    ids = [case["case_id"] for case in CASES]
    if len(ids) != len(set(ids)):
        raise ValueError("case IDs must be unique")
    pairs = Counter((case["family"], case["size"]) for case in CASES)
    families = {case["family"] for case in CASES}
    if len(families) != 12 or set(pairs.values()) != {1}:
        raise ValueError("expected exactly one S/M/L design for each of 12 families")
    required_lists = (
        "reveals", "non_goals", "files", "work_path", "requirements", "allowed",
        "public_checks", "hidden", "mutants", "execution", "collaboration", "analysis",
        "implementation", "definition_of_done", "stack",
    )
    for case in CASES:
        if case["size"] not in {"S", "M", "L"}:
            raise ValueError(f"invalid size: {case['case_id']}")
        for key in required_lists:
            if not case[key]:
                raise ValueError(f"empty {key}: {case['case_id']}")
        hidden_ids = [item["id"] for item in case["hidden"]]
        if len(hidden_ids) != len(set(hidden_ids)):
            raise ValueError(f"duplicate hidden criterion: {case['case_id']}")


def main() -> int:
    audit_data()
    index_rows = []
    for case in sorted(CASES, key=lambda item: item["case_id"]):
        directory = ROOT / case["case_id"].lower()
        directory.mkdir(parents=True, exist_ok=True)
        for name, renderer in zip(DOC_NAMES, RENDERERS, strict=True):
            content = renderer(case)
            if PLACEHOLDER.search(content):
                raise ValueError(f"placeholder found in {case['case_id']}/{name}")
            (directory / name).write_text(content, encoding="utf-8")
        actual = sorted(path.name for path in directory.glob("*.md"))
        if actual != sorted(DOC_NAMES):
            raise ValueError(f"unexpected design document set: {case['case_id']}: {actual}")
        index_rows.append(
            f"| `{case['case_id']}` | {case['family']} | {case['size']} | "
            f"`{case['profile_id']}` | designed |"
        )
    index = "\n".join(
        [
            "# Case design index",
            "",
            "Generated from the primary-owned structured design. Status is updated only after review.",
            "",
            "| Case | Family | Size | Profile | Status |",
            "| --- | --- | --- | --- | --- |",
            *index_rows,
            "",
        ]
    )
    (ROOT / "INDEX.md").write_text(index, encoding="utf-8")
    print(f"rendered and audited {len(CASES)} cases / {len(CASES) * len(DOC_NAMES)} documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
