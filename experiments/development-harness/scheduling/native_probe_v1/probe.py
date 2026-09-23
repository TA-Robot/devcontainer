"""Synthetic Responses server exercising actual pinned native child execution.

Container only, no credentials, no external network. Response content is fixed
test code. The provider ledger is an independent oracle for rollout accounting.
"""
import http.server
import itertools
import json
from pathlib import Path
import shlex
import subprocess
import threading

from accounting import collect


def main():
    mode = json.loads(Path('/policy/mode.json').read_text())['mode']
    requests = []
    counts = {}
    sequence = itertools.count(1)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            meta = json.loads(self.headers['x-codex-turn-metadata'])
            tid = meta['thread_id']
            counts[tid] = counts.get(tid, 0) + 1
            step = counts[tid]
            is_root = meta['agent_name'] == '/root'
            number = next(sequence)
            response_id = 'resp_probe_' + str(number)
            missing = mode == 'missing_usage' and not is_root and step == 3
            groups = [g for i in body.get('input', []) if i.get('type') == 'additional_tools'
                      for g in i.get('tools', [])]
            descriptions = '\n'.join(t.get('description', '') for g in groups for t in g.get('tools', []))
            names = [g['name'] + '.' + t['name'] for g in groups for t in g.get('tools', [])]
            requests.append({'thread_id': tid, 'parent_thread_id': meta.get('parent_thread_id'),
                             'turn_id': meta['turn_id'], 'response_id': response_id,
                             'usage': None if missing else {'input_tokens': 20, 'cached_input_tokens': 7,
                                 'output_tokens': 5, 'cache_write_input_tokens': 0,
                                 'reasoning_output_tokens': 0, 'total_tokens': 25},
                             'shell_available': '### `exec_command`' in descriptions,
                             'spawn_available': 'collaboration.spawn_agent' in names})
            message = {'id': 'msg_' + str(number), 'type': 'message', 'role': 'assistant',
                       'content': [{'type': 'output_text', 'text': 'PROBE_DONE'}]}

            def call(name, args):
                return {'id': 'tool_' + str(number), 'type': 'function_call',
                        'call_id': 'call_' + str(number), 'name': name, 'namespace': 'collaboration',
                        'arguments': json.dumps(args)}

            def shell(command):
                return {'id': 'tool_' + str(number), 'type': 'custom_tool_call',
                        'call_id': 'call_' + str(number), 'name': 'exec', 'namespace': 'functions',
                        'input': 'text(await tools.exec_command(' + json.dumps({'cmd': command, 'yield_time_ms': 10000}) + '));'}

            if is_root:
                if step == 1:
                    message = shell('echo root > /work/root.txt')
                elif step == 2:
                    message = call('spawn_agent', {'task_name': 'probe', 'message': 'Run the bounded capability probe.',
                                   'fork_turns': 'all' if mode == 'fork_all' else 'none'})
                elif step in (3, 5):
                    message = call('wait_agent', {'timeout_ms': 10000})
                elif step == 4:
                    message = call('followup_task', {'target': 'probe', 'message': 'Return one further final response.'})
            elif step == 1:
                network = ('import socket,json\nfrom pathlib import Path\n'
                    'try:\n s=socket.create_connection(("127.0.0.1",' + str(server.server_port) + '),timeout=1);s.close();denied=False\n'
                    'except OSError:\n denied=True\n'
                    'Path("/work/child-network.json").write_text(json.dumps({"denied":denied}))\n')
                command = ('python3 -c ' + shlex.quote(network)
                    + ' && cp /public/fifo.py /work/submission.py && python3 /public/public_check.py --candidate /work/submission.py --cases /public/probe.json --output /work/child-report.json')
                if mode == 'child_timeout':
                    command = 'echo started > /work/child-running.txt && sleep 60'
                message = shell(command)
            events = [
                {'type': 'response.created', 'response': {'id': response_id}},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': message},
                {'type': 'response.completed', 'response': {'id': response_id, 'status': 'completed', 'output': [message]}}]
            if not missing:
                events[-1]['response']['usage'] = {'input_tokens': 20, 'output_tokens': 5,
                    'total_tokens': 25, 'input_tokens_details': {'cached_tokens': 7}}
            data = ''.join('data: ' + json.dumps(e) + '\n\n' for e in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    args = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check',
            '--json', '--model', 'gpt-6-astra', '-c', 'model_reasoning_effort="high"',
            '-c', 'model_catalog_json="/policy/model-catalog.json"']
    for key, value in json.loads(Path('/policy/policy.json').read_text()).items():
        args += ['-c', key + '=' + json.dumps(value)]
    args += ['-c', 'model_provider="local_probe"', '-c', 'model_providers.local_probe.name="local probe"',
             '-c', f'model_providers.local_probe.base_url="http://127.0.0.1:{server.server_port}/v1"',
             '-c', 'model_providers.local_probe.wire_api="responses"',
             '-c', 'model_providers.local_probe.requires_openai_auth=false', '-']
    result = None
    try:
        result = subprocess.run(args, input='Execute the finite synthetic capability probe.',
                                text=True, capture_output=True, timeout=60)
    finally:
        server.shutdown()
        server.server_close()
        report = collect('/codex/sessions', '/codex/state_5.sqlite')
        # The output deliberately excludes prompts, command text, and model messages.
        root_usage = None
        if result:
            for line in result.stdout.splitlines():
                event = json.loads(line)
                if event.get('type') == 'turn.completed':
                    root_usage = event['usage']
        child = Path('/work/child-report.json')
        network = Path('/work/child-network.json')
        print(json.dumps({'mode': mode, 'exit_code': result.returncode if result else None,
                          'root_stdout_usage': root_usage, 'requests': requests, 'accounting': report,
                          'child_network_denied': network.exists() and json.loads(network.read_text())['denied'],
                          'child_public_check_valid': child.exists() and json.loads(child.read_text())['valid']}))


if __name__ == '__main__':
    main()
