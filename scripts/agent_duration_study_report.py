#!/usr/bin/env python3
"""Render a bounded content-free Markdown report from one validated atlas."""

from __future__ import annotations

from collections import defaultdict
import html
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Mapping, Sequence

from agent_contracts import load_json
from agent_duration_atlas import validate_atlas
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    canonical_json_digest,
    validate_case_catalog_record,
)
from agent_duration_validity import (
    DEFAULT_VALIDITY,
    summarize_case_validity,
    validate_validity_record,
)


DEFAULT_CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
HARD_SERIES_LIMIT = 5_000
HARD_CASE_LIMIT = 5_000
HARD_INPUT_BYTES = 512 * 1024 * 1024
HARD_OUTPUT_BYTES = 512 * 1024 * 1024
SIZE_ORDER = ("S", "M", "L")


class StudyReportError(DurationStudyError):
    """Raised when a study report cannot be rendered without losing evidence."""


def _bounded_positive(value: int, *, label: str, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > upper:
        raise StudyReportError(f"{label} must be between 1 and {upper}")
    return value


def load_validated_atlas(path: Path) -> dict[str, Any]:
    """Load one aggregate atlas under a hard byte bound; raw runs fail validation."""

    resolved = path.resolve()
    if not resolved.is_file():
        raise StudyReportError(f"study report atlas input is not a file: {path}")
    try:
        size = resolved.stat().st_size
        if size > HARD_INPUT_BYTES:
            raise StudyReportError("study report atlas input exceeds the hard byte limit")
        raw = resolved.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StudyReportError(f"cannot load study report atlas: {path}") from exc
    if not isinstance(value, dict):
        raise StudyReportError("study report atlas root must be an object")
    validate_atlas(value)
    return value


def load_validated_catalog(path: Path) -> dict[str, Any]:
    value = load_json(path.resolve())
    if not isinstance(value, dict):
        raise StudyReportError("study report catalog root must be an object")
    validate_case_catalog_record(value)
    return value


def _code(value: Any) -> str:
    if isinstance(value, str):
        rendered = value
    else:
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"<code>{html.escape(rendered, quote=False)}</code>"


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def _indented_json(value: Any) -> list[str]:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return [f"    {line}" for line in rendered.splitlines()]


def _milliseconds(value: int | float) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise StudyReportError("atlas contains a non-finite duration or score") from exc


def _ordered_series(atlas: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return sorted(atlas["series"], key=lambda item: item["series_id"])


def _ordered_cases(series: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return sorted(
        series["cases"],
        key=lambda item: (
            item["primary_stratum"]["case"]["case_id"],
            item["primary_stratum"]["case"]["revision"],
            item["stratum_id"],
        ),
    )


def _case_rows(atlas: Mapping[str, Any]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    return [
        (series, case)
        for series in _ordered_series(atlas)
        for case in _ordered_cases(series)
    ]


def _observed_index(
    case_rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]]:
    result: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = defaultdict(list)
    for series, case in case_rows:
        result[case["primary_stratum"]["case"]["case_id"]].append((series, case))
    return dict(result)


def _render_catalog_coverage(
    catalog: Mapping[str, Any] | None,
    case_rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> list[str]:
    observed = _observed_index(case_rows)
    lines = ["## Family and size coverage", ""]
    if catalog is None:
        cells: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for series, case in case_rows:
            profile = series["series_stratum"]["profile"]
            case_id = case["primary_stratum"]["case"]["case_id"]
            if case_id not in cells[profile["family"]][profile["size"]]:
                cells[profile["family"]][profile["size"]].append(case_id)
        lines.extend(
            [
                "No catalog was supplied. The table contains observed atlas cells only; the unmeasured reference cells cannot be determined.",
                "",
                "| Family | S | M | L |",
                "| --- | --- | --- | --- |",
            ]
        )
        for family in sorted(cells):
            values = [", ".join(sorted(cells[family].get(size, []))) or "not observed" for size in SIZE_ORDER]
            lines.append(f"| {family} | " + " | ".join(_cell(value) for value in values) + " |")
        lines.extend(["", "Catalog comparison: unavailable.", ""])
        return lines

    catalog_digest = canonical_json_digest(catalog)
    catalog_entries = sorted(catalog["entries"], key=lambda item: item["case"]["case_id"])
    catalog_by_id = {entry["case"]["case_id"]: entry for entry in catalog_entries}
    families: list[str] = []
    catalog_cells: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for entry in catalog_entries:
        case = entry["case"]
        if case["family"] not in families:
            families.append(case["family"])
        catalog_cells[case["family"]][case["size"]].append(case["case_id"])
    atlas_digests = sorted(
        {
            sample["catalog_digest"]
            for _series, case in case_rows
            for sample in case["samples"]
        }
    )
    digest_match = atlas_digests == [catalog_digest]
    known_observed = sorted(set(observed) & set(catalog_by_id))
    unknown_observed = sorted(set(observed) - set(catalog_by_id))
    unmeasured = sorted(set(catalog_by_id) - set(observed))

    lines.extend(
        [
            f"- Supplied catalog: {_code(catalog['catalog_id'])}, revision {_code(catalog['revision'])}",
            f"- Supplied catalog digest: {_code(catalog_digest)}",
            f"- Atlas case catalog digest(s): {', '.join(_code(item) for item in atlas_digests)}",
            (
                f"- Digest compatibility: exact; every observed case stratum names supplied catalog revision {_code(catalog['revision'])}."
                if digest_match
                else f"- Digest compatibility: mismatch; the atlas digest set does not identify supplied catalog revision {_code(catalog['revision'])}. The earlier catalog revision number is not encoded in the atlas."
            ),
            f"- Observed supplied-catalog cells: {len(known_observed)} / {len(catalog_entries)}",
            f"- Unmeasured supplied-catalog cells: {len(unmeasured)} / {len(catalog_entries)}",
            f"- Reference corpus check: {len(catalog_entries)} supplied cells; the checked-in target is 36.",
            "",
            "| Family | S | M | L |",
            "| --- | --- | --- | --- |",
        ]
    )
    for family in families:
        rendered_cells: list[str] = []
        for size in SIZE_ORDER:
            case_labels: list[str] = []
            for case_id in sorted(catalog_cells[family].get(size, [])):
                strata = observed.get(case_id, [])
                if strata:
                    run_count = sum(case["counts"]["runs"] for _series, case in strata)
                    stratum_word = "stratum" if len(strata) == 1 else "strata"
                    run_word = "run" if run_count == 1 else "runs"
                    case_labels.append(
                        f"{case_id}: observed ({len(strata)} {stratum_word}, {run_count} {run_word})"
                    )
                else:
                    case_labels.append(f"{case_id}: unmeasured")
            rendered_cells.append("<br>".join(_cell(item) for item in case_labels) or "not in catalog")
        lines.append(f"| {family} | " + " | ".join(rendered_cells) + " |")

    lines.extend(["", f"Unmeasured catalog case IDs ({len(unmeasured)}):"])
    lines.append("- " + (", ".join(_code(item) for item in unmeasured) if unmeasured else "none"))
    lines.extend(["", f"Atlas case IDs absent from supplied catalog ({len(unknown_observed)}):"])
    lines.append("- " + (", ".join(_code(item) for item in unknown_observed) if unknown_observed else "none"))

    revision_differences: list[str] = []
    identity_differences: list[str] = []
    for case_id in known_observed:
        catalog_case = catalog_by_id[case_id]["case"]
        rows = observed[case_id]
        revisions = sorted({case["primary_stratum"]["case"]["revision"] for _series, case in rows})
        if revisions != [catalog_case["revision"]]:
            revision_differences.append(
                f"{case_id}: atlas={','.join(str(item) for item in revisions)} catalog={catalog_case['revision']}"
            )
        for series, case in rows:
            identity = case["primary_stratum"]["case"]
            profile = series["series_stratum"]["profile"]
            differences: list[str] = []
            if identity["capsule_digest"] != catalog_case["capsule_digest"]:
                differences.append("capsule-digest")
            if profile["family"] != catalog_case["family"]:
                differences.append("family")
            if profile["size"] != catalog_case["size"]:
                differences.append("size")
            if identity["strong_online_oracle"] != catalog_case["strong_online_oracle"]:
                differences.append("oracle-strength")
            if differences:
                identity_differences.append(
                    f"{case_id}/{case['stratum_id']}: {','.join(differences)}"
                )
    lines.extend(["", f"Case revision differences ({len(revision_differences)}):"])
    lines.append("- " + ("; ".join(_cell(item) for item in revision_differences) if revision_differences else "none"))
    lines.extend(["", f"Case identity/profile differences ({len(identity_differences)}):"])
    lines.append("- " + ("; ".join(_cell(item) for item in identity_differences) if identity_differences else "none"))
    lines.append("")
    return lines


def _render_duration_views(case: Mapping[str, Any]) -> list[str]:
    lines = [
        "| Duration view | Evidence | Raw observed points | Observed range |",
        "| --- | --- | --- | --- |",
    ]
    for view in case["duration_views"]:
        points = view["points"]
        if len(points) == 1:
            evidence = "single observation; raw point"
        else:
            evidence = f"{len(points)} same-case observations; raw points"
        point_label = "; ".join(
            f"{point['run_id']}={_milliseconds(point['milliseconds'])} ms" for point in points
        )
        observed_range = view.get("observed_range_ms")
        if observed_range is None:
            range_label = "not available"
        else:
            range_label = (
                f"{_milliseconds(observed_range['minimum'])}–"
                f"{_milliseconds(observed_range['maximum'])} ms (observed min/max)"
            )
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (view["view_id"], evidence, point_label, range_label)
            )
            + " |"
        )
    if not case["duration_views"]:
        lines.append("| none | no duration view in aggregate | none | not available |")
    return lines


def _render_quality_evidence(
    case: Mapping[str, Any],
    validity: Mapping[str, Any] | None,
) -> list[str]:
    inference = summarize_case_validity(case, validity)
    inference_by_run = {
        item["run_id"]: item for item in inference["observations"]
    }
    lines = [
        "| Run | Outcome | Censoring / cap | Artifact auditability | Inference gate | Evaluator status | Check count | Criterion score | Failed criterion IDs |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for sample in sorted(case["samples"], key=lambda item: (item["observed_at"], item["run_id"])):
        evidence = sample["quality_evidence"]
        score = evidence["score"]
        if score is None:
            score_label = "unavailable"
            failed_label = "unavailable"
        else:
            score_label = (
                f"{score['resolution']}; {score['passed']}/{score['total']}; "
                f"ratio={_milliseconds(score['ratio'])}; "
                f"public={score['public_passed']}/{score['public_total']}; "
                f"hidden={score['hidden_passed']}/{score['hidden_total']}; "
                "all-checks-required=true"
            )
            failed_label = ", ".join(score["failed_check_ids"]) or "none"
        outcome = sample["outcome"]
        outcome_label = (
            f"infrastructure={outcome['infrastructure']}; artifact={outcome['artifact']}; "
            f"online={outcome['online_acceptance']}; offline={outcome['offline_score']}; "
            f"basis={outcome['quality_basis']}; failure={outcome['failure_class']}"
        )
        censoring = sample["censoring"]
        censoring_label = (
            f"{censoring['status']}; observed-terminal="
            f"{_milliseconds(censoring['observed_terminal_ms'])} ms; "
            f"declared-cap={_milliseconds(censoring['safety_cap_ms'])} ms"
        )
        auditability = sample.get(
            "artifact_auditability",
            {
                "retention": "content-free-only",
                "completeness": "not-retained",
                "file_count": 0,
                "total_bytes": 0,
            },
        )
        auditability_label = (
            f"{auditability['retention']}/{auditability['completeness']}; "
            f"files={auditability['file_count']}; bytes={auditability['total_bytes']}"
        )
        unexpected = auditability.get("unexpected_change_summary")
        if unexpected is not None:
            auditability_label += (
                "; unexpected("
                f"total={unexpected['total']}; "
                f"tracked={unexpected['tracked']}; "
                f"untracked={unexpected['untracked']}; "
                f"deleted={unexpected['deleted']})"
            )
        inference_observation = inference_by_run[sample["run_id"]]
        lines.append(
            "| "
            + " | ".join(
                _cell(str(value))
                for value in (
                    sample["run_id"],
                    outcome_label,
                    censoring_label,
                    auditability_label,
                    f"{inference_observation['status']}; {inference_observation['reason']}",
                    evidence["evaluator_status"],
                    evidence["check_count"],
                    score_label,
                    failed_label,
                )
            )
            + " |"
        )
    return lines


def _render_case(
    case: Mapping[str, Any],
    *,
    ordinal: int,
    validity: Mapping[str, Any] | None,
) -> list[str]:
    identity = case["primary_stratum"]["case"]
    counts = case["counts"]
    quality = counts["quality_population"]
    censoring = counts["censoring"]
    artifact = counts["first_artifact_resolution"]
    window = case["observation_window"]
    inference = summarize_case_validity(case, validity)
    lines = [
        f"### Case {ordinal}: {identity['case_id']} revision {identity['revision']}",
        "",
        f"- Stratum ID: {_code(case['stratum_id'])}",
        f"- Evidence state: {_code(case['evidence_state'])}",
        f"- Observation window: {_code(window['first_observed_at'])} to {_code(window['last_observed_at'])}",
        f"- Runs / observation blocks: {counts['runs']} / {counts['observation_blocks']}",
        f"- Effort-quality use: {_code(inference['effort_quality_use'])}",
        f"- Case design status: {_code(inference['design_status'])}",
        f"- Comparison gates: {_code(inference['comparison_gate_status'])}; not evaluated by this report",
        f"- Validity reasons: {', '.join(_code(item) for item in inference['reason_codes'])}",
        "",
        "#### Exact case identity",
        "",
    ]
    lines.extend(_indented_json(identity))
    lines.extend(
        [
            "",
            "| Count group | Values |",
            "| --- | --- |",
            (
                "| Quality | "
                f"pass={quality['quality-pass']}; fail={quality['quality-fail']}; "
                f"unknown={quality['quality-unknown']} |"
            ),
            (
                "| Censoring | "
                f"complete={censoring['complete-terminal']}; right={censoring['right-censored']}; "
                f"administrative={censoring['administratively-censored']} |"
            ),
            (
                "| First artifact | "
                f"progress={artifact['progress-envelope']}; not-observed={artifact['not-observed']}; "
                f"not-applicable={artifact['not-applicable']}; unknown={artifact['unknown']} |"
            ),
            "",
        ]
    )
    lines.extend(_render_duration_views(case))
    lines.extend(["", "#### Content-free quality evidence", ""])
    lines.extend(_render_quality_evidence(case, validity))
    lines.append("")
    return lines


def _render_series(
    series: Mapping[str, Any],
    *,
    ordinal: int,
    case_ordinal: int,
    validity: Mapping[str, Any] | None,
) -> tuple[list[str], int]:
    stratum = series["series_stratum"]
    window = series["observation_window"]
    lines = [
        f"## Series {ordinal}",
        "",
        f"- Series ID: {_code(series['series_id'])}",
        f"- Study ID: {_code(stratum['study_id'])}",
        f"- Evidence state: {_code(series['evidence_state'])}",
        f"- Observation window: {_code(window['first_observed_at'])} to {_code(window['last_observed_at'])}",
        f"- Characterization: {_code(series['characterization']['status'])}; {_code(series['characterization']['reason'])}",
        f"- Execution surface(s): {', '.join(_code(item['execution_surface']) for item in stratum['participants'])}",
        "",
        "### Exact profile and configuration",
        "",
    ]
    lines.extend(_indented_json({"profile": stratum["profile"], "configuration": stratum["configuration"]}))
    lines.extend(["", "### Exact environment", ""])
    lines.extend(_indented_json(stratum["environment"]))
    lines.extend(["", "### Exact participant, model, requested/applied settings, and surface", ""])
    lines.extend(_indented_json(stratum["participants"]))
    lines.extend(["", "### Case observations", ""])
    for case in _ordered_cases(series):
        case_ordinal += 1
        lines.extend(_render_case(case, ordinal=case_ordinal, validity=validity))
    return lines, case_ordinal


def build_study_report(
    atlas: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any] | None = None,
    validity: Mapping[str, Any] | None = None,
    max_series: int,
    max_cases: int,
    max_output_bytes: int,
) -> str:
    """Build deterministic Markdown or fail before silently omitting a stratum."""

    _bounded_positive(max_series, label="max-series", upper=HARD_SERIES_LIMIT)
    _bounded_positive(max_cases, label="max-cases", upper=HARD_CASE_LIMIT)
    _bounded_positive(max_output_bytes, label="max-output-bytes", upper=HARD_OUTPUT_BYTES)
    validate_atlas(atlas)
    if catalog is not None:
        if not isinstance(catalog, Mapping):
            raise StudyReportError("study report catalog root must be an object")
        validate_case_catalog_record(dict(catalog))
    if validity is not None:
        validate_validity_record(validity, catalog=catalog)
    series_items = _ordered_series(atlas)
    case_rows = _case_rows(atlas)
    if len(series_items) > max_series:
        raise StudyReportError(
            f"atlas has {len(series_items)} series, exceeding explicit max-series {max_series}"
        )
    if len(case_rows) > max_cases:
        raise StudyReportError(
            f"atlas has {len(case_rows)} case strata, exceeding explicit max-cases {max_cases}"
        )

    source = atlas["source"]
    window = source["observation_window"]
    lines = [
        "# Agent Duration Study Report",
        "",
        "This is a deterministic observational report built from a validated aggregate atlas. It does not copy raw prompts, transcripts, private reasoning, or retained task-artifact content.",
        "",
        "## Methodology",
        "",
        f"- Aggregate method: {_code(atlas['aggregation_method'])}",
        "- Duration values are emitted only as raw case points and aggregate-provided observed min/max ranges.",
        "- One observation is shown only as one raw point. A range requires at least two points in the same case stratum.",
        "- Requested generation values remain distinct from applied values; an applied value appears only when the atlas records status `applied`.",
        "- Criterion scores and failed criterion IDs are emitted only from each sample's content-free quality evidence. Missing scores remain unavailable and are not inferred.",
        "- Retained artifact content and paths are omitted. When available, unexpected tracked, untracked, and deleted changes are shown only as counts.",
        "- Case-design and observation validity are reported separately. Comparison gates remain open until identity, applied setting, repeat/singleton conditions, and quality-measurement headroom are checked.",
        "- The report is descriptive only. It produces no provider/model ranking, automatic route, or preferred configuration.",
        "",
        "## Observation window and provenance",
        "",
        f"- First observed: {_code(window['first_observed_at'])}",
        f"- Last observed: {_code(window['last_observed_at'])}",
        f"- Source run-set digest: {_code(source['run_set_digest'])}",
        f"- Source run schema: {_code(source['run_schema_version'])}",
        f"- Source records: {source['record_count']}",
        f"- Canonical source bytes: {source['canonical_record_bytes']}",
        f"- Atlas counts: series={atlas['counts']['series']}; case-strata={atlas['counts']['case_strata']}; samples={atlas['counts']['samples']}",
        f"- Report resource caps: max-series={max_series}; max-cases={max_cases}; max-output-bytes={max_output_bytes}",
        "",
    ]
    if validity is not None:
        summaries = [summarize_case_validity(case, validity) for _series, case in case_rows]
        use_counts = {
            status: sum(item["effort_quality_use"] == status for item in summaries)
            for status in (
                "eligible-pending-comparison-gates",
                "conditional-only",
                "excluded",
                "not-audited",
            )
        }
        lines.extend(
            [
                "## Effort-quality inference validity",
                "",
                f"- Validity audit: {_code(validity['validity_id'])}",
                f"- Audit scope: {_code(validity['scope'])}",
                f"- Audit catalog digest: {_code(validity['catalog']['digest'])}",
                f"- Observed case-stratum use counts: {_code(use_counts)}",
                "- Pending comparison gates: "
                + ", ".join(_code(item) for item in validity["policy"]["comparison_gates"]),
                "- `eligible-pending-comparison-gates` is not a conclusion that effort caused quality; this report does not evaluate those comparison gates.",
                "- Revision-1 F10-S and F12-L are excluded. Missing/partial failed artifacts remain conditional, even when their terminal time is valid.",
                "",
            ]
        )
    lines.extend(_render_catalog_coverage(catalog, case_rows))
    case_ordinal = 0
    for ordinal, series in enumerate(series_items, start=1):
        rendered, case_ordinal = _render_series(
            series,
            ordinal=ordinal,
            case_ordinal=case_ordinal,
            validity=validity,
        )
        lines.extend(rendered)
    lines.extend(
        [
            "## Limitations",
            "",
            "- This report preserves the atlas strata and does not generalize beyond the exact environment, model identity, generation-setting status, execution surface, case revision, and observation window shown above.",
            "- Observed min/max values describe only the displayed same-case points; they are not uncertainty or prediction intervals.",
            "- Right- or administratively-censored terminal times are incomplete observations and are counted separately.",
            "- Criterion-level details are limited to the aggregate's content-free score fields and failed IDs; evaluator rubric text is not present and is not reconstructed.",
            "- Unmeasured catalog cells remain unmeasured; no adjacent family, size, model, or provider value is substituted.",
            "- Raw prompts, transcripts, private reasoning, retained task-artifact contents, and evaluator output are outside this report; only auditability metadata is shown.",
            "",
        ]
    )
    report = "\n".join(lines)
    encoded = report.encode("utf-8")
    if len(encoded) > max_output_bytes:
        raise StudyReportError(
            f"study report output is {len(encoded)} bytes, exceeding explicit max-output-bytes {max_output_bytes}"
        )
    return report


def atomic_write_study_report(
    path: Path,
    report: str,
    *,
    max_output_bytes: int,
    replace: Callable[[Path, Path], Any] = os.replace,
) -> None:
    """Atomically create or replace a derived Markdown report after cap checks."""

    _bounded_positive(max_output_bytes, label="max-output-bytes", upper=HARD_OUTPUT_BYTES)
    encoded = report.encode("utf-8")
    if len(encoded) > max_output_bytes:
        raise StudyReportError("study report output exceeds max-output-bytes before writing")
    if path.exists() and not path.is_file():
        raise StudyReportError("study report output path exists and is not a file")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


__all__ = [
    "DEFAULT_CATALOG",
    "DEFAULT_VALIDITY",
    "HARD_CASE_LIMIT",
    "HARD_OUTPUT_BYTES",
    "HARD_SERIES_LIMIT",
    "StudyReportError",
    "atomic_write_study_report",
    "build_study_report",
    "load_validated_atlas",
    "load_validated_catalog",
]
