"""Provider-free F04-L suitability audit. Never use host evaluation on live artifacts."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import agent_duration_fixtures as fixtures

CASE_ID = 'F04-L-PYBASH-001'
CATALOG = ROOT / 'experiments/multi-agent-duration/catalog/families/f04.json'
CAPSULE = ROOT / 'experiments/multi-agent-duration/capsules/f04-l-python-bash-restart.md'
PROBES = ('fresh-process-idempotence', 'argument-boundaries', 'invalid-state-preservation',
          'atomic-replacement-visible-to-reader')


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('historical source changed; recalibrate candidate construction')
    return source.replace(old, new, 1)


def replace_save(source, implementation):
    start = source.index('def save_state(')
    end = source.index('\n\ndef enqueue(', start)
    return source[:start] + implementation.rstrip() + source[end:]


def candidates():
    good = fixtures.L_GOOD
    alternative = copy.deepcopy(good)
    alternative['queue_store.py'] = replace_save(good['queue_store.py'], '''def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="queue-stage-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(state, ensure_ascii=False, indent=2) + "\\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
''')
    inplace = copy.deepcopy(good)
    inplace['queue_store.py'] = replace_save(good['queue_store.py'], '''def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state) + "\\n", encoding="utf-8")
''')
    split = copy.deepcopy(good)
    split['bin/queuectl'] = replace_once(good['bin/queuectl'], '"$@"', '$*')
    swallow = copy.deepcopy(good)
    swallow['bin/queuectl'] = replace_once(good['bin/queuectl'],
        'exec python3 "$script_dir/../queue_cli.py" "$@"',
        'python3 "$script_dir/../queue_cli.py" "$@" || true')
    malformed = copy.deepcopy(good)
    malformed['queue_store.py'] = replace_once(good['queue_store.py'],
        '    state = json.loads(path.read_text(encoding="utf-8"))',
        '    try:\n        state = json.loads(path.read_text(encoding="utf-8"))\n'
        '    except json.JSONDecodeError:\n        return {"version": 1, "items": {}}')
    unsorted = copy.deepcopy(good)
    unsorted['queue_store.py'] = replace_once(good['queue_store.py'], '    return sorted(', '    return list(')
    # The reference serializer sorts object keys too; removing only sorted(pending)
    # would still satisfy the contract, so preserve insertion order in this mutant.
    unsorted['queue_store.py'] = replace_once(unsorted['queue_store.py'], 'sort_keys=True', 'sort_keys=False')
    recipe = fixtures.RECIPES['f04-l-python-bash-restart-v2']
    return [
        ('known-good', copy.deepcopy(good), 'pass', []),
        ('alternate-atomic-writer', alternative, 'pass', []),
        ('in-place-truncating-write', inplace, 'pass', ['atomic-replacement-visible-to-reader']),
        ('wrapper-splits-arguments', split, 'pass', ['argument-boundaries']),
        ('wrapper-first-argument', copy.deepcopy(recipe['mutants']['wrapper-first-argument']['files']),
         'fail', ['fresh-process-idempotence']),
        ('repeat-ack-increments', copy.deepcopy(recipe['mutants']['repeat-ack-increments']['files']),
         'fail', ['fresh-process-idempotence']),
        ('wrapper-swallows-status', swallow, 'fail', ['invalid-state-preservation']),
        ('malformed-state-overwritten', malformed, 'fail', ['invalid-state-preservation']),
        ('unsorted-pending', unsorted, 'fail', ['fresh-process-idempotence']),
    ]


def run_queue(workspace, store, *arguments):
    # Candidate set above is maintained audit code, not provider output. Use a clean
    # environment and a fresh process; no inherited credentials or PYTHONPATH.
    return subprocess.run([str(workspace / 'bin/queuectl'), '--store', str(store), *arguments],
        cwd=store.parent, env={'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
        'HOME': '/nonexistent', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
        'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True, timeout=5)


def observe(workspace, probe):
    with tempfile.TemporaryDirectory(prefix='f04-observation-') as raw:
        parent = Path(raw)
        if probe == 'argument-boundaries':
            parent = parent / 'store folder 空白'
            parent.mkdir()
        store = parent / 'queue.json'
        observations = []

        def command(*args):
            result = run_queue(workspace, store, *args)
            observations.append({'command': list(args), 'returncode': result.returncode,
                                 'stdout': result.stdout})
            return result

        def require(condition):
            if not condition:
                raise ValueError('behavioral requirement failed')

        try:
            if probe == 'argument-boundaries':
                item, payload = 'item with space', 'payload "quoted" 日本語\nsecond line'
                require(command('enqueue', item, payload).returncode == 0)
                state = json.loads(store.read_text())
                require(state['items'][item]['payload'] == payload)
                require(command('pending').stdout == item + '\n')
                require(command('ack', item).returncode == 0)
                require(command('pending').stdout == '')
            elif probe == 'fresh-process-idempotence':
                require(command('enqueue', 'z-item', 'second').returncode == 0)
                require(command('enqueue', 'a-item', 'first').returncode == 0)
                require(command('pending').stdout == 'a-item\nz-item\n')
                require(command('ack', 'a-item').returncode == 0)
                before = store.read_bytes()
                require(command('ack', 'a-item').returncode == 0)
                require(store.read_bytes() == before)
                require(json.loads(before)['items']['a-item']['ack_count'] == 1)
                require(command('pending').stdout == 'z-item\n')
            elif probe == 'invalid-state-preservation':
                require(command('enqueue', 'kept', 'value').returncode == 0)
                before = store.read_bytes()
                require(command('ack', 'missing').returncode == 4)
                require(store.read_bytes() == before)
                store.write_bytes(b'{broken-json\n')
                before = store.read_bytes()
                require(command('enqueue', 'new', 'value').returncode != 0)
                require(store.read_bytes() == before)
            elif probe == 'atomic-replacement-visible-to-reader':
                require(command('enqueue', 'kept', 'value').returncode == 0)
                before = store.read_bytes()
                # An independently open descriptor must retain the complete old version
                # while the path switches to the new version. No source hooks/sleeps.
                with store.open('rb', buffering=0) as reader:
                    require(command('ack', 'kept').returncode == 0)
                    retained = reader.read()
                after = store.read_bytes()
                observations.append({'old_reader_retained_bytes': retained == before,
                                     'path_changed': after != before})
                require(retained == before and after != before)
                state = json.loads(after)
                require(state['items']['kept']['acknowledged'] is True)
                require(state['items']['kept']['ack_count'] == 1)
            else:
                raise ValueError('unknown probe')
        except (ValueError, KeyError, OSError) as exc:
            return {'probe': probe, 'status': 'fail', 'reason': type(exc).__name__, 'observations': observations}
        except subprocess.TimeoutExpired:
            return {'probe': probe, 'status': 'unknown', 'reason': 'command-timeout', 'observations': observations}
    return {'probe': probe, 'status': 'pass', 'observations': observations}


def historical_observations():
    source = ROOT / 'generated/duration-atlas/current.json'
    atlas = json.loads(source.read_text())
    rows = []
    for series in atlas['series']:
        for case in series['cases']:
            if case['primary_stratum']['case']['case_id'] != CASE_ID:
                continue
            configuration = case['primary_stratum']['configuration']
            for sample in case['samples']:
                rows.append({'run_id': sample['run_id'], 'configuration': configuration,
                             'quality_population': sample['quality_population'],
                             'score': sample.get('quality_evidence', {}).get('score'),
                             'artifact_auditability': sample.get('artifact_auditability')})
    return {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'records': rows,
            'interpretation': 'Historical full scores concern the original checks only; artifacts are not rescored.'}


def audit():
    started = time.monotonic()
    records = []
    for label, sources, expected_old, expected_failures in candidates():
        with tempfile.TemporaryDirectory(prefix='f04-audit-') as raw:
            path = Path(raw) / 'fixture'
            manifest = fixtures.build_fixture(CASE_ID, path, catalog_path=CATALOG,
                fixture_id='f04-suitability-' + label, now=datetime(2026, 9, 6, tzinfo=timezone.utc))
            if manifest['case']['revision'] != 1:
                raise ValueError('audit requires the historical revision 1')
            workspace = path / 'workspace'
            for name, source in sources.items():
                (workspace / name).write_text(source)
            old = fixtures.evaluate_fixture(path)
            probes = [observe(workspace, probe) for probe in PROBES]
            failures = [p['probe'] for p in probes if p['status'] == 'fail']
            # Defects may affect several behaviors; require the intended failure and
            # accept no unknown. Both valid implementations must pass every probe.
            matched = (old['status'] == expected_old and all(p['status'] != 'unknown' for p in probes)
                       and set(expected_failures) <= set(failures)
                       and (bool(expected_failures) or not failures))
            records.append({'candidate': label, 'expected_historical_status': expected_old,
                            'required_probe_failures': expected_failures,
                            'status': 'pass' if matched else 'fail', 'historical_score': old['score'],
                            'supplementary_probes': probes,
                            'candidate_sha256': {k: hashlib.sha256(v.encode()).hexdigest() for k, v in sources.items()}})
    return {'kind': 'provider-free-f04-lifecycle-suitability-audit', 'case_id': CASE_ID, 'revision': 1,
            'status': 'pass' if all(r['status'] == 'pass' for r in records) else 'fail',
            'live_provider_calls': 0, 'historical_scores_overwritten': False,
            'unmodified_task_admitted': False, 'supplementary_probes_are_new_historical_scores': False,
            'scope': 'normal process restart, argument boundaries and observable atomic replacement',
            'unmeasured': ['process kill during write', 'power-loss durability', 'concurrent writers',
                           'multi-agent benefit'],
            'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__).resolve(), Path(fixtures.__file__), CATALOG, CAPSULE)},
            'historical_observations': historical_observations(), 'records': records,
            'duration_seconds': time.monotonic() - started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        result = audit()
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'candidates': len(result['records'])}))
    raise SystemExit(result['status'] != 'pass')
