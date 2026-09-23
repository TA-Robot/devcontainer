"""Finite relay and real pinned-CLI tool surface, using only synthetic providers."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/selection/relay_v1'
sys.path.insert(0, str(HERE))
import relay


def events(action, content, usage=True):
    rows = [{'type': 'thread.started', 'thread_id': 'test'}, {'type': 'turn.started'},
            {'type': 'item.completed', 'item': {'type': 'agent_message',
             'text': json.dumps({'action': action, 'content': content})}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 20, 'cached_input_tokens': 0, 'output_tokens': 5} if usage else None}]
    return '\n'.join(json.dumps(r) for r in rows)


def decision():
    return json.dumps({'candidates': [
        {'id': 'candidate-1', 'scopes': {'matching-adoption': 'needs-repair', 'path-boundaries': 'needs-repair'},
         'evidence': ['candidates/candidate-1/manage-agent-project'], 'reason': 'Unicode 日本語 / escaped "quotes"'},
        {'id': 'candidate-2', 'scopes': {'matching-adoption': 'acceptable', 'path-boundaries': 'needs-repair'},
         'evidence': ['candidates/candidate-2/manage-agent-project'], 'reason': 'Calibration only'}], 'selected': None},
        ensure_ascii=False, indent=3) + '\n'


class ParserTests(unittest.TestCase):
    def test_submission_failure_never_invents_cleanup(self):
        actor_record = {'status': 'completed', 'removed': True,
                        'usage': {'input_tokens': 20, 'cached_input_tokens': 0, 'output_tokens': 5},
                        'response': {'action': 'submit', 'content': decision()},
                        'content_sha256': relay.adapter.digest(decision().encode())}
        def failure(task, content, folder):
            (folder / 'submission').mkdir()
            relay.adapter.save(folder / 'submission/run.json', {'owned_container_removed': True})
            raise ValueError('assessment interrupted after successful cleanup')
        for final, removed in [(ValueError('started without record'), False),
                ({'removed': False, 'content_sha256': actor_record['content_sha256']}, False),
                (failure, True)]:
            with self.subTest(final=final), tempfile.TemporaryDirectory() as raw:
                options = {'side_effect': final} if callable(final) or isinstance(final, Exception) else {'return_value': final}
                with mock.patch.object(relay, 'actor', return_value=actor_record), mock.patch.object(relay, 'final_assessment', **options):
                    result = relay.run(Path(raw)/'pair', fake=lambda *args: 'unused')
                self.assertEqual(result['status'], 'stopped')
                self.assertEqual(result['all_recorded_containers_removed'], removed)
                self.assertEqual(result['conditions']['solo']['final']['removed'], removed)

    def test_exact_content_usage_and_unexpected_tools(self):
        content = decision()
        request, usage, raw = relay.parse_actor(events('submit', content))
        self.assertEqual(request['content'], content)
        self.assertEqual(usage['output_tokens'], 5)
        progress = json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Inspecting the supplied code.'}})
        self.assertEqual(relay.parse_actor(progress+'\n'+events('submit', content))[0]['content'], content)
        for bad in (events('submit', content, False), events('alien', content),
                    events('submit', content)+'\n'+json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution'}}),
                    events('submit', content)+'\n'+json.dumps({'type': 'item.completed', 'item': None}),
                    events('submit', content)+'\n'+json.dumps({'type': 'item.completed', 'item': {'type': 'error', 'message': 'other error'}})):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                relay.parse_actor(bad)

    def test_common_input_history_and_role_boundary(self):
        public = {'TASK.md': 'example'}
        base = relay.prompt(public, 'maker', [], None, 2)
        advised = relay.prompt(public, 'maker', [], 'independent finding', 2)
        self.assertEqual(base.split('\n', 1)[0], advised.split('\n', 1)[0])
        self.assertEqual(json.loads(base.split('\n', 1)[1])['task_files'], public)
        self.assertIn('No probes are available', relay.prompt(public, 'advisor', [], None, 2))
        self.assertEqual(json.loads(relay.prompt(public, 'maker', [{'stdout': 'unaltered'}], None, 1).split('\n', 1)[1])['history'], [{'stdout': 'unaltered'}])


@unittest.skipUnless(os.environ.get('LIFECYCLE_RELAY_DOCKER'), 'set LIFECYCLE_RELAY_DOCKER=1 for real images')
class DockerTests(unittest.TestCase):
    def test_real_codex_sends_no_tools_and_no_reference_is_installed(self):
        image = json.loads((HERE / 'actor-image.json').read_text())['image']
        command = ['docker', 'run', '--rm', '--network', 'none', '--read-only',
            '--tmpfs', '/codex:rw,mode=1777', '--tmpfs', '/work:rw,mode=1777', '--tmpfs', '/tmp:rw,mode=1777',
            '--mount', f'type=bind,src={HERE},dst=/policy,readonly', image, 'python3', '/policy/capability.py']
        value = json.loads(subprocess.check_output(command, text=True, timeout=45))
        self.assertEqual(value['exit_code'], 0, value)
        self.assertEqual(value['requests'], 1)
        self.assertEqual(value['tools'], [[]])
        request, usage, _ = relay.parse_actor(value['events'])
        self.assertEqual(request['action'], 'advice')
        code = "from pathlib import Path; assert not any(Path(p).exists() for p in ['/usr/local/bin/manage-agent-project','/usr/local/share/agent-project','/usr/local/lib/agentctl','/opt/devcontainer-ai-cli','/var/run/docker.sock'])"
        subprocess.run(['docker', 'run', '--rm', '--network', 'none', image, 'python3', '-c', code], check=True, timeout=15)

    def test_full_fake_pair_probe_feedback_and_exact_submission(self):
        code = "import json;from pathlib import Path;print(json.dumps({'candidates':sorted(p.name for p in Path('/task/candidates').iterdir())}))"
        def fake(condition, role, index):
            if role == 'advisor':
                return events('advice', 'Independent calibration advice')
            if index == (1 if condition == 'consult' else 0):
                return events('probe', code)
            return events('submit', decision())
        with tempfile.TemporaryDirectory(prefix='lifecycle-relay-pair-') as raw:
            path = Path(raw) / 'pair'
            result = relay.run(path, fake=fake)
            self.assertEqual(result['status'], 'completed', result)
            self.assertTrue(result['all_recorded_containers_removed'])
            for condition, count in [('solo', 2), ('consult', 3)]:
                row = result['conditions'][condition]
                self.assertEqual(len(row['actors']), count)
                self.assertEqual(row['usage']['output_tokens'], 5 * count)
                self.assertEqual(row['final']['assessment']['status'], 'matched')
                self.assertEqual((path / condition / 'submission/probe.stdout').read_bytes(), decision().encode())
                prompt = json.loads((path / condition / f'actor-{count-1}/prompt.private.txt').read_text().split('\n', 1)[1])
                self.assertIn('candidate-1', prompt['history'][0]['stdout'])
                self.assertEqual(prompt['untrusted_advice'], 'Independent calibration advice' if condition == 'consult' else None)
            with self.assertRaises(FileExistsError):
                relay.run(path, fake=fake)

    def test_unknown_usage_stops_before_probe_or_other_condition(self):
        with tempfile.TemporaryDirectory(prefix='lifecycle-relay-usage-') as raw:
            result = relay.run(Path(raw)/'pair', fake=lambda *args: events('submit', decision(), False))
            self.assertEqual(result['status'], 'stopped')
            self.assertEqual(list(result['conditions']), ['solo'])
            self.assertFalse(result['conditions']['solo']['usage_complete'])
            self.assertTrue(result['all_recorded_containers_removed'])

    def test_actor_timeout_and_over_budget_usage_are_stopped(self):
        with tempfile.TemporaryDirectory(prefix='lifecycle-relay-cutoff-') as raw:
            root = Path(raw)
            result = relay.actor('test', root/'small-cap', seconds=20, token_cap=1,
                                 fake_events=events('submit', decision()))
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['usage']['output_tokens'], 5)
            self.assertTrue(result['removed'])
            result = relay.actor('test', root/'deadline', seconds=.001, token_cap=10,
                                 fake_events=events('submit', decision()))
            self.assertEqual(result['status'], 'failed')
            # Creation can lose the race to the tiny deadline: cleanup is never invented.
            self.assertIsNone(result['usage'])


if __name__ == '__main__':
    unittest.main()
