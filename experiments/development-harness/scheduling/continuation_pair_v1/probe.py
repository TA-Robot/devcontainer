"""Actual CLI/tools with a finite synthetic provider; runs inside Docker only."""
import hashlib
import http.server
import itertools
import json
from pathlib import Path
import shlex
import subprocess
import threading


def main():
    mode = json.loads(Path('/policy/mode.json').read_text())['mode']
    condition = json.loads(Path('/policy/limits.json').read_text())['condition']
    requests, counts = [], {}
    sequence = itertools.count(1)

    def child_finished(parent):
        for path in Path('/codex/sessions').rglob('*.jsonl'):
            try:
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                if (rows[0]['payload'].get('parent_thread_id') == parent
                        and any(r['type'] == 'event_msg' and r['payload'].get('type') == 'task_complete' for r in rows)):
                    return True
            except (OSError, ValueError, KeyError): pass
        return False

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            meta = json.loads(self.headers['x-codex-turn-metadata'])
            tid = meta['thread_id']; root = meta['agent_name'] == '/root'
            counts[tid] = counts.get(tid, 0)+1; step = counts[tid]; number = next(sequence)
            if number > 40: raise RuntimeError('finite request cap')
            groups = [g for i in body.get('input', []) if i.get('type') == 'additional_tools' for g in i.get('tools', [])]
            names = [g['name']+'.'+t['name'] for g in groups for t in g.get('tools', [])]
            descriptions = '\n'.join(t.get('description', '') for g in groups for t in g.get('tools', []))
            missing = mode == 'missing_usage' and root and step == 2
            requests.append({'thread_id': tid, 'is_root': root, 'step': step,
                             'spawn_available': 'collaboration.spawn_agent' in names,
                             'shell_available': '### `exec_command`' in descriptions,
                             'usage_present': not missing})
            message = {'id': 'msg_'+str(number), 'type': 'message', 'role': 'assistant',
                       'content': [{'type': 'output_text', 'text': 'Continuation probe complete.'}]}

            def shell(command):
                return {'id': 'tool_'+str(number), 'type': 'custom_tool_call', 'call_id': 'call_'+str(number),
                        'name': 'exec', 'namespace': 'functions',
                        'input': 'text(await tools.exec_command('+json.dumps({'cmd': command, 'yield_time_ms': 10000})+'));'}

            def call(name, args):
                return {'id': 'tool_'+str(number), 'type': 'function_call', 'call_id': 'call_'+str(number),
                        'namespace': 'collaboration', 'name': name, 'arguments': json.dumps(args)}

            if root and step == 1:
                if mode == 'timeout':
                    message = shell('echo running > /work/probe-running.txt && sleep 60')
                else:
                    edit = ('from pathlib import Path; import hashlib,json; '
                            's=Path("/public/initial.py").read_bytes(); '
                            'Path("/work/initial-hash.json").write_text(json.dumps({"sha256":hashlib.sha256(s).hexdigest()})); '
                            'Path("/work/broken.py").write_bytes(b"print(dict())\\n"+s)')
                    message = shell('python3 -c '+shlex.quote(edit)+' && python3 /public/public_check.py '
                                    '--candidate /work/broken.py --cases /public/probe.json --output /work/broken.json')
            elif root and step == 2:
                edit = ('from pathlib import Path; '
                        'Path("/work/submission.py").write_bytes(Path("/public/initial.py").read_bytes()+b"\\n# synthetic verified continuation\\n")')
                message = shell('python3 -c '+shlex.quote(edit)+' && python3 /public/public_check.py '
                                '--candidate /work/submission.py --cases /public/probe.json --output /work/repaired.json')
            elif root and step == 3:
                script = ('import socket,json\nfrom pathlib import Path\n'
                          'try:\n s=socket.create_connection(("127.0.0.1",'+str(server.server_port)+'),timeout=1);s.close();denied=False\n'
                          'except OSError:\n denied=True\n'
                          'try:\n Path("/observation/forged").write_text("x");protected=False\n'
                          'except OSError:\n protected=True\n'
                          'try:\n Path("/public/initial.py").write_text("x");readonly=False\n'
                          'except OSError:\n readonly=True\n'
                          'Path("/work/boundary.json").write_text(json.dumps({"network_denied":denied,"observation_protected":protected,"initial_readonly":readonly,"private_input_absent":not Path("/qualification.private.json").exists()}))\n')
                message = shell('python3 -c '+shlex.quote(script))
            elif root and condition == 'adaptive':
                if step == 4:
                    message = call('spawn_agent', {'task_name': 'checker', 'fork_turns': 'none',
                        'message': 'Use the public initial source and the bounded capability probe; return a final result.'})
                elif not child_finished(tid):
                    message = shell('sleep 0.25')
            elif not root and step == 1:
                message = shell('python3 /public/public_check.py --candidate /public/initial.py '
                                '--cases /public/probe.json --output /work/child.json')
            rid = 'resp_continuation_'+str(number)
            events = [{'type': 'response.created', 'response': {'id': rid}},
                      {'type': 'response.output_item.done', 'output_index': 0, 'item': message},
                      {'type': 'response.completed', 'response': {'id': rid, 'status': 'completed', 'output': [message]}}]
            if not missing:
                events[-1]['response']['usage'] = {'input_tokens': 20, 'output_tokens': 5, 'total_tokens': 25,
                                                   'input_tokens_details': {'cached_tokens': 7}}
            data = ''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    args = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--json',
            '--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="high"',
            '-c', 'model_catalog_json="/policy/model-catalog.json"']
    for key, value in json.loads(Path('/policy/policy.json').read_text()).items():
        args += ['-c', key+'='+json.dumps(value)]
    args += ['-c', 'model_provider="local_probe"', '-c', 'model_providers.local_probe.name="local probe"',
             '-c', f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
             '-c', 'model_providers.local_probe.wire_api="responses"',
             '-c', 'model_providers.local_probe.requires_openai_auth=false', '-']
    result = None
    try:
        result = subprocess.run(args, input='Execute the finite continuation capability probe.',
                                text=True, capture_output=True, timeout=60)
    finally:
        server.shutdown(); server.server_close()
        print(json.dumps({'condition': condition, 'mode': mode, 'requests': requests,
                          'returncode': result.returncode if result else None,
                          'initial_sha256': hashlib.sha256(Path('/public/initial.py').read_bytes()).hexdigest()}))


if __name__ == '__main__': main()
