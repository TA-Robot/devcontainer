#!/usr/bin/env python3
"""Reproduce the proposed large task with existing commands and synthetic providers."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
for key in ('AGENTCTL_TEST_BIN', 'AGENTCTL_TEST_TEMPLATE', 'AGENTCTL_TEST_LIBRARY'):
    os.environ.pop(key, None)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


jobs = load('candidate_jobs', ROOT / 'scripts/test-agentctl-jobs.py')
supervisor = load('candidate_supervisor', ROOT / 'scripts/test-agentctl-supervisor.py')
OBSERVATIONS = {}


class CandidateAudit(jobs.AgentctlJobTests):
    """Only the explicitly named probes below are selected; no live provider."""

    def call(self, *args, expected=0):
        result = self.invoke('job', *args, '--json')
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def make(self, name, commands, dependencies=None):
        job = self.create(name, dependency_job_ids=dependencies or [],
                          acceptance=[{'kind': 'command', 'value': c} for c in commands])
        (self.workspace / name).unlink()
        return job

    def develop(self, job, commands):
        self.extra_environment['FAKE_ACCEPTANCE_COMMANDS'] = json.dumps(commands)
        return self.call('run', job['job_id'], '--provider', 'codex')

    def checked(self, job):
        return self.call('check', job['job_id'], '--timeout', '3')

    def strict(self, job):
        result = self.call('validate', job['job_id'], '--require-checks')
        self.assertEqual(result['validation']['command_evidence'], 'independently-executed')
        return result

    def test_existing_strict_chain_and_explicit_reentry(self):
        commands = ['test -s result.txt']
        parent = self.make('parent.json', commands)
        child = self.make('child.json', commands, [parent['job_id']])
        self.call('run', child['job_id'], '--provider', 'codex', expected=2)
        initial = subprocess.check_output(['git', '-C', str(self.workspace), 'rev-parse', 'HEAD']).strip()
        for job in (parent, child):
            self.develop(job, commands)
            self.checked(job)
            self.strict(job)
        # Every call is a fresh CLI process; durable state selects what remains.
        self.call('run', parent['job_id'], '--provider', 'codex', expected=2)
        self.assertEqual(len(self.call('show', parent['job_id'])['attempts']), 1)
        collected = self.call('collect', child['job_id'])
        self.assertEqual(collected['dependency_order'], [parent['job_id'], child['job_id']])
        self.assertFalse(collected['automatic_integration_performed'])
        self.assertEqual(collected['integration_assessment'], 'review_required')
        first_path = Path(collected['report_path'])
        before = first_path.read_bytes()
        second = self.call('collect', child['job_id'])
        self.assertNotEqual(second['report_path'], str(first_path))
        self.assertEqual(first_path.read_bytes(), before)
        self.assertEqual(subprocess.check_output(['git', '-C', str(self.workspace), 'rev-parse', 'HEAD']).strip(), initial)
        OBSERVATIONS['strict_chain'] = {
            'existing_commands_sufficient': True, 'jobs': 2, 'provider_attempts': 2,
            'duplicate_provider_dispatch': False, 'automatic_integration': False,
            'collection_reentry': 'new immutable report; original report unchanged',
            'overlapping_changes': 'review_required', 'new_product_code': False}

    def test_failed_public_check_prevents_strict_dependency_release(self):
        commands = ['exit 7']
        parent = self.make('parent.json', commands)
        child = self.make('child.json', ['test -s result.txt'], [parent['job_id']])
        self.develop(parent, commands)
        check = self.call('check', parent['job_id'], '--timeout', '3', expected=1)
        self.assertEqual(check['status'], 'failed')
        self.call('validate', parent['job_id'], '--require-checks', expected=2)
        self.call('run', child['job_id'], '--provider', 'codex', expected=2)
        self.assertEqual(self.call('show', child['job_id'])['attempts'], [])
        OBSERVATIONS['failure_before_validation'] = {
            'provider_claim_overruled': True, 'strict_validation_rejected': True,
            'child_attempts': 0, 'new_product_code': False}

    def test_validation_is_not_continuous_independent_check_authority(self):
        gate = self.root / 'external-gate'
        commands = [f"test ! -f '{gate}'"]
        parent = self.make('parent.json', commands)
        child_commands = ['test -s result.txt']
        child = self.make('child.json', child_commands, [parent['job_id']])
        self.develop(parent, commands)
        self.checked(parent)
        self.strict(parent)
        gate.touch()
        failure = self.call('check', parent['job_id'], '--timeout', '3', expected=1)
        self.assertEqual(failure['status'], 'failed')
        view = self.call('checks', parent['job_id'])
        self.assertEqual(view['latest']['status'], 'failed')
        self.assertEqual(self.call('show', parent['job_id'])['state'], 'validated')
        # Observation of current semantics, NOT desired behavior for a strict campaign.
        self.develop(child, child_commands)
        self.checked(child)
        self.strict(child)
        collected = self.call('collect', child['job_id'])
        self.assertEqual(collected['status'], 'ready')
        OBSERVATIONS['later_failure'] = {
            'latest_parent_check': 'failed', 'parent_state': 'validated',
            'child_dispatch_permitted': True, 'collection_permitted': True,
            'meaning': 'validated is a durable prior decision, not a live independent-check gate',
            'large_task_proven': False}


CASES = [
    (CandidateAudit, 'test_existing_strict_chain_and_explicit_reentry'),
    (CandidateAudit, 'test_failed_public_check_prevents_strict_dependency_release'),
    (CandidateAudit, 'test_validation_is_not_continuous_independent_check_authority'),
    (jobs.AgentctlJobTests, 'test_check_abrupt_death_keeps_incomplete_and_requires_explicit_recovery'),
    (jobs.AgentctlJobTests, 'test_checks_detect_changed_source_and_task_without_repair'),
    (jobs.AgentctlJobTests, 'test_checks_clean_retry_requires_new_evidence_for_new_source'),
    (jobs.AgentctlJobTests, 'test_checks_upgrade_actual_earlier_database_and_jobs'),
    (jobs.AgentctlJobTests, 'test_checks_upgrade_actual_phase2_evidence_and_interruption'),
    (supervisor.AgentctlSupervisorTests, 'test_detached_runner_survives_dispatch_client_and_heartbeats'),
    (supervisor.AgentctlSupervisorTests, 'test_restart_reconciliation_marks_lost_execution_orphaned'),
    (supervisor.AgentctlSupervisorTests, 'test_durable_queue_requires_safe_resubmit_after_supervisor_restart'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refusing to replace an earlier audit')
    started = time.monotonic()
    original_run = subprocess.run
    def bounded_run(*a, **kw):
        return original_run(*a, **{'timeout': 60, **kw})
    with patch('subprocess.run', bounded_run):
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(cls(name) for cls, name in CASES))
    sources = [Path(__file__), ROOT / 'scripts/test-agentctl-jobs.py', ROOT / 'scripts/test-agentctl-supervisor.py',
               ROOT / 'scripts/agentctl', ROOT / 'scripts/agentctl_jobs.py', ROOT / 'scripts/agentctl_supervisor.py']
    report = {'schema_version': 1, 'kind': 'development-task-candidate-audit-v1',
        'candidate': 'agentctl-dependent-jobs-check-recovery-collection',
        'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'elapsed_seconds': time.monotonic() - started,
        'observations': OBSERVATIONS, 'calibration_passed': result.wasSuccessful(),
        'large_task_admitted': False, 'live_comparison_admitted': False,
        'decision': 'Existing command composition covers the proposed core; the observed evidence-authority gap alone does not establish a large change series.',
        'limits': {'provider': 'synthetic only', 'command_timeout_seconds': 60,
            'classification': 'cost_cap', 'scope': 'this provider-free audit', 'owner': 'primary/integrator',
            'rationale': 'bound local CLI probes without model calls',
            'update_when': 'CLI or fixture behavior changes',
            'not_proven': ['exhaustive absence of product gaps', 'automatic owner-loss recovery',
                           'large-project generalization', 'fresh independent evidence at every downstream dispatch']}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
