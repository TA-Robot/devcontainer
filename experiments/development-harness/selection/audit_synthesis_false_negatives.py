"""Reproduce F12-L semantic false negatives without changing its historical oracle."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_duration_cases import f12
from agent_duration_fixtures import build_fixture, evaluate_fixture


def audit():
    cases = {'reference': copy.deepcopy(f12.L_GOOD),
             'explicitly-deny-generalization': copy.deepcopy(f12.L_GOOD),
             'additional-recovery-unknown': copy.deepcopy(f12.L_GOOD)}
    for claim in cases['explicitly-deny-generalization']['claims']:
        if claim['claim_id'] == 'A-WARM':
            claim['condition'] += ' This comparison is not universal.'
    cases['additional-recovery-unknown']['unknowns'].append({
        'unknown_id': 'U-ADDITIONAL-RECOVERY', 'status': 'unknown', 'evidence': ['INC-D-RECOVERY'],
        'missing_evidence': 'Rollback escalation and operator coverage for the unresolved recovery incident remain unverified.'})
    records = []
    for label, answer in cases.items():
        with tempfile.TemporaryDirectory(prefix='f12-false-negative-') as raw:
            folder = Path(raw) / 'fixture'
            build_fixture('F12-L-MDJSON-001', folder,
                catalog_path=ROOT / 'experiments/multi-agent-duration/catalog/families/f12.json',
                fixture_id='f12-false-negative-' + label)
            (folder / 'workspace/decision-record.json').write_text(json.dumps(answer))
            (folder / 'workspace/DECISION-RECORD.md').write_text(f12._render_l(answer))
            value = evaluate_fixture(folder)
            records.append({'candidate': label, 'status': value['status'], 'score': value['score']})
    return {'kind': 'f12-false-negative-calibration', 'case_id': 'F12-L-MDJSON-001', 'revision': 3,
            'case_source_sha256': hashlib.sha256(Path(f12.__file__).read_bytes()).hexdigest(),
            'audit_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'records': records, 'historical_score_overwritten': False, 'live_provider_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        result = audit()
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps([{'candidate': r['candidate'], 'score': r['score']['passed'],
                      'failed': r['score']['failed_check_ids']} for r in result['records']]))
