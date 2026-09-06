"""Provider-free regression tests for preparation, publication and recovery."""

import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().with_name("sync-host-ai-cli-versions")
PACKAGES = {"codex": "@openai/codex", "claude": "@anthropic-ai/claude-code",
            "gemini": "@google/gemini-cli"}
KEYS = {"codex": "CODEX_CLI_VERSION", "claude": "CLAUDE_CODE_VERSION",
        "gemini": "GEMINI_CLI_VERSION", "grok": "GROK_CLI_VERSION"}
INSTALLER = r'''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
root = Path(os.environ['FIXTURE_ROOT'])
mode = os.environ.get('FIXTURE_MODE', 'ok')
args = sys.argv[1:]
kind = Path(sys.argv[0]).name
with (root / 'calls').open('a') as log:
    log.write(json.dumps([kind, args]) + '\n')
if kind == 'npm':
    prefix = Path(args[args.index('--prefix') + 1])
    for spec in (a for a in args if a.startswith('@')):
        package, version = spec.rsplit('@', 1)
        name = {'@openai/codex':'codex', '@anthropic-ai/claude-code':'claude',
                '@google/gemini-cli':'gemini'}[package]
        directory = prefix / 'lib/node_modules' / package
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'package.json').write_text(json.dumps({'version': version}))
        binary = directory / 'cli'
        reported = '9.9.9' if mode == 'npm-wrong' else version
        binary.write_text('#!/bin/sh\necho ' + name + ' ' + reported + '\n'
                          + ('exit 17\n' if mode == 'exit-fail' else ''))
        if mode == 'absolute-install-path':
            payload = directory / 'payload'
            payload.write_text(binary.read_text())
            payload.chmod(0o755)
            binary.write_text('#!/bin/sh\nexec "' + str(payload) + '" "$@"\n')
        binary.chmod(0o644 if mode == 'non-executable' else 0o755)
        link = prefix / 'bin' / name
        if mode != 'missing-binary':
            link.symlink_to('../lib/node_modules/' + package + '/cli')
    if mode == 'npm-fail':
        raise SystemExit(31)
    if mode == 'hold':
        (root / 'entered').write_text(str(os.getpid()))
        while not (root / 'release').exists():
            time.sleep(.01)
else:
    if mode == 'curl-fail':
        raise SystemExit(22)
    url = next(a for a in args if a.startswith('https://'))
    version = url.rsplit('/grok-', 1)[1].split('-linux-', 1)[0]
    if mode == 'grok-wrong':
        version = '9.9.9'
    output = Path(args[args.index('-o') + 1])
    output.write_text('#!/bin/sh\necho grok ' + version + '\n')
'''


def tree(root):
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            data = os.readlink(path) if stat.S_ISLNK(mode) else (
                path.read_bytes() if stat.S_ISREG(mode) else None)
            result[str(path.relative_to(root))] = (mode, data)
    return result


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sync regression ")
        self.root = Path(self.temp.name)
        self.prefix = self.root / "protected parent" / "CLI prefix"
        (self.prefix / "bin").mkdir(parents=True)
        self.manifest = self.root / "versions.env"
        self.processes = []
        for name in KEYS:
            if name in PACKAGES:
                directory = self.prefix / "lib/node_modules" / PACKAGES[name]
                directory.mkdir(parents=True)
                (directory / "package.json").write_text('{"version":"1.0.0"}')
                binary = directory / "cli"
                (self.prefix / "bin" / name).symlink_to(
                    "../lib/node_modules/" + PACKAGES[name] + "/cli")
            else:
                binary = self.prefix / "bin" / name
            binary.write_text(f"#!/bin/sh\necho {name} 1.0.0\n")
            binary.chmod(0o755)
        (self.prefix / "private file").write_text("keep this\n")
        (self.prefix / "private file").chmod(0o600)
        (self.prefix / "user link").symlink_to("private file")
        for name in ("npm", "curl"):
            path = self.root / name
            path.write_text(INSTALLER)
            path.chmod(0o755)
        self.write_manifest()
        self.before = tree(self.prefix)

    def tearDown(self):
        for process in self.processes:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
            process.stdout.close()
            process.stderr.close()
        self.prefix.parent.chmod(0o755)
        self.temp.cleanup()

    def write_manifest(self, names=KEYS, version="2.3.4"):
        self.manifest.write_text("".join(f"{KEYS[n]}={version}\n" for n in names))

    def start(self, mode="ok", **env):
        settings = {k: v for k, v in os.environ.items() if not k.startswith("DEVCONTAINER_")}
        settings.update(DEVCONTAINER_AI_CLI_CHANNEL="edge",
                        DEVCONTAINER_AI_CLI_VERSION_FILE=str(self.manifest),
                        DEVCONTAINER_AI_CLI_PREFIX=str(self.prefix),
                        DEVCONTAINER_AI_CLI_NPM_BIN=str(self.root / "npm"),
                        DEVCONTAINER_AI_CLI_CURL_BIN=str(self.root / "curl"),
                        FIXTURE_ROOT=str(self.root), FIXTURE_MODE=mode)
        settings.update(env)
        process = subprocess.Popen(["bash", str(SCRIPT)], env=settings,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        self.processes.append(process)
        return process

    def run_sync(self, mode="ok", success=True, **env):
        process = self.start(mode, **env)
        output, error = process.communicate(timeout=12)
        self.assertEqual(process.returncode == 0, success, output + error)
        return error

    def versions(self):
        return {name: subprocess.check_output([str(self.prefix / "bin" / name), "--version"],
                                              text=True).strip() for name in KEYS}

    def assert_versions(self, names=KEYS, version="2.3.4"):
        self.assertEqual(self.versions(), {n: f"{n} {version if n in names else '1.0.0'}" for n in KEYS})

    def wait_entered(self, process):
        deadline = time.monotonic() + 5
        while not (self.root / "entered").exists():
            self.assertIsNone(process.poll())
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.01)

    def test_success_noop_and_unwritable_parent(self):
        self.prefix.parent.chmod(0o555)
        self.run_sync()
        self.assert_versions()
        self.assertTrue(self.prefix.is_dir())
        self.assertFalse(self.prefix.is_symlink())
        self.assertTrue((self.prefix / "bin").is_symlink())
        for name in ("private file", "user link"):
            self.assertEqual(tree(self.prefix)[name], self.before[name])
        before, calls = tree(self.prefix), (self.root / "calls").read_bytes()
        self.run_sync()
        self.assertEqual(tree(self.prefix), before)
        self.assertEqual((self.root / "calls").read_bytes(), calls)

    def test_failures_preserve_tree_and_retry(self):
        for mode in ("npm-fail", "curl-fail", "npm-wrong", "grok-wrong",
                     "missing-binary", "non-executable", "exit-fail", "absolute-install-path"):
            with self.subTest(mode=mode):
                self.run_sync(mode, success=False)
                self.assertEqual(tree(self.prefix), self.before)
        self.run_sync()
        self.assert_versions()
        updated = tree(self.prefix)
        self.write_manifest(version="3.4.5")
        self.run_sync("curl-fail", success=False)
        self.assertEqual(tree(self.prefix), updated)
        self.run_sync()
        self.assert_versions(version="3.4.5")

    def test_unspecified_tools_and_partial_noop(self):
        self.write_manifest(["codex"])
        self.run_sync()
        self.assert_versions(["codex"])
        (self.root / "calls").write_text("")
        self.write_manifest(["codex", "grok"])
        self.run_sync()
        self.assert_versions(["codex", "grok"])
        self.assertNotIn('"npm"', (self.root / "calls").read_text())

    def test_metadata_is_not_an_executable_check(self):
        for package in PACKAGES.values():
            (self.prefix / "lib/node_modules" / package / "package.json").write_text(
                '{"version":"2.3.4"}')
        self.run_sync()
        self.assert_versions()

    def test_empty_optional_environment_values_use_defaults(self):
        self.run_sync(DEVCONTAINER_AI_CLI_CURL_BIN="", DEVCONTAINER_GROK_DOWNLOAD_BASE="",
                      PATH=str(self.root) + os.pathsep + os.environ["PATH"])
        self.assert_versions()
        calls = [json.loads(line) for line in (self.root / "calls").read_text().splitlines()]
        curl_args = next(args for name, args in calls if name == "curl")
        self.assertTrue(any(arg.startswith("https://x.ai/cli/grok-") for arg in curl_args))

    def test_symlinked_package_ancestors_never_write_through(self):
        modules = self.prefix / "lib/node_modules"
        external = self.root / "external modules"
        modules.rename(external)
        modules.symlink_to(external)
        before = tree(external)
        self.write_manifest(["codex"])
        self.run_sync()
        self.assert_versions(["codex"])
        self.assertEqual(tree(external), before)

    def test_unspecified_external_binary_link_remains_usable(self):
        outside = self.prefix.parent / "external claude"
        outside.write_text("#!/bin/sh\necho claude 1.0.0\n")
        outside.chmod(0o755)
        binary = self.prefix / "bin/claude"
        binary.unlink()
        binary.symlink_to("../../external claude")
        self.write_manifest(["codex"])
        self.run_sync()
        self.assert_versions(["codex"])

    def test_signals_preserve_legacy_and_generation(self):
        for sig, wanted in ((signal.SIGTERM, "2.3.4"), (signal.SIGKILL, "4.5.6")):
            with self.subTest(signal=sig):
                before = tree(self.prefix)
                process = self.start("hold")
                self.wait_entered(process)
                self.assertEqual(tree(self.prefix), before)
                os.killpg(process.pid, sig)
                self.assertNotEqual(process.wait(timeout=3), 0)
                self.assertEqual(tree(self.prefix), before)
                (self.root / "entered").unlink()
                self.run_sync()
                self.assert_versions(version=wanted)
                self.write_manifest(version="4.5.6")

    def test_concurrent_alias_and_later_manifest(self):
        first = self.start("hold")
        self.wait_entered(first)
        alias = self.root / "prefix alias"
        alias.symlink_to(self.prefix)
        self.write_manifest(version="7.8.9")
        error = self.run_sync(success=False, DEVCONTAINER_AI_CLI_PREFIX=str(alias))
        self.assertIn("retry", error)
        self.assertEqual(len((self.root / "calls").read_text().splitlines()), 1)
        (self.root / "release").touch()
        self.assertEqual(first.wait(timeout=12), 0)
        self.assert_versions()
        self.run_sync()
        self.assert_versions(version="7.8.9")

    def test_killed_parent_keeps_child_lock(self):
        first = self.start("hold")
        self.wait_entered(first)
        os.kill(first.pid, signal.SIGKILL)
        first.wait(timeout=3)
        self.assertIn("execution group", self.run_sync(success=False))
        self.assertEqual(tree(self.prefix), self.before)
        os.killpg(first.pid, signal.SIGKILL)
        # The lock follows live file descriptors, not the coordinator PID. Give
        # the kernel a bounded interval to finish terminating the child.
        deadline = time.monotonic() + 3
        while True:
            process = self.start()
            _, error = process.communicate(timeout=12)
            if process.returncode == 0:
                break
            self.assertIn("already running", error)
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.01)
        self.assert_versions()


if __name__ == "__main__":
    unittest.main()
