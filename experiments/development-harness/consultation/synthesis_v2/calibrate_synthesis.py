"""Private provider-free calibration; never include references in developer bundles."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time

import synthesis_case as case
import synthesis_rules as rules


def reference(alternative=False):
    value = copy.deepcopy(case.f12.L_VALID_ALTERNATIVE if alternative else case.f12.L_GOOD)
    value.update(version=2, evaluation_contract=rules.CASE_ID)
    for claim in value['claims']:
        claim['scope'] = copy.deepcopy(case.contract()['claim_scopes'][claim['claim_id']])
    for unknown in value['unknowns']:
        unknown['topics'] = ['recovery'] if 'INC-D-RECOVERY' in unknown['evidence'] else ['provider']
    if alternative:
        # v2 additionally requires resolvable matrix references. This is a new private
        # calibration answer, not a conversion of any historical participant artifact.
        value['constraint_matrix'][1]['gate_id'] = 'G-A-OWNER'
        value['constraint_matrix'][2]['gate_id'] = 'R-A'
    return value


def candidates():
    rows = []

    def add(name, change=None, expected='pass', failed=None, boundary=False):
        value = reference()
        if change:
            change(value)
        rows.append({'candidate': name, 'answer': value, 'expected': expected,
                     'required_failure': failed, 'unmeasured_boundary': boundary})

    def claim(value, key='A-WARM'):
        return next(c for c in value['claims'] if c['claim_id'] == key)

    add('reference')
    add('alternative-target-and-identifiers')
    rows[-1]['answer'] = reference(True)
    add('deny-generalization', lambda v: claim(v).update(condition=
        'Observed warm comparison only; not universal, not all workloads, not cold and warm.'))
    add('deny-serialized-guarantees', lambda v: v['unknowns'][1].update(missing_evidence=
        'No universal winner is established and provider behavior guaranteed is not a supported claim.'))
    add('non-english-explanation', lambda v: (claim(v).update(condition='提示された暖機済みの観測値だけを比較する。'),
        v['unknowns'][1].update(missing_evidence='将来の提供元の挙動と失効処理は未確認。')))
    add('additional-recovery-unknown', lambda v: v['unknowns'].append({
        'unknown_id': 'extra-recovery', 'status': 'unknown', 'topics': ['recovery', 'rollback'],
        'evidence': ['INC-D-RECOVERY'], 'missing_evidence': 'Escalation and operator coverage remain unverified.'}))
    add('additional-provider-unknown', lambda v: v['unknowns'].append({
        'unknown_id': 'extra-provider', 'status': 'unknown', 'topics': ['provider', 'runtime'],
        'evidence': ['INC-D-RECOVERY'], 'missing_evidence': 'Runtime behavior across identity changes is unverified.'}))
    add('overlapping-topics-and-evidence', lambda v: v['unknowns'][1].update(
        topics=['provider', 'recovery'], evidence=['INC-D-RECOVERY']))
    add('reordered-claims', lambda v: v['claims'].reverse())
    add('renamed-unknown-identifiers', lambda v: [u.update(unknown_id='local-' + str(i))
                                               for i, u in enumerate(v['unknowns'])])
    for name, change, failure in (
        ('universal-population', lambda v: claim(v)['scope'].update(population='all-workloads'), 'claim-scope'),
        ('cross-workload-inference', lambda v: claim(v)['scope'].update(workloads=['warm', 'cold']), 'claim-scope'),
        ('unsupported-throughput', lambda v: claim(v, 'C-THROUGHPUT').update(disposition='supported'), 'claim-scope'),
        ('missing-claim-evidence', lambda v: claim(v).update(evidence=[]), 'evidence-links'),
        ('wrong-existing-evidence', lambda v: claim(v).update(evidence=['BM-B-WARM']), 'evidence-links'),
        ('invented-evidence', lambda v: v['unknowns'][1].update(evidence=['INVENTED']), 'evidence-links'),
        ('missing-provenance', lambda v: claim(v).update(provenance=[]), 'artifact-contract'),
        ('wrong-provenance', lambda v: claim(v).update(provenance=['proposals/B.md']), 'evidence-links'),
        ('missing-recovery-topic', lambda v: v['unknowns'][0].update(topics=['ownership']), 'unknown-coverage'),
        ('missing-provider-topic', lambda v: v['unknowns'][1].update(topics=['runtime']), 'unknown-coverage'),
        ('missing-recovery-evidence', lambda v: v['unknowns'][0].update(evidence=[]), 'unknown-coverage'),
        ('unknown-declared-known', lambda v: v['unknowns'][1].update(status='known'), 'unknown-coverage'),
        ('recovery-guaranteed', lambda v: claim(v, 'D-RECOVERY').update(disposition='supported', confidence='high'), 'unknown-coverage'),
        ('missing-unknown-explanation', lambda v: v['unknowns'][1].update(missing_evidence=''), 'artifact-contract'),
        ('duplicate-claim-id', lambda v: v['claims'].append(copy.deepcopy(v['claims'][0])), 'artifact-contract'),
        ('duplicate-unknown-id', lambda v: v['unknowns'].append(copy.deepcopy(v['unknowns'][0])), 'artifact-contract'),
        ('wrong-median', lambda v: v['metrics'][0].update(median_ms=0), 'metric-integrity'),
        ('boolean-sample-count', lambda v: v['metrics'][0].update(sample_count=True), 'artifact-contract'),
        ('censored-count-lost', lambda v: v['metrics'][1].update(censored=0), 'metric-integrity'),
        ('pooled-samples-accepted', lambda v: v['metrics'][4].update(valid=True, median_ms=100), 'metric-integrity'),
        ('missing-controls', lambda v: v.update(controls=v['controls'][1:]), 'decision-constraints'),
        ('immediate-target', lambda v: v['decision'].update(phases=v['decision']['phases'][1:]), 'decision-constraints'),
        ('missing-decision-edge', lambda v: v['decision'].update(depends_on=['D-MIGRATION']), 'decision-constraints'),
        ('dangling-gate', lambda v: v['constraint_matrix'][0].update(gate_id='absent'), 'decision-constraints'),
        ('missing-alternative-counterevidence', lambda v: v['alternatives'][0].update(evidence=[]), 'decision-constraints'),
        ('wrong-contract-version', lambda v: v.update(evaluation_contract='F12-L-MDJSON-001'), 'artifact-contract'),
        ('missing-scope', lambda v: claim(v).pop('scope'), 'artifact-contract'),
    ):
        add(name, change, 'fail', failure)
    # These deliberately pass: preventing a claim that prose/operations are now measured.
    add('ungraded-prose-contradiction', lambda v: claim(v).update(
        condition='A is a universal winner for all workloads.'), boundary=True)
    add('ungraded-operational-noop', lambda v: (v['controls'][0].update(decision_effect='Ignore this control.'),
        v['decision']['phases'][0]['gates'][0].update(check='printf success', expected='success'),
        v['decision']['phases'][0]['rollback_triggers'][0].update(action='Ignore failure and continue.')), boundary=True)
    return rows


def submit(workspace, value):
    (workspace / 'decision-record.json').write_text(json.dumps(value, ensure_ascii=False, allow_nan=False))
    (workspace / 'DECISION-RECORD.md').write_text(rules.render(value))


def calibrate():
    started = time.monotonic()
    records = []
    with tempfile.TemporaryDirectory(prefix='synthesis-v2-calibration-') as raw:
        workspace = Path(raw) / 'workspace'
        case.create(workspace)
        for candidate in candidates():
            submit(workspace, candidate['answer'])
            result = case.evaluate(workspace)
            failures = [r['name'] for r in result['checks'] if r['status'] == 'failed']
            matched = (result['status'] == candidate['expected'] and
                       (candidate['required_failure'] is None or candidate['required_failure'] in failures))
            records.append({key: value for key, value in candidate.items() if key != 'answer'} |
                           {'status': 'pass' if matched else 'fail', 'evaluation': result})
    sources = {name: hashlib.sha256((case.HERE / name).read_bytes()).hexdigest()
               for name in ('synthesis_case.py', 'synthesis_rules.py', 'calibrate_synthesis.py', 'brief.md')}
    sources['historical_f12.py'] = hashlib.sha256(Path(case.f12.__file__).read_bytes()).hexdigest()
    passed = all(r['status'] == 'pass' for r in records)
    return {'case_id': rules.CASE_ID, 'kind': 'provider-free-calibration',
            'status': 'pass' if passed else 'fail',
            'live_provider_calls': 0, 'historical_score_overwritten': False,
            'source_sha256': sources, 'duration_seconds': time.monotonic() - started,
            'admission': 'structured-assembly-calibrated-only' if passed else 'blocked-by-calibration',
            'general_quality_comparison_eligible': False,
            'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        result = calibrate()
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'records': len(result['records'])}))
    raise SystemExit(result['status'] != 'pass')
