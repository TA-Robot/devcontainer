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
BASE=HERE.parent/'v1'
WORKLOAD=HERE.parent/'workloads_v1'
ROOT=HERE.parents[3]
sys.path.insert(0,str(BASE))
from evaluate import evaluate, save, digest
from runtime import decode
sys.path.insert(0,str(WORKLOAD))
from qualify import aggregate
from workloads import suite

NOTICE='Under-development features enabled: code_mode. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /codex/config.toml.'


class StopRequested(RuntimeError):pass


def identity():
    files=[*sorted(HERE.glob('*.py')),HERE/'PROMPT.md',HERE/'policy.json',HERE/'model-catalog.json',HERE/'Actor.Dockerfile',HERE/'image.json',WORKLOAD/'solo-protocol.md',WORKLOAD/'WORKLOAD.md',WORKLOAD/'workloads.py',WORKLOAD/'qualify.py',WORKLOAD/'qualification.json',BASE/'runtime.py',BASE/'transport.py',BASE/'evaluate.py',BASE/'TASK.md',BASE/'calibration/fifo.py']
    return {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in files}


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


def actor(output, public, *, auth=None, fake=False, seconds=1800):
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    work=output/'work';work.mkdir()
    policy=output/'policy';policy.mkdir()
    for name in ('policy.json','model-catalog.json'):shutil.copyfile(HERE/name,policy/name)
    prompt=output/'prompt.private.txt';prompt.write_bytes((HERE/'PROMPT.md').read_bytes())
    image=decode((HERE/'image.json').read_bytes())
    if digest((HERE/'Actor.Dockerfile').read_bytes())!=image['dockerfile_sha256']:raise ValueError('image source changed')
    name='scheduling-solo-'+uuid.uuid4().hex
    record={'status':'started','container':name,'removed':False,'usage':None,'image':image['image']}
    save(output/'start.json',record)
    args=['docker','create','-i','--name',name,'--init','--network','none' if fake else 'bridge','--read-only',
          '--cap-drop','ALL','--security-opt','no-new-privileges','--security-opt','seccomp=unconfined',
          '--pids-limit','256','--memory','2g','--cpus','2',
          '--user',f'{os.getuid()}:{os.getgid()}','--log-driver','none','--tmpfs','/codex:rw,nosuid,nodev,size=64m,mode=1777',
          '--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777',
          '--mount',f'type=bind,src={public.resolve()},dst=/public,readonly',
          '--mount',f'type=bind,src={work.resolve()},dst=/work',
          '--mount',f'type=bind,src={policy.resolve()},dst=/policy,readonly']
    if fake:args+=['--mount',f'type=bind,src={HERE / "capability.py"},dst=/probe.py,readonly']
    elif auth:args+=['--mount',f'type=bind,src={auth.resolve()},dst=/codex/auth.json,readonly']
    else:raise ValueError('live credential required')
    args+=[image['image']]+(['python3','/probe.py'] if fake else capability.argv(HERE)+['-'])
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
        if code!=0 or parsed['usage']['output_tokens']>60000:raise ValueError('provider/cost failure')
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


def run(output, auth=None, *, fake=False):
    if not fake:
        checked=decode((HERE/'validation.json').read_bytes())
        if checked['source_sha256']!=identity() or checked['status']!='passed':raise ValueError('source-matched preflight required')
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    credential=output/'auth.json'
    report={'kind':'scheduling-strong-solo-calibration-v1','status':'running','runs':[],
            'execution':'provider-free' if fake else 'live',
            'confirmation_executed':False,'collaboration_effect_measured':False}
    began=time.monotonic();interrupted=[]
    def stop(signum,frame):
        if not interrupted:interrupted.append(signum);raise StopRequested('controller signal')
    handlers={s:signal.signal(s,stop) for s in (signal.SIGINT,signal.SIGTERM)}
    try:
        sys.path.insert(0,str(ROOT/'scripts'))
        from agent_duration_live import _validate_provider_credential_window
        if not fake:
            source=_validate_provider_credential_window('codex',auth,timeout_seconds=6120)
            shutil.copyfile(source,credential);credential.chmod(0o600)
        projection_hash=projection.prepare(output/'public')
        sealed=identity();save(output/'seal.json',{'source_sha256':sealed,'public_sha256':projection_hash,'runs':2,'seconds_per_run':1800,'output_tokens_per_run':60000,'outer_seconds':6120})
        targets=decode((WORKLOAD/'qualification.json').read_bytes())['targets']['qualification']
        for index in range(2):
            if identity()!=sealed or time.monotonic()-began>3060*index+60:raise ValueError('source or outer reservation')
            folder=output/f'run-{index+1}'
            record=actor(folder,output/'public',auth=credential if not fake else None,fake=fake)
            row={'actor':record,'status':'unmeasured'};report['runs'].append(row)
            if record['status']!='completed' or record['development_seconds']>1800:break
            try:sha=submission(folder/'work',folder/'submission.py')
            except (OSError,ValueError) as e:
                row.update(status='not-attained',submission_failure=type(e).__name__)
                save(folder/'outcome.json',row)
                continue
            row['submission_sha256']=sha
            # Assessment is a separate bounded controller process, so the total cap
            # includes all scenarios and their cleanup rather than only each call.
            data=folder/'qualification.private.json';data.write_text(json.dumps(suite('qualification')))
            evaluation=folder/'assessment';row['assessment_started']=True
            p=subprocess.Popen([sys.executable,str(BASE/'evaluate.py'),'--candidate',str(folder/'submission.py'),
                    '--scenarios',str(data),'--output',str(evaluation)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:p.communicate(timeout=1200)
            except (StopRequested,subprocess.TimeoutExpired):
                p.terminate()
                try:p.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    p.kill();p.communicate(timeout=3)
                row['assessment_cleanup_unknown']=not (evaluation/'result.json').exists()
                if not row['assessment_cleanup_unknown']:
                    row['assessment']=decode((evaluation/'result.json').read_bytes())
                raise ValueError('independent assessment interrupted')
            raw=decode((evaluation/'result.json').read_bytes());row['assessment']=raw
            if (p.returncode!=0 or not raw.get('all_containers_removed') or len(raw['cases'])!=24
                    or any(r['status']=='unmeasured' for r in raw['cases'])):break
            if any(r['status']=='invalid-policy' for r in raw['cases']):
                row.update(status='not-attained',invalid_cases=[r['id'] for r in raw['cases'] if r['status']=='invalid-policy'])
                save(folder/'outcome.json',row)
                continue
            observed=aggregate(raw);row['observed']=observed
            row['unmet']=[{'family':f,'metric':m,'value':v,'target':targets[f][m]} for f,metrics in observed.items() for m,v in metrics.items() if v>targets[f][m]]
            row['status']='attained' if not row['unmet'] else 'not-attained'
            save(folder/'outcome.json',row)
            if time.monotonic()-began>6120:raise ValueError('outer deadline')
        report['status']='completed' if len(report['runs'])==2 and all(r['status'] in ('attained','not-attained') for r in report['runs']) else 'withhold'
    except (StopRequested,OSError,ValueError,KeyError,subprocess.SubprocessError) as e:
        report.update(status='withhold',failure=type(e).__name__+': '+str(e))
    finally:
        if credential.exists():credential.unlink()
        report['credential_copy_removed']=not credential.exists()
        report['all_recorded_containers_removed']=all(r['actor']['removed'] and (
            r.get('assessment',{}).get('all_containers_removed',False) if r.get('assessment_started') else True
            ) for r in report['runs'])
        report['elapsed_seconds']=time.monotonic()-began
        save(output/'result.json',report)
        for s,h in handlers.items():signal.signal(s,h)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--auth',required=True,type=Path);a=p.parse_args()
    print(json.dumps({'status':run(a.output,a.auth)['status']}))
