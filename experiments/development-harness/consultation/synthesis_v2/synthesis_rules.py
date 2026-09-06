"""Public, deterministic checks for synthesis scope v2; no candidate code execution."""
import argparse
import json
import math
from pathlib import Path
from statistics import median

CASE_ID = 'consultation-synthesis-scope-v2'
CHECKS = ('artifact-contract', 'evidence-links', 'claim-scope', 'unknown-coverage',
          'metric-integrity', 'decision-constraints', 'document-sync')


def strict_json(text):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate JSON key')
            value[key] = item
        return value

    def invalid(value):
        raise ValueError('nonfinite JSON number')

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('nonfinite JSON number')
        return number

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite)


def render(value):
    # Every structured field is visible, including scope and unknown topics.
    return ('# Structured fabric decision — scope v2\n\n'
            'The JSON below is the authoritative record. Free prose is not semantically graded.\n\n'
            '```json\n' + json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                                     allow_nan=False) + '\n```\n')


def require(value):
    if not value:
        raise ValueError('contract violation')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, nonempty=False):
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(text(item) for item in value) and len(value) == len(set(value)))


def keyed(items, key):
    require(isinstance(items, list) and 0 < len(items) <= 128)
    require(all(isinstance(item, dict) and text(item.get(key)) for item in items))
    result = {item[key]: item for item in items}
    require(len(result) == len(items))
    return result


def shape(value, contract):
    require(isinstance(value, dict) and set(value) == set(contract['record_fields']))
    require(type(value['version']) is int and value['version'] == 2)
    require(value['evaluation_contract'] == CASE_ID)
    decision = value['decision']
    require(isinstance(decision, dict) and set(decision) ==
            {'strategy', 'depends_on', 'phases', 'conditional_optimization'})
    require(text(decision['strategy']) and strings(decision['depends_on'], True))
    groups = {'claim': value['claims'], 'metric': value['metrics'], 'control': value['controls'],
              'constraint': value['constraint_matrix'], 'alternative': value['alternatives'],
              'unknown': value['unknowns'], 'refresh': value['refresh_plan'],
              'phase': decision['phases'], 'conditional_optimization': [decision['conditional_optimization']]}
    require(isinstance(decision['phases'], list))
    require(all(isinstance(p, dict) for p in decision['phases']))
    for kind, field in (('gate', 'gates'), ('rollback_trigger', 'rollback_triggers')):
        groups[kind] = []
        for phase in decision['phases']:
            require(isinstance(phase.get(field), list) and phase[field])
            groups[kind].extend(phase[field])
    list_fields = {'provenance', 'evidence', 'topics', 'eligible_only_if'}
    special = {'scope', 'sample_count', 'censored', 'valid', 'median_ms', 'exclusion_reason',
               'phase', 'gates', 'rollback_triggers', 'missing_evidence'}
    for kind, items in groups.items():
        require(isinstance(items, list) and 0 < len(items) <= 128)
        for item in items:
            require(isinstance(item, dict) and set(item) == set(contract['required_fields'][kind]))
            for field, content in item.items():
                if field in list_fields:
                    require(strings(content, field in {'provenance', 'topics', 'eligible_only_if'}))
                elif field == 'missing_evidence':
                    require(strings(content) if kind == 'claim' else text(content))
                elif field not in special:
                    require(text(content))
    for item in value['claims']:
        scope = item['scope']
        require(isinstance(scope, dict) and set(scope) == {'population', 'workloads'})
        require(text(scope['population']) and strings(scope['workloads']))
    for item in value['metrics']:
        require(type(item['sample_count']) is int and item['sample_count'] >= 0)
        require(type(item['censored']) is int and item['censored'] >= 0)
        require(type(item['valid']) is bool)
        require(item['median_ms'] is None or type(item['median_ms']) in (int, float))
        require(item['exclusion_reason'] is None or text(item['exclusion_reason']))
    for item in decision['phases']:
        require(type(item['phase']) is int and item['phase'] > 0)
    for field, key in (('claims', 'claim_id'), ('metrics', 'evidence_id'), ('controls', 'control_id'),
                       ('constraint_matrix', 'constraint_id'), ('alternatives', 'option'),
                       ('unknowns', 'unknown_id'), ('refresh_plan', 'trigger_id')):
        keyed(value[field], key)
    keyed(groups['gate'], 'gate_id')
    keyed(groups['rollback_trigger'], 'trigger_id')
    require(len({p['phase'] for p in decision['phases']}) == len(decision['phases']))


def evidence_links(value, contract, evidence):
    claims = keyed(value['claims'], 'claim_id')
    require(set(claims) == set(contract['claim_ids']))
    collections = (value['claims'], value['controls'], value['alternatives'], value['unknowns'],
                   [value['decision']['conditional_optimization']])
    for items in collections:
        for item in items:
            require(set(item['evidence']) <= set(evidence))
    paths = {entry.split('#')[0] for entry in evidence.values()}
    for claim_id, claim in claims.items():
        rule = contract['claim_evidence'][claim_id]
        require(set(rule['required_evidence']) <= set(claim['evidence']))
        require(set(claim['provenance']) <= paths and rule['provenance'] in claim['provenance'])
        require(claim['confidence'] in contract['confidence_values'])
        require(claim['disposition'] in contract['disposition_values'])
        if claim['disposition'] == 'unknown':
            require(claim['confidence'] == 'unknown' and claim['missing_evidence'])


def claim_scope(value, contract):
    for claim in value['claims']:
        expected = contract['claim_scopes'][claim['claim_id']]
        require(claim['scope']['population'] == expected['population'])
        require(set(claim['scope']['workloads']) == set(expected['workloads']))
    claims = keyed(value['claims'], 'claim_id')
    require(claims['C-THROUGHPUT']['disposition'] == 'rejected')


def unknown_coverage(value, contract):
    unknowns = value['unknowns']
    require(len(unknowns) >= contract['minimum_counts']['unknowns'])
    require(all(item['status'] == 'unknown' for item in unknowns))
    for topic, required in contract['required_unknown_topics'].items():
        matching = [item for item in unknowns if topic in item['topics']]
        require(matching)
        require(all(set(required) <= set(item['evidence']) for item in matching))
    claims = keyed(value['claims'], 'claim_id')
    for claim_id, rule in contract['required_claim_outcomes'].items():
        require(claims[claim_id]['disposition'] == rule['disposition'])
        require(claims[claim_id]['confidence'] == rule['confidence'])
        require(set(rule['required_evidence']) <= set(claims[claim_id]['evidence']))
        require(claims[claim_id]['missing_evidence'])


def metrics(value, raw):
    declared = keyed(value['metrics'], 'evidence_id')
    require(set(declared) == {item['evidence_id'] for item in raw['series']})
    for item in raw['series']:
        observed = declared[item['evidence_id']]
        for key in ('proposal', 'workload', 'censored', 'valid'):
            require(observed[key] == item[key])
        require(observed['sample_count'] == len(item['samples_ms']))
        require(observed['median_ms'] == (median(item['samples_ms']) if item['valid'] else None))
        require(observed['exclusion_reason'] == item.get('exclusion_reason'))


def decision_constraints(value, contract):
    decision = value['decision']
    phases = decision['phases']
    space = contract['decision_space']
    require(len(phases) >= contract['minimum_counts']['phases'])
    require(phases[0]['option'] == space['migration_bridge_option'])
    require(phases[-1]['option'] in space['permitted_target_options'])
    require(all(p['option'] in contract['proposal_options'] and
                p['option'] not in space['forbidden_selected_options'] for p in phases))
    claims = keyed(value['claims'], 'claim_id')
    required = set(contract['required_decision_dependencies'])
    required.update(set(space['target_evidence'][phases[-1]['option']]) & set(claims))
    require(required <= set(decision['depends_on']) <= set(claims))
    edges = {e for control in value['controls'] for e in control['evidence']}
    require(set(contract['required_control_evidence']) <= edges)
    alternatives = keyed(value['alternatives'], 'option')
    require(set(alternatives) == set(contract['proposal_options']))
    for option, refs in contract['alternative_minimum_evidence'].items():
        require(set(refs) <= set(alternatives[option]['evidence']))
    matrix = keyed(value['constraint_matrix'], 'constraint_id')
    require(set(matrix) == set(contract['constraint_ids']))
    gate_ids = {g['gate_id'] for p in phases for g in p['gates']}
    gate_ids.update(g['trigger_id'] for p in phases for g in p['rollback_triggers'])
    require(all(c['status'] in contract['constraint_status_values'] and c['gate_id'] in gate_ids
                for c in matrix.values()))
    require(decision['conditional_optimization']['option'] in contract['proposal_options'])
    require({r['category'] for r in value['refresh_plan']} == set(contract['refresh_categories']))


def evaluate(value, markdown, contract, evidence, raw):
    rows = {key: 'unknown' for key in CHECKS}
    try:
        shape(value, contract)
        rows['artifact-contract'] = 'passed'
    except (ValueError, TypeError, KeyError):
        rows['artifact-contract'] = 'failed'
    if rows['artifact-contract'] == 'passed':
        checks = {'evidence-links': lambda: evidence_links(value, contract, evidence),
                  'claim-scope': lambda: claim_scope(value, contract),
                  'unknown-coverage': lambda: unknown_coverage(value, contract),
                  'metric-integrity': lambda: metrics(value, raw),
                  'decision-constraints': lambda: decision_constraints(value, contract),
                  'document-sync': lambda: require(markdown == render(value))}
        for name, check in checks.items():
            try:
                check()
                rows[name] = 'passed'
            except (ValueError, TypeError, KeyError, IndexError):
                rows[name] = 'failed'
    return {'case_id': CASE_ID, 'status': 'pass' if all(v == 'passed' for v in rows.values()) else 'fail',
            'checks': [{'name': k, 'status': v} for k, v in rows.items()],
            'measurement_scope': 'structured-evidence-assembly', 'prose_semantics_measured': False,
            'operational_effectiveness_measured': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('render', 'check'))
    args = parser.parse_args()
    try:
        value = strict_json(Path('decision-record.json').read_text())
        if args.action == 'render':
            Path('DECISION-RECORD.md').write_text(render(value))
        else:
            result = evaluate(value, Path('DECISION-RECORD.md').read_text(),
                              strict_json(Path('decision-contract.json').read_text()),
                              strict_json(Path('evidence/index.json').read_text()),
                              strict_json(Path('evidence/benchmarks/raw.json').read_text()))
            print(json.dumps(result, ensure_ascii=False))
            raise SystemExit(result['status'] != 'pass')
    except (OSError, ValueError, TypeError, RecursionError):
        print(json.dumps({'case_id': CASE_ID, 'status': 'fail', 'reason': 'invalid-artifact'}))
        raise SystemExit(1)
