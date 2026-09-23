import json,os,subprocess
from pathlib import Path
assert not Path('/task/private').exists()
assert not Path('/home/devuser/.codex/auth.json').exists()
assert not Path('/var/run/docker.sock').exists()
for path in ('/usr/local/bin/manage-agent-project', '/usr/local/share/agent-project',
             '/usr/local/lib/agentctl', '/opt/devcontainer-ai-cli'):
 assert not Path(path).exists(), 'unexpected reference/provider in probe image: '+path
rows=[]
for candidate in sorted(Path('/task/candidates').iterdir()):
 try:
  (candidate/'manage-agent-project').write_text('mutate')
  raise AssertionError('candidate was writable')
 except OSError: pass
 base=Path('/work')/candidate.name;base.mkdir()
 source=base/'source';source.mkdir()
 target=base/'target';target.mkdir()
 (source/'settings.txt').write_text('same');(target/'settings.txt').write_text('same')
 (target/'settings.txt').chmod(0o600)
 cli=str(candidate/'manage-agent-project')
 def call(*args):
  p=subprocess.run([cli,*map(str,args),'--json'],capture_output=True,text=True,timeout=5)
  return p,json.loads(p.stdout)
 p,result=call('adopt','--source',source,'--target',target)
 adoption='acceptable' if p.returncode==0 else 'needs-repair'
 if p.returncode==0:
  assert (target/'settings.txt').stat().st_mode&0o777==0o600
  p,again=call('adopt','--source',source,'--target',target);assert p.returncode==0 and again['status']=='noop'
 # Inspect API result; neither an unrelated permission error nor a conflict is proof of rejection.
 p,plan=call('plan','--source',source,'--target','//'+str(source).lstrip('/'))
 rejected=p.returncode!=0 and plan.get('status')=='error' and 'separate trees' in plan.get('error','')
 accepted=p.returncode==0 and plan.get('status') in ('ready','conflict')
 assert rejected or accepted,(p.returncode,plan)
 boundary='acceptable' if rejected else 'needs-repair'
 rows.append({'id':candidate.name,'scopes':{'matching-adoption':adoption,'path-boundaries':boundary},
              'reason':'Calibration probe; agreement does not validate every check or free-text evidence.',
              'evidence':['probe.py']})
good=[r['id'] for r in rows if all(v=='acceptable' for v in r['scopes'].values())]
print(json.dumps({'candidates':rows,'selected':good[0] if len(good)==1 else None}))
