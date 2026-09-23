"""Real CLI and synthetic Responses server; never uses provider credentials."""
import http.server
import json
from pathlib import Path
import shlex
import threading

import entry


def main():
    requests = []
    mode = json.loads(Path('/control/limits.json').read_text()).get('probe_mode', 'normal')

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            i = len(requests)
            item = {'id': f'msg_{i}', 'type': 'message', 'role': 'assistant',
                    'content': [{'type': 'output_text', 'text': 'Capability probe complete.'}]}
            commands = [
                "printf 'answer = 0\n' > .pilot_probe.py\npython -c \"import runpy; assert runpy.run_path('.pilot_probe.py')['answer'] == 1\"",
                "printf 'answer = 1\n' > .pilot_probe.py\npython -c \"import runpy; assert runpy.run_path('.pilot_probe.py')['answer'] == 1\"\npython -m pytest -q test/units/module_utils/common/test_collections.py",
            ]
            script = '''import json,socket
from pathlib import Path
r={}
for name in ('/codex/auth.json','/control/prompt.txt','/observation/stdout.private.jsonl'):
 try: Path(name).read_bytes();r[name]=False
 except OSError:r[name]=True
try: Path('/observation/forged').write_text('x');r['private_write']=False
except OSError:r['private_write']=True
try: socket.create_connection(('127.0.0.1',PORT),timeout=1).close();r['network']=False
except OSError:r['network']=True
Path('.pilot_boundary.json').write_text(json.dumps(r))
assert all(r.values()),r
'''.replace('PORT', str(server.server_port))
            commands.append('python -c ' + shlex.quote(script))
            if mode == 'timeout':
                commands = ["printf 'answer = 1\n' > .pilot_probe.py\nsleep 120"]
            if i <= len(commands):
                item = {'id': f'tool_{i}', 'type': 'custom_tool_call', 'call_id': f'call_{i}',
                        'name': 'exec', 'namespace': 'functions',
                        'input': 'text(await tools.exec_command(' + json.dumps({'cmd': commands[i], 'yield_time_ms': 10000}) + '));'}
            response_id = f'resp_probe_{i}'
            usage = {'input_tokens': 20, 'output_tokens': 5, 'total_tokens': 25,
                     'input_tokens_details': {'cached_tokens': 0}}
            events = [
                {'type': 'response.created', 'response': {'id': response_id}},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                {'type': 'response.completed', 'response': {'id': response_id, 'status': 'completed',
                                                          'output': [item], 'usage': usage}},
            ]
            data = ''.join('data: ' + json.dumps(e) + '\n\n' for e in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = entry.run([
            '-c', 'model_provider="probe"', '-c', 'model_providers.probe.name="synthetic"',
            '-c', f'model_providers.probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
            '-c', 'model_providers.probe.wire_api="responses"',
            '-c', 'model_providers.probe.requires_openai_auth=false',
        ])
    finally:
        server.shutdown()
        server.server_close()
    surfaces = []
    for r in requests:
        surface = json.dumps([r.get('tools', []), [i for i in r.get('input', []) if i.get('type') == 'additional_tools']])
        surfaces.append({'shell_available': 'exec_command' in surface,
                         'subagent_available': 'spawn_agent' in surface})
    Path('/observation/probe.json').write_text(json.dumps({
        'bridge': result, 'requests': len(requests), 'surfaces': surfaces,
        'outputs': [[i for i in r.get('input', []) if 'output' in i.get('type', '')] for r in requests],
        'boundary': json.loads(Path('/app/.pilot_boundary.json').read_text()) if Path('/app/.pilot_boundary.json').exists() else None,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
