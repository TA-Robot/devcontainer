"""Build/evaluate a separate task; historical F12 and pilot scores stay immutable."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import synthesis_rules as rules

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_duration_cases import f12

OUTPUTS = {'decision-record.json', 'DECISION-RECORD.md'}
FILE_CAP = 262144


def contract():
    value = copy.deepcopy(f12.L_DECISION_CONTRACT_VALUE)
    value.update(schema_version=3, evaluation_contract=rules.CASE_ID, record_version=2,
                 record_fields=[*f12.L_DECISION_TEMPLATE_VALUE, 'evaluation_contract'],
                 claim_condition_terms={},
                 disposition_values=['supported', 'narrowed', 'constrained', 'rejected', 'unknown', 'required'],
                 required_unknown_topics={'recovery': ['INC-D-RECOVERY'], 'provider': []})
    value['required_fields']['claim'].append('scope')
    value['required_fields']['unknown'].append('topics')
    value['claim_scopes'] = {
        key: {'population': 'supplied-evidence', 'workloads': []} for key in value['claim_ids']}
    for key, workload in (('A-WARM', 'warm'), ('A-COLD', 'cold')):
        value['claim_scopes'][key] = {'population': 'supplied-samples', 'workloads': [workload]}
    for key in ('C-THROUGHPUT', 'D-RECOVERY'):
        value['claim_scopes'][key] = {'population': 'not-established', 'workloads': []}
    # Published minimum edges come from the supplied proposal/constraint sources.
    edges = {'A-WARM': ['BM-A-WARM'], 'A-COLD': ['BM-A-COLD'],
             'B-ISOLATION': ['SEC-B-ISOLATION'], 'B-MIGRATION': ['CON-MIGRATION'],
             'C-THROUGHPUT': ['BM-C-POOLED'], 'D-MIGRATION': ['PROP-D', 'CON-MIGRATION'],
             'D-RECOVERY': ['INC-D-RECOVERY'], 'CON-MIGRATION': ['CON-MIGRATION'],
             'CON-OWNER': ['CON-OWNER', 'INC-A-CLEANUP', 'INC-D-RECOVERY'],
             'CON-ROLLBACK': ['CON-ROLLBACK']}
    value['claim_evidence'] = {key: {'required_evidence': refs,
        'provenance': 'constraints.json' if key.startswith('CON-') else f'proposals/{key[0]}.md'}
        for key, refs in edges.items()}
    return value


def files():
    value = contract()
    result = {name: source for name, source in f12.L_FILES.items()
              if name.startswith(('proposals/', 'evidence/')) or name == 'constraints.json'}
    template = copy.deepcopy(f12.L_DECISION_TEMPLATE_VALUE)
    template.update(version=2, evaluation_contract=rules.CASE_ID)
    for claim in template['claims']:
        claim['scope'] = {'population': '', 'workloads': []}
    for unknown in template['unknowns']:
        unknown['topics'] = []
    result.update({'decision-contract.json': json.dumps(value, indent=2) + '\n',
                   'decision-record.template.json': json.dumps(template, indent=2) + '\n',
                   'DECISION-RECORD.template.md': rules.render(template),
                   'tools/synthesis_rules.py': (HERE / 'synthesis_rules.py').read_text(),
                   'TASK.md': (HERE / 'brief.md').read_text(),
                   'AGENTS.md': '# Task scope\n\nFollow TASK.md. Only decision-record.json and DECISION-RECORD.md are deliverables.\n'})
    return result


def create(path):
    path.mkdir(parents=True, exist_ok=False)
    for name, source in files().items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)


def inventory(path):
    if path.is_symlink() or not path.is_dir():
        raise ValueError('physical stopped snapshot required')
    result = {}
    for directory, dirs, names in os.walk(path, followlinks=False):
        if Path(directory) == path:
            dirs[:] = [name for name in dirs if name != '.git']
            names = [name for name in names if name != '.git']
        for name in dirs + names:
            item = Path(directory) / name
            mode = item.lstat().st_mode
            relative = str(item.relative_to(path))
            if stat.S_ISDIR(mode):
                result[relative + '/'] = None
            else:
                if not stat.S_ISREG(mode) or item.stat().st_size > FILE_CAP:
                    raise ValueError('nonregular or oversized snapshot file')
                with item.open('rb') as stream:
                    content = stream.read(FILE_CAP + 1)
                if len(content) > FILE_CAP:
                    raise ValueError('snapshot file grew beyond cap')
                result[relative] = hashlib.sha256(content).hexdigest()
    return result


def expected_inventory():
    result = {}
    for name, source in files().items():
        result[name] = hashlib.sha256(source.encode()).hexdigest()
        for parent in Path(name).parents:
            if str(parent) != '.':
                result[str(parent) + '/'] = None
    return result


def evaluate(path):
    def failed(reason):
        return {'case_id': rules.CASE_ID, 'status': 'fail', 'reason': reason,
                'checks': [{'name': 'source-integrity', 'status': 'failed' if reason == 'source-integrity' else 'passed'},
                           *[{'name': key, 'status': 'failed' if reason == 'invalid-artifact' and
                              key == 'artifact-contract' else 'unknown'} for key in rules.CHECKS]]}

    try:
        before = inventory(path)
        expected = expected_inventory()
        if (set(before) - set(expected) - OUTPUTS or
                any(name not in before or before[name] != sha for name, sha in expected.items())):
            return failed('source-integrity')
    except (OSError, ValueError):
        return failed('source-integrity')
    try:
        # Only data is read. Trusted evaluator code and inputs come from this version,
        # never from the candidate tools or its git configuration.
        value = rules.strict_json((path / 'decision-record.json').read_text())
        markdown = (path / 'DECISION-RECORD.md').read_text()
        result = rules.evaluate(value, markdown, contract(), f12.L_EVIDENCE_INDEX, f12.L_BENCHMARKS)
    except (OSError, ValueError, TypeError, RecursionError):
        result = failed('invalid-artifact')
    try:
        if inventory(path) != before:
            return failed('source-integrity')
    except (OSError, ValueError):
        return failed('source-integrity')
    if 'reason' not in result:
        result['checks'].insert(0, {'name': 'source-integrity', 'status': 'passed'})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('create', 'evaluate'))
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    if args.action == 'create':
        create(args.workspace)
    else:
        result = evaluate(args.workspace)
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(result['status'] != 'pass')
