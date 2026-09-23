"""Actual pinned Codex request/tools and synthetic tool execution; run in Docker."""
import http.server
import json
from pathlib import Path
import subprocess
import shlex
import threading


def argv(policy_root=Path('/policy')):
    args=['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral',
          '--skip-git-repo-check','--json','--model','gpt-6-astra',
          '-c','model_reasoning_effort="high"','-c','model_catalog_json="/policy/model-catalog.json"']
    for key,value in json.loads((policy_root/'policy.json').read_text()).items():
        args+=['-c',key+'='+json.dumps(value)]
    return args


def main():
    requests=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            message={'id':'msg_test','type':'message','role':'assistant',
                     'content':[{'type':'output_text','text':'capability complete'}]}
            if len(requests)<=3:
                if len(requests)==1:
                    command = "echo 'print(dict())' > /work/broken.py && python3 /public/public_check.py --candidate /work/broken.py --cases /public/probe.json --output /work/broken-report.json"
                elif len(requests)==2:
                    command = "cp /public/fifo.py /work/submission.py && python3 /public/public_check.py --candidate /work/submission.py --cases /public/probe.json --output /work/repaired-report.json"
                else:
                    script = ('import socket,json\nfrom pathlib import Path\n'
                        'try:\n s=socket.create_connection(("127.0.0.1",'+str(server.server_port)+'),timeout=1);s.close();denied=False\n'
                        'except OSError:\n denied=True\n'
                        'Path("/work/network-denied.json").write_text(json.dumps({"denied":denied}))\n')
                    command = 'python3 -c '+shlex.quote(script)
                message={'id':'tool_'+str(len(requests)),'type':'custom_tool_call','call_id':'call_'+str(len(requests)),
                         'name':'exec','namespace':'functions',
                         'input':'text(await tools.exec_command('+json.dumps({'cmd':command,'yield_time_ms':10000})+'));'}
            events=[{'type':'response.created','response':{'id':'resp_test_'+str(len(requests))}},
                    {'type':'response.output_item.done','output_index':0,'item':message},
                    {'type':'response.completed','response':{'id':'resp_test_'+str(len(requests)),'status':'completed','output':[message],
                     'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25,'input_tokens_details':{'cached_tokens':0}}}}]
            data=''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=http.server.HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    args=argv()+['-c','model_provider="local_probe"','-c','model_providers.local_probe.name="local probe"',
          '-c',f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
          '-c','model_providers.local_probe.wire_api="responses"','-c','model_providers.local_probe.requires_openai_auth=false','-']
    try:result=subprocess.run(args,input='Return a brief final response.',text=True,capture_output=True,timeout=90)
    finally:server.shutdown();server.server_close()
    surfaces=[]
    for request in requests:
        groups=[g for item in request.get('input',[]) if item.get('type')=='additional_tools' for g in item.get('tools',[])]
        names=[g.get('name')+'.'+t.get('name') for g in groups for t in g.get('tools',[])]
        descriptions='\n'.join(t.get('description','') for g in groups for t in g.get('tools',[]))
        surfaces.append({'names':names,'shell_available':'### `exec_command`' in descriptions,
                         'subagent_available':any('spawn_agent' in n for n in names) or '### `spawn_agent`' in descriptions})
    def report(name):
        path=Path('/work')/name
        return json.loads(path.read_text()) if path.exists() else None
    broken,repaired=report('broken-report.json'),report('repaired-report.json')
    print(json.dumps({'exit_code':result.returncode,'requests':len(requests),'surfaces':surfaces,
        'broken_detected':bool(broken and not broken['valid']),
        'repair_passed':bool(repaired and repaired['valid']),
        'shell_network_denied':bool(report('network-denied.json') and report('network-denied.json')['denied']),
        'tool_outputs':[[i for i in r.get('input',[]) if 'output' in i.get('type','')] for r in requests],'events':result.stdout,'diagnostic':result.stderr[-3000:]}))


if __name__=='__main__':main()
