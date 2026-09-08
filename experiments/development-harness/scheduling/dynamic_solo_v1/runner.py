"""Finite strong-solo developer runs and independent scheduling assessment."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

import capability
import projection

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'dynamic_v1'
ROOT=HERE.parents[3]
sys.path.insert(0,str(BASE))
from evaluate import evaluate, save, digest
from runtime import decode

NOTICE='Under-development features enabled: code_mode. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /codex/config.toml.'


class StopRequested(RuntimeError):pass



def capture(args, seconds, prompt, folder):
    process=None;started=time.monotonic();total=0
    try:
        with (folder/'stdout.private.jsonl').open('xb') as stdout, (folder/'stderr.private.txt').open('xb') as stderr, prompt.open('rb') as source:
            process=subprocess.Popen(args,stdin=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            with selectors.DefaultSelector() as selector:
                for stream in (process.stdout,process.stderr):
                    os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ)
                while selector.get_map() or process.poll() is None:
                    if time.monotonic()-started>seconds:raise TimeoutError('developer deadline')
                    for key,_ in selector.select(.05):
                        chunk=os.read(key.fd,65536)
                        if not chunk:selector.unregister(key.fileobj);continue
                        total+=len(chunk)
                        if total>16777216:raise ValueError('developer output cap')
                        target=stdout if key.fileobj is process.stdout else stderr
                        target.write(chunk);target.flush()
            return process.returncode
    finally:
        if process:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait(timeout=3)
            process.stdout.close();process.stderr.close()


def parse(events):
    usage=None;messages=[];commands=0
    for line in events.splitlines():
        event=decode(line)
        if not isinstance(event,dict):raise ValueError('CLI event shape')
        kind=event.get('type')
        if usage is not None:raise ValueError('events after completed turn')
        if kind in ('thread.started','turn.started'):continue
        if kind in ('item.started','item.updated','item.completed'):
            item=event.get('item')
            if not isinstance(item,dict):raise ValueError('CLI item shape')
            itype=item.get('type')
            if itype not in ('agent_message','reasoning','command_execution','file_change','error'):
                raise ValueError('unexpected tool or agent event')
            if itype=='error' and item.get('message')!=NOTICE:raise ValueError('unknown CLI error')
            if kind=='item.completed' and itype=='agent_message':messages.append(item['text'])
            if kind=='item.completed' and itype=='command_execution':
                command=item.get('command','')
                if re.search(r'\bcodex\s+(?:exec|resume|app-server)|\b(?:claude|grok)\b|api\.openai\.com|chatgpt\.com/backend-api',command):
                    raise ValueError('possible additional model invocation')
                commands+=1
        elif kind=='turn.completed':
            raw=event.get('usage')
            if not isinstance(raw,dict) or any(type(raw.get(k)) is not int or raw[k]<0 for k in ('input_tokens','cached_input_tokens','output_tokens')):raise ValueError('unknown usage')
            usage={k:raw[k] for k in ('input_tokens','cached_input_tokens','output_tokens')}
        else:raise ValueError('failed/unknown CLI event')
    if usage is None or not messages:raise ValueError('completed response required')
    return {'usage':usage,'commands':commands,'final':messages[-1]}


def actor(output, public, *, auth=None, fake=False, seconds=2400, actor_source=None):
    actor_root=actor_source or HERE
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    work=output/'work';work.mkdir()
    policy=output/'policy';policy.mkdir()
    for name in ('policy.json','model-catalog.json'):shutil.copyfile(actor_root/name,policy/name)
    prompt=output/'prompt.private.txt';prompt.write_bytes((actor_root/'PROMPT.md').read_bytes())
    image=decode((actor_root/'image.json').read_bytes())
    if digest((actor_root/'Actor.Dockerfile').read_bytes())!=image['dockerfile_sha256']:raise ValueError('image source changed')
    name='scheduling-solo-'+uuid.uuid4().hex
    record={'status':'started','container':name,'removed':False,'usage':None,'image':image['image']}
    save(output/'start.json',record)
    args=['docker','create','-i','--name',name,'--init','--network','none' if fake else 'bridge','--read-only',
          '--cap-drop','ALL','--security-opt','no-new-privileges','--security-opt','seccomp=unconfined',
          '--pids-limit','256','--memory','2g','--cpus','1',
          '--user',f'{os.getuid()}:{os.getgid()}','--log-driver','none','--tmpfs','/codex:rw,nosuid,nodev,size=64m,mode=1777',
          '--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777',
          '--mount',f'type=bind,src={public.resolve()},dst=/public,readonly',
          '--mount',f'type=bind,src={work.resolve()},dst=/work',
          '--mount',f'type=bind,src={policy.resolve()},dst=/policy,readonly']
    if fake:args+=['--mount',f'type=bind,src={actor_root / "capability.py"},dst=/probe.py,readonly']
    elif auth:args+=['--mount',f'type=bind,src={auth.resolve()},dst=/codex/auth.json,readonly']
    else:raise ValueError('live credential required')
    args+=[image['image']]+(['python3','/probe.py'] if fake else capability.argv(actor_root)+['-'])
    began=time.monotonic()
    try:
        subprocess.run(args,capture_output=True,check=True,timeout=15)
        code=capture(['docker','start','-ai',name],seconds-(time.monotonic()-began),prompt,output)
        record['returncode']=code
        events=(output/'stdout.private.jsonl').read_text()
        if fake:
            value=decode(events);record['capability']=value
            if (value['exit_code']!=0 or not value['broken_detected'] or not value['repair_passed']
                    or not value['shell_network_denied'] or not value['surfaces']
                    or any(s['subagent_available'] or not s['shell_available'] for s in value['surfaces'])):
                raise ValueError('capability CLI failed')
            parsed=parse(value['events'])
        else:parsed=parse(events)
        record.update(parsed)
        if code!=0 or parsed['usage']['output_tokens']>80000:raise ValueError('provider/cost failure')
        record['status']='completed'
    except (StopRequested,TimeoutError,OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as e:
        record.update(status='stopped',failure=type(e).__name__)
    finally:
        record['development_seconds']=time.monotonic()-began
        cleanup=time.monotonic()
        try:record['removed']=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15).returncode==0
        except (OSError,subprocess.SubprocessError):pass
        record['cleanup_seconds']=time.monotonic()-cleanup
        if not record['removed']:record['status']='stopped'
        save(output/'actor.json',record)
    return record


def submission(work, output):
    fd=os.open(work/'submission.py',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise ValueError('regular submission required')
        code=f.read(65537)
    if not 0<len(code)<=65536:raise ValueError('submission size')
    output.write_bytes(code)
    return digest(code)


def identity():
    files = [*HERE.glob('*.py'), *[HERE/n for n in ('PROMPT.md', 'TASK.md', 'protocol.md', 'policy.json', 'model-catalog.json', 'Actor.Dockerfile', 'image.json')],
             *[BASE/n for n in ('runtime.py', 'transport.py', 'evaluate.py', 'workloads.py', 'TASK.md', 'policies/reference.py')],
             ROOT/'scripts/agent_duration_live.py']
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(files)}


def assess(candidate, cases, output, base):
    data = output.with_suffix('.cases.private.json'); save(data, cases)
    p = subprocess.Popen([sys.executable, str(base/'evaluate.py'), '--candidate', str(candidate),
        '--scenarios', str(data), '--output', str(output)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        p.communicate(timeout=900)
    finally:
        if p.poll() is None:
            p.terminate()
            try: p.communicate(timeout=30)
            except subprocess.TimeoutExpired: p.kill(); p.communicate(timeout=3)
    raw = decode((output/'result.json').read_bytes()); seal = decode((output/'seal.json').read_bytes())
    expected = {n: digest((base/n).read_bytes()) for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
    if (seal['source_sha256'] != expected or seal['candidate_sha256'] != digest(candidate.read_bytes())
            or seal['scenario_sha256'] != digest(json.dumps(cases, sort_keys=True, allow_nan=False).encode())):
        raise ValueError('assessment source mismatch')
    if (p.returncode != 0 or not raw.get('all_containers_removed') or len(raw['cases']) != len(cases)
            or {r['id'] for r in raw['cases']} != {c['id'] for c in cases}
            or any(r['status'] not in ('measured', 'invalid-policy') for r in raw['cases'])):
        raise ValueError('incomplete assessment')
    return raw


def run(output, auth=None, *, fake=False):
    initial = identity()
    if not fake:
        validated = decode((HERE/'validation.json').read_bytes())
        if validated['status'] != 'passed' or validated['source_sha256'] != initial:
            raise ValueError('source-matched preflight required')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'kind': 'dynamic-strong-solo-profile-v1', 'status': 'withhold', 'execution': 'provider-free' if fake else 'live',
              'actor_started': False, 'assessments': {}, 'confirmation_executed': False, 'collaboration_effect_measured': False}
    credential = output/'auth.json'; began = time.monotonic(); interrupted = []
    def stop(signum, frame):
        if not interrupted: interrupted.append(signum); raise StopRequested('controller interrupted')
    handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        # Seal a complete source tree and use it for projection, actor inputs and scoring.
        frozen = output/'source'
        for name, expected in initial.items():
            data = (ROOT/name).read_bytes()
            if digest(data) != expected: raise ValueError('source changed during snapshot')
            target = frozen/name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data); target.chmod(0o444)
        actor_root = frozen/HERE.relative_to(ROOT); base = frozen/BASE.relative_to(ROOT)
        public_hash = projection.prepare(output/'public', base=base, actor=actor_root)
        save(output/'seal.json', {'source_sha256': initial, 'public_sha256': public_hash, 'live_starts': 1,
             'development_seconds': 2400, 'output_tokens': 80000, 'assessment_seconds_each': 900, 'outer_seconds': 4500})
        if not fake:
            sys.path.insert(0, str(ROOT/'scripts'))
            from agent_duration_live import _validate_provider_credential_window
            ready = _validate_provider_credential_window('codex', auth, timeout_seconds=4500)
            shutil.copyfile(ready, credential); credential.chmod(0o600)
        if time.monotonic()-began > 60: raise ValueError('preparation reservation exceeded')
        report['actor_started'] = True
        report['actor'] = actor(output/'developer', output/'public', auth=credential if not fake else None,
                                fake=fake, seconds=180 if fake else 2400, actor_source=actor_root)
        if report['actor']['status'] != 'completed' or report['actor']['development_seconds'] > (180 if fake else 2400): raise ValueError('developer incomplete')
        try: report['submission_sha256'] = submission(output/'developer/work', output/'submission.py')
        except (OSError, ValueError) as error:
            report.update(status='no-valid-submission', failure=type(error).__name__)
            return report
        cases = projection.probe() if fake else projection.cases(base, 'qualification')
        reference = output/'reference.py'
        reference.write_bytes(b"MODE = 'lookahead'\n"+(base/'policies/reference.py').read_bytes())
        for name, candidate in [('submission', output/'submission.py'), ('reference', reference)]:
            report['assessments'][name] = {'status': 'started', 'cleanup': 'unknown'}
            raw = assess(candidate, cases, output/f'assessment-{name}', base)
            report['assessments'][name] = {'status': raw['status'], 'cleanup': 'confirmed', 'result': raw}
            if name == 'reference' and raw['status'] != 'completed': raise ValueError('reference failed')
        if any(digest((frozen/n).read_bytes()) != h for n, h in initial.items()):
            raise ValueError('frozen source changed')
        if time.monotonic()-began > 4500: raise ValueError('outer deadline')
        report['status'] = 'completed' if report['assessments']['submission']['status'] == 'completed' else 'invalid-policy'
    except (StopRequested, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        report['failure'] = type(error).__name__+': '+str(error)
    finally:
        if credential.exists(): credential.unlink()
        report['credential_copy_removed'] = not credential.exists()
        report['owned_cleanup_confirmed'] = (report.get('actor', {}).get('removed') is True
            and all(r['cleanup'] == 'confirmed' for r in report['assessments'].values()))
        report['elapsed_seconds'] = time.monotonic()-began
        save(output/'result.json', report)
        for s, h in handlers.items(): signal.signal(s, h)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--auth', required=True, type=Path); a = p.parse_args()
    result = run(a.output, a.auth)
    print(json.dumps({'status': result['status']}))
    sys.exit(0 if result['status'] in ('completed', 'invalid-policy', 'no-valid-submission') else 1)
