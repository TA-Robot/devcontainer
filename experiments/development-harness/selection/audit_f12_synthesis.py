"""Provider-free audit of what F12-L actually distinguishes; historical source is unchanged."""
import argparse
import copy
from datetime import datetime, timezone
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
    records = []
    answers = {'known-good': copy.deepcopy(f12.L_GOOD),
               'ineffective-operational-controls': copy.deepcopy(f12.L_GOOD),
               'wrong-measured-metric': copy.deepcopy(f12.L_GOOD)}
    hollow = answers['ineffective-operational-controls']
    for control in hollow['controls']:
        control['decision_effect'] = 'Do not enforce this control; proceed even if the incident recurs.'
    for phase in hollow['decision']['phases']:
        for gate in phase['gates']:
            gate['check'] = 'printf success'
            gate['expected'] = 'success'
        for trigger in phase['rollback_triggers']:
            trigger['action'] = 'Ignore the failed check and continue without rollback.'
    for metric in answers['wrong-measured-metric']['metrics']:
        if metric['evidence_id'] == 'BM-A-WARM':
            metric['median_ms'] = 0
    for name, answer in answers.items():
        with tempfile.TemporaryDirectory(prefix='f12-suitability-') as raw:
            path = Path(raw) / 'fixture'
            fixture = build_fixture('F12-L-MDJSON-001', path,
                catalog_path=ROOT / 'experiments/multi-agent-duration/catalog/families/f12.json',
                fixture_id='f12-suitability-' + name, now=datetime(2026, 9, 6, tzinfo=timezone.utc))
            workspace = path / 'workspace'
            (workspace / 'decision-record.json').write_text(json.dumps(answer))
            (workspace / 'DECISION-RECORD.md').write_text(f12._render_l(answer))
            evaluated = evaluate_fixture(path)
            records.append({'candidate': name, 'case': fixture['case'], 'snapshot': fixture['snapshot'],
                            'status': evaluated['status'], 'score': evaluated['score']})
    return {'kind': 'provider-free-f12-suitability-audit', 'case_id': 'F12-L-MDJSON-001',
            'scope': 'contrast numeric evidence validation with operational-control meaning',
            'case_source_sha256': hashlib.sha256(Path(f12.__file__).read_bytes()).hexdigest(),
            'audit_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'records': records,
            'interpretation': 'Passing structural checks does not establish that proposed safeguards or rollback actions work.',
            'live_provider_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        result = audit()
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps([{'candidate': r['candidate'], 'status': r['status']} for r in result['records']]))
