"""Run INSIDE the actor image with a synthetic local Responses server, no auth/network.

Observe the real CLI request rather than inferring tool exposure from config names.
"""
import http.server
import json
from pathlib import Path
import subprocess
import threading


def argv(policy_root=Path('/policy')):
    args = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
            '--skip-git-repo-check', '--json', '--output-schema', '/policy/response.schema.json',
            '--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="high"',
            '-c', 'model_catalog_json="/policy/model-catalog.json"']
    for key, value in json.loads((policy_root / 'policy.json').read_text()).items():
        args += ['-c', key + '=' + json.dumps(value)]
    return args


def main():
    requests = []
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            message = {'id': 'msg_test', 'type': 'message', 'role': 'assistant',
                       'content': [{'type': 'output_text', 'text': '{"action":"advice","content":"capability only"}'}]}
            events = [
                {'type': 'response.created', 'response': {'id': 'resp_test'}},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': message},
                {'type': 'response.completed', 'response': {'id': 'resp_test', 'status': 'completed',
                    'output': [message], 'usage': {'input_tokens': 20, 'output_tokens': 5, 'total_tokens': 25,
                                                'input_tokens_details': {'cached_tokens': 0}}}}]
            data = ''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    args = argv() + ['-c', 'model_provider="local_probe"',
        '-c', 'model_providers.local_probe.name="local probe"',
        '-c', f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
        '-c', 'model_providers.local_probe.wire_api="responses"',
        '-c', 'model_providers.local_probe.requires_openai_auth=false', '-']
    try:
        result = subprocess.run(args, input='Return the requested response shape.', text=True,
                                capture_output=True, timeout=30)
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps({'exit_code': result.returncode, 'requests': len(requests),
                      'tools': [[t.get('name', t.get('type')) for t in r.get('tools', [])] for r in requests],
                      'events': result.stdout, 'diagnostic': result.stderr[-2000:]}))


if __name__ == '__main__':
    main()
