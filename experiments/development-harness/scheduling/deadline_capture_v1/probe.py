"""Synthetic provider: submit a fixed artifact, then complete or remain active."""
import http.server
import json
from pathlib import Path
import shlex
import subprocess
import threading


def main():
    mode = json.loads(Path('/policy/mode.json').read_text())['mode']; counts = {}; requests = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            meta = json.loads(self.headers['x-codex-turn-metadata']); tid = meta['thread_id']
            counts[tid] = counts.get(tid, 0)+1; step = counts[tid]; n = len(requests)+1
            requests.append({'thread_id': tid, 'step': step})
            if n > 20: raise RuntimeError('finite synthetic request cap')
            message = {'id': 'msg_'+str(n), 'type': 'message', 'role': 'assistant',
                       'content': [{'type': 'output_text', 'text': 'Capture calibration complete.'}]}
            def shell(command):
                return {'id': 'tool_'+str(n), 'type': 'custom_tool_call', 'call_id': 'call_'+str(n),
                        'name': 'exec', 'namespace': 'functions',
                        'input': 'text(await tools.exec_command('+json.dumps({'cmd': command, 'yield_time_ms': 10000})+'));'}
            def call(name, args):
                return {'id': 'tool_'+str(n), 'type': 'function_call', 'call_id': 'call_'+str(n),
                        'namespace': 'collaboration', 'name': name, 'arguments': json.dumps(args)}
            if mode == 'child' and meta['agent_name'] == '/root':
                message = (call('spawn_agent', {'task_name': 'writer', 'fork_turns': 'none',
                           'message': 'Execute the finite artifact capture probe.'}) if step == 1 else
                           call('wait_agent', {'timeout_ms': 10000}))
            elif step == 1:
                if mode == 'invalid':
                    invalid = 'import sys,json\nfor line in sys.stdin:\n r=json.loads(line);print(json.dumps({"request_id":r["request_id"],"assignments":None}),flush=True)\n'
                    command = 'python3 -c '+shlex.quote('from pathlib import Path; Path("/work/submission.py").write_text('+repr(invalid)+')')
                elif mode == 'missing': command = 'true'
                else: command = 'cp /public/initial.py /work/submission.py'
                if mode == 'child': command += ' && chmod u+w /work/submission.py'
                command += ' && echo ready > /work/capture-ready.txt'
                if mode == 'child':
                    writer = ('import time\nfrom pathlib import Path\n'
                              'while True:\n with Path("/work/submission.py").open("a") as f:f.write("\\n# capture heartbeat\\n")\n time.sleep(.05)\n')
                    command += ' && python3 -c '+shlex.quote(writer)
                elif mode != 'normal': command += ' && sleep 60'
                message = shell(command)
            rid = 'resp_capture_'+str(n)
            events = [{'type': 'response.created', 'response': {'id': rid}},
                      {'type': 'response.output_item.done', 'output_index': 0, 'item': message},
                      {'type': 'response.completed', 'response': {'id': rid, 'status': 'completed', 'output': [message],
                       'usage': {'input_tokens': 20, 'output_tokens': 5, 'total_tokens': 25,
                                 'input_tokens_details': {'cached_tokens': 7}}}}]
            data = ''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    args = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--json',
            '--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="high"',
            '-c', 'model_catalog_json="/policy/model-catalog.json"']
    for k, v in json.loads(Path('/policy/policy.json').read_text()).items(): args += ['-c', k+'='+json.dumps(v)]
    args += ['-c', 'model_provider="local_probe"', '-c', 'model_providers.local_probe.name="local probe"',
             '-c', f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
             '-c', 'model_providers.local_probe.wire_api="responses"',
             '-c', 'model_providers.local_probe.requires_openai_auth=false', '-']
    try: result = subprocess.run(args, input='Run the finite capture calibration.', text=True, capture_output=True, timeout=60)
    finally: server.shutdown(); server.server_close()
    print(json.dumps({'returncode': result.returncode, 'requests': requests, 'mode': mode}))


if __name__ == '__main__': main()
