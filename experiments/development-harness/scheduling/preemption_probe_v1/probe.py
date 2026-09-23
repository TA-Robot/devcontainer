"""Synthetic native peer notification while the parent response is streaming."""
import http.server
import itertools
import json
from pathlib import Path
import subprocess
import threading
import time

from accounting import collect


def main():
    partial = threading.Event(); child_done = threading.Event()
    terminal_attempted = threading.Event()
    control = json.loads(Path('/policy/mode.json').read_text())['mode'] == 'control'
    sequence = itertools.count(1); counts = {}; requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            meta = json.loads(self.headers['x-codex-turn-metadata'])
            tid = meta['thread_id']; counts[tid] = counts.get(tid,0)+1
            step = counts[tid]; number = next(sequence); root = meta['agent_name']=='/root'
            rid = 'resp_preempt_'+str(number)
            if number > 12: raise RuntimeError('finite request cap')
            is_partial = root and step == 2
            request={'thread_id':tid,'response_id':rid,'partial':is_partial,
                     'usage':None if is_partial else {'input_tokens':20,'output_tokens':5}}
            requests.append(request)
            message={'id':'msg_'+str(number),'type':'message','role':'assistant',
                     'content':[{'type':'output_text','text':'PARTIAL' if is_partial else 'DONE'}]}
            if is_partial: message['phase']='commentary'
            if root and step==1 and control:
                message={'id':'tool_'+str(number),'type':'custom_tool_call','call_id':'call_'+str(number),
                    'name':'exec','namespace':'functions','input':'text(await tools.exec_command({cmd:"true"}));'}
            elif root and step==1:
                message={'id':'tool_'+str(number),'type':'function_call','call_id':'call_'+str(number),
                    'name':'spawn_agent','namespace':'collaboration','arguments':json.dumps({
                        'task_name':'notice','message':'Send the scripted notice.','fork_turns':'none'})}
            elif not root and step==1:
                if not partial.wait(10): raise RuntimeError('parent partial not reached')
                message={'id':'tool_'+str(number),'type':'function_call','call_id':'call_'+str(number),
                    'name':'send_message','namespace':'collaboration','arguments':json.dumps({
                        'target':'/root','message':'Synthetic peer evidence arrived.'})}
            elif not root:
                child_done.set()
            elif step==3:
                message={'id':'tool_'+str(number),'type':'custom_tool_call','call_id':'call_'+str(number),
                    'name':'exec','namespace':'functions',
                    'input':'text(await tools.exec_command({cmd:"sleep 0.2",yield_time_ms:10000}));'}
            events=[{'type':'response.created','response':{'id':rid}},
                    {'type':'response.output_item.done','output_index':0,'item':message}]
            if not is_partial:
                events.append({'type':'response.completed','response':{'id':rid,'status':'completed','output':[message],
                    'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25,'input_tokens_details':{'cached_tokens':0}}}})
            data=''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200);self.send_header('Content-Type','text/event-stream')
            if not is_partial:self.send_header('Content-Length',str(len(data)))
            else:self.send_header('Connection','close')
            self.end_headers();self.wfile.write(data);self.wfile.flush()
            if is_partial:
                partial.set()
                if not control:child_done.wait(10)
                time.sleep(.5)
                request['usage']={'input_tokens':20,'output_tokens':5}
                request['delayed_terminal_attempted']=True
                completed={'type':'response.completed','response':{'id':rid,'status':'completed','output':[message],
                    'usage':{'input_tokens':20,'output_tokens':5,'total_tokens':25,'input_tokens_details':{'cached_tokens':0}}}}
                try:
                    self.wfile.write(('data: '+json.dumps(completed)+'\n\n').encode());self.wfile.flush()
                    request['terminal_write_completed']=True
                except (BrokenPipeError,ConnectionResetError):request['terminal_write_completed']=False
                finally:terminal_attempted.set()

    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    args=['codex','exec','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--json',
          '--model','gpt-6-astra','-c','model_reasoning_effort="high"','-c','model_catalog_json="/policy/model-catalog.json"']
    for k,v in json.loads(Path('/policy/policy.json').read_text()).items():args+=['-c',k+'='+json.dumps(v)]
    args+=['-c','model_provider="local_probe"','-c','model_providers.local_probe.name="local probe"',
           '-c',f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
           '-c','model_providers.local_probe.wire_api="responses"',
           '-c','model_providers.local_probe.requires_openai_auth=false','-']
    result=None
    try:result=subprocess.run(args,input='Run the finite notification probe.',text=True,capture_output=True,timeout=25)
    finally:
        terminal_attempted.wait(2)
        server.shutdown();server.server_close()
        print(json.dumps({'exit_code':result.returncode if result else None,'requests':requests,
            'partial_started':partial.is_set(),'child_done':child_done.is_set(),'control':control,
            'delayed_terminal_attempted':terminal_attempted.is_set(),
            'accounting':collect('/codex/sessions','/codex/state_5.sqlite')}))


if __name__=='__main__':main()
