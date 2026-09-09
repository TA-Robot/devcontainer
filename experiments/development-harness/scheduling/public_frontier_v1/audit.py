"""Read developer-owned public reports; never execute candidates or grade anew."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f'not a regular file: {path}')
        return stream.read()


def save(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def metrics(report, cases):
    """Validate complete comparable primary metrics, ignoring reported totals."""
    if report.get('valid') is not True:
        raise ValueError('report not valid')
    rows = report.get('cases', [])
    if len(rows) != len(cases) or {r['id'] for r in rows} != set(cases):
        raise ValueError('missing or duplicate cases')
    result = {}
    for row in rows:
        value = row['result']
        if row['status'] != 'measured' or value.get('status') != 'completed':
            raise ValueError('unmeasured case')
        scenario = cases[row['id']]
        offered = sum(j['weight'] for j in scenario['jobs'])
        if type(value['offered_value']) is not int or value['offered_value'] != offered:
            raise ValueError('offered value mismatch')
        counts = {}
        for weight in (1, 4, 16):
            service = value['service_classes'][str(weight)]
            total = sum(j['weight'] == weight for j in scenario['jobs'])
            if type(service['total']) is not int or service['total'] != total:
                raise ValueError('service population mismatch')
            count = service['on_time']
            if type(count) is not int or not 0 <= count <= total:
                raise ValueError('invalid service count')
            counts[weight] = count
        on_time = value['on_time_value']
        if type(on_time) is not int or on_time != sum(k * v for k, v in counts.items()):
            raise ValueError('on-time value and class counts disagree')
        result[row['id']] = {'value': on_time, 'critical': counts[16]}
    return result


def summarize(records, baseline):
    """Independent objective ceilings: do not claim a joint attainable policy."""
    groups = {'all': sorted(baseline)}
    for case_id in sorted(baseline):
        _, band, family, _ = case_id.split('-')
        groups.setdefault(band, []).append(case_id)
        groups.setdefault(band + '/' + family, []).append(case_id)
    result = {}
    for group, ids in groups.items():
        totals = {name: {m: sum(rows[i][m] for i in ids) for m in ('value', 'critical')}
                  for name, rows in records.items()}
        reference = {m: sum(baseline[i][m] for i in ids) for m in ('value', 'critical')}
        ceiling = ({m: sum(max(rows[i][m] for rows in records.values()) for i in ids)
                    for m in ('value', 'critical')} if records else None)
        nondominated = [name for name, v in totals.items() if not any(
            all(other[m] >= v[m] for m in v) and any(other[m] > v[m] for m in v)
            for other in totals.values())]
        result[group] = {'case_count': len(ids), 'solo_selected': reference,
                         'candidate_totals': totals, 'nondominated_records': nondominated,
                         'separate_objective_ceiling': ceiling,
                         'ceiling_minus_solo': ({m: ceiling[m] - reference[m] for m in reference}
                                                if ceiling is not None else None)}
    return result


def audit(original, output):
    original = original.resolve()
    output = output.resolve()
    if output == original or original in output.parents:
        raise ValueError('output must be outside original run')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    files = {}

    def read(relative):
        data = read_regular(original / relative)
        sha = digest(data)
        if relative in files and files[relative] != sha:
            raise ValueError('input changed during audit')
        files[relative] = sha
        return data

    public_bytes = read('public/development.json')
    public = json.loads(public_bytes)
    cases = {c['id']: c for c in public}
    expected_ids = {f'development-{b}-{f}-{s}' for b in ('ordinary', 'contended', 'severe')
                    for f in ('burst', 'scarce', 'cache', 'mixed') for s in (0, 1)}
    if len(public) != 24 or set(cases) != expected_ids:
        raise ValueError('requires original public 24-case coverage')
    canonical_sha = digest(json.dumps(public, sort_keys=True, separators=(',', ':')).encode())
    original_result = json.loads(read('result.json'))
    selected = {}
    selected_sha = {}
    for actor, report in (('solo', 'public_final.json'), ('adaptive', 'submission_official.json')):
        prefix = f'actors/{actor}/'
        if read(prefix + 'public/development.json') != public_bytes:
            raise ValueError('different public inputs')
        selected_sha[actor] = digest(read(prefix + 'work/submission.py'))
        selected[actor] = metrics(json.loads(read(prefix + 'work/' + report)), cases)
    if selected_sha['solo'] != original_result['submission_sha256']['solo']:
        raise ValueError('original solo submission changed')
    declaration = re.search(rb'Final source SHA256: `([0-9a-f]{64})`',
                            read('actors/adaptive/work/SELECTION.md'))
    if declaration is None or declaration[1].decode() != selected_sha['adaptive']:
        raise ValueError('adaptive declared submission changed')

    prefix = 'actors/adaptive/work/'
    work = original / prefix
    sources = {}
    for path in sorted(work.glob('*.py')):
        sha = digest(read(prefix + path.name))
        sources.setdefault(sha, []).append(path.name)
    inventory, record_metrics = {}, {}
    ignored = 0
    for path in sorted(work.glob('*.json')):
        report = json.loads(read(prefix + path.name))
        if not isinstance(report, dict) or not isinstance(report.get('cases'), list):
            ignored += 1
            continue
        ids = [r.get('id') for r in report['cases'] if isinstance(r, dict)]
        if set(ids) != expected_ids:
            ignored += 1
            continue
        row = {'report_sha256': files[prefix + path.name], 'included': False}
        inventory[path.name] = row
        try:
            measured = metrics(report, cases)
        except (KeyError, TypeError, ValueError) as exc:
            row['reason'] = type(exc).__name__ + ': ' + str(exc)
            continue
        sha = report.get('source_sha256')
        source_matches = sources.get(sha, [])
        source_bound = bool(source_matches) and report.get('source_frozen_at_run_start') is True
        input_hash = report.get('cases_sha256')
        if input_hash is not None and input_hash != canonical_sha:
            raise ValueError(f'public input hash mismatch: {path.name}')
        tier = ('input_and_source_bound' if source_bound and input_hash == canonical_sha else
                'source_bound' if source_bound else 'record_only')
        row.update(included=True, tier=tier, source_sha256=sha,
                   matching_source_files=source_matches, input_sha256=input_hash,
                   fast_identity_copy=report.get('fast_identity_copy'),
                   reason='developer record; independent execution not certified')
        record_metrics[path.name] = measured
    if not record_metrics or record_metrics.get('submission_official.json') != selected['adaptive']:
        raise ValueError('selected adaptive public record missing')
    pools = {
        'input_and_source_bound': [n for n, r in inventory.items()
                                   if r.get('tier') == 'input_and_source_bound'],
        'source_bound_including_missing_input_hash': [n for n, r in inventory.items()
                                   if r.get('tier') in ('input_and_source_bound', 'source_bound')],
        'all_complete_records_including_unbound': list(record_metrics),
    }
    source = read_regular(Path(__file__))
    (output / 'audit-source.py').write_bytes(source)
    save(output / 'plan.json', {
        'kind': 'public-record-frontier-v1', 'original': str(original),
        'source_sha256': digest(source), 'input_sha256': files,
        'inventory': inventory, 'ignored_non_full_public_reports': ignored, 'pools': pools,
        'original_status': original_result['status'], 'selected_sha256': selected_sha,
        'live_calls': 0, 'candidate_executions': 0, 'hidden_input_reads': 0,
    })
    result = {'kind': 'public-record-frontier-v1', 'status': 'completed',
              'measurement_scope': 'developer-owned public records, not independent re-evaluation',
              'ceiling_scope': 'per-case retrospective maxima for each objective separately',
              'original_status': original_result['status'], 'original_status_changed': False,
              'selected': selected, 'record_metrics': record_metrics,
              'pools': {name: summarize({n: record_metrics[n] for n in names}, selected['solo'])
                        for name, names in pools.items()}}
    for name, expected in files.items():
        if digest(read_regular(original / name)) != expected:
            raise ValueError('original input changed after analysis')
    result['all_read_inputs_unchanged'] = True
    save(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.original, args.output)
    print(json.dumps({'status': report['status'], 'pools': {
        name: rows['all']['ceiling_minus_solo'] for name, rows in report['pools'].items()}}))
