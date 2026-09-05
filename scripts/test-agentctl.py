#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
AGENTCTL = ROOT / "scripts" / "agentctl"


CODEX_HELP = """exec --sandbox --ask-for-approval --cd --color
--output-schema --output-last-message --ephemeral --json
"""
CLAUDE_HELP = """--print --output-format --json-schema --permission-mode --agent --worktree
--no-session-persistence
"""
GROK_HELP = """--agent --allow --cwd --deny --json-schema --max-turns --no-subagents
--output-format --permission-mode --prompt-file --sandbox stdio
"""


class AgentctlImportTests(unittest.TestCase):
    def run_layout(self, *, checkout: bool) -> subprocess.CompletedProcess[str]:
        """Execute the actual CLI with distinct local/installed/CWD sentinels."""
        with tempfile.TemporaryDirectory(prefix="agentctl-import-") as raw:
            root = Path(raw)
            entry_dir = root / "bin"
            installed = root / "installed"
            working = root / "working"
            for directory in (entry_dir, installed, working):
                directory.mkdir()
            source = AGENTCTL.read_text(encoding="utf-8")
            # Relocate only the installation prefix for host and image tests.
            source = source.replace(
                'INSTALLED_LIBRARY = Path("/usr/local/lib/agentctl")',
                f"INSTALLED_LIBRARY = Path({str(installed)!r})",
            )
            entry = entry_dir / "agentctl"
            entry.write_text(source, encoding="utf-8")
            for directory, label in ((installed, "installed"), (working, "wrong-cwd")):
                (directory / "agentctl_jobs.py").write_text(
                    f"raise SystemExit('selected-{label}')\n", encoding="utf-8"
                )
            if checkout:
                (entry_dir / "agentctl_jobs.py").write_text(
                    "raise SystemExit('selected-checkout')\n", encoding="utf-8"
                )
            return subprocess.run(
                [sys.executable, str(entry), "--version"], cwd=working,
                env={**os.environ, "PYTHONPATH": str(working), "PYTHONDONTWRITEBYTECODE": "1"},
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            )

    def test_checkout_library_wins_over_installed_and_working_directory(self) -> None:
        result = self.run_layout(checkout=True)
        self.assertEqual(1, result.returncode)
        self.assertEqual("selected-checkout", result.stderr.strip())

    def test_installed_cli_uses_bundle_not_working_directory(self) -> None:
        result = self.run_layout(checkout=False)
        self.assertEqual(1, result.returncode)
        self.assertEqual("selected-installed", result.stderr.strip())


class AgentctlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agentctl-test-")
        self.workspace = Path(self.temp.name) / "workspace"
        self.workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "config", "user.name", "test"], check=True)
        (self.workspace / "tracked.txt").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.workspace), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "init"], check=True)
        devcontainer = self.workspace / ".devcontainer"
        devcontainer.mkdir()
        digest = "a" * 64
        (devcontainer / "devcontainer-lock.json").write_text(
            json.dumps(
                {
                    "features": {
                        "example:1": {
                            "version": "1.0.0",
                            "resolved": f"example@sha256:{digest}",
                            "integrity": f"sha256:{digest}",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        self.bin_dir = Path(self.temp.name) / "bin"
        self.bin_dir.mkdir()
        self.codex = self.make_provider("codex", "codex-cli 1.2.3", CODEX_HELP)
        self.claude = self.make_provider("claude", "4.5.6 (Claude Code)", CLAUDE_HELP)
        self.grok = self.make_provider("grok", "grok 1.0.3 (fixture) [stable]", GROK_HELP)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_provider(
        self,
        name: str,
        version: str,
        help_text: str,
        *,
        auth_ready: bool = True,
        version_stderr: str = "",
        version_exit: int = 0,
    ) -> Path:
        path = self.bin_dir / name
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import json\n"
            "import sys\n"
            f"version = {version!r}\n"
            f"help_text = {help_text!r}\n"
            f"auth_ready = {auth_ready!r}\n"
            f"version_stderr = {version_stderr!r}\n"
            f"version_exit = {version_exit!r}\n"
            "if 'codex' in sys.argv[0] and sys.argv[1:] == ['login', 'status']:\n"
            "    print('Logged in using test' if auth_ready else 'Not logged in')\n"
            "    raise SystemExit(0 if auth_ready else 1)\n"
            "if 'claude' in sys.argv[0] and sys.argv[1:] == ['auth', 'status']:\n"
            "    print(json.dumps({'loggedIn': auth_ready, 'authMethod': 'test' if auth_ready else 'none'}))\n"
            "    raise SystemExit(0 if auth_ready else 1)\n"
            "if '--version' in sys.argv:\n"
            "    sys.stderr.write(version_stderr)\n"
            "    print(version)\n"
            "    raise SystemExit(version_exit)\n"
            "print(help_text)\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def invoke(
        self,
        *arguments: str,
        codex: Path | None = None,
        claude: Path | None = None,
        grok: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "AGENTCTL_CODEX_BIN": str(codex or self.codex),
                "AGENTCTL_CLAUDE_BIN": str(claude or self.claude),
                "AGENTCTL_GROK_BIN": str(grok or self.grok),
                "DEVCONTAINER_AI_CLI_CHANNEL": "stable",
                "DEVCONTAINER_CODEX_CLI_VERSION": "1.2.3",
                "DEVCONTAINER_CLAUDE_CODE_VERSION": "4.5.6",
                "DEVCONTAINER_GROK_CLI_VERSION": "1.0.3",
                "XAI_API_KEY": "test-only-placeholder",
            }
        )
        return subprocess.run(
            [sys.executable, str(AGENTCTL), *arguments],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_doctor_json_passes_capability_contract(self) -> None:
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["toolchain_channel"], "stable")
        self.assertEqual(payload["capabilities"]["codex"]["missing"], [])
        self.assertEqual(payload["capabilities"]["claude"]["missing"], [])
        self.assertEqual(payload["capabilities"]["grok"]["missing"], [])
        self.assertTrue(payload["capabilities"]["codex"]["auth"]["ready"])
        self.assertTrue(payload["capabilities"]["claude"]["auth"]["ready"])
        self.assertIsNone(payload["capabilities"]["grok"]["auth"]["ready"])
        self.assertEqual(
            payload["capabilities"]["grok"]["auth"]["verification"],
            "configuration-only",
        )
        scheduler = next(
            check for check in payload["checks"] if check["id"] == "scheduler.config"
        )
        self.assertEqual(scheduler["status"], "pass")
        self.assertEqual(scheduler["capacity"]["integration"], 1)
        self.assertEqual(scheduler["port_range"], [24000, 24999])

    def test_doctor_version_ignores_nonfatal_stderr_warning(self) -> None:
        noisy = self.make_provider("noisy-codex", "codex-cli 1.2.3", CODEX_HELP,
                                   version_stderr="WARNING: could not create PATH aliases: read-only filesystem\n")
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace), codex=noisy)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["capabilities"]["codex"]["version"], "codex-cli 1.2.3")

    def test_doctor_version_does_not_match_a_pin_mentioned_only_in_stderr(self) -> None:
        noisy = self.make_provider("wrong-codex", "codex-cli 9.9.9", CODEX_HELP,
                                   version_stderr="previous cached version was 1.2.3\n")
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace), codex=noisy)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["capabilities"]["codex"]["version"], "codex-cli 9.9.9")

    def test_doctor_version_preserves_stderr_only_cli_support(self) -> None:
        stderr_only = self.make_provider("stderr-codex", "", CODEX_HELP,
                                         version_stderr="codex-cli 1.2.3\n")
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace), codex=stderr_only)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["capabilities"]["codex"]["version"], "codex-cli 1.2.3")

    def test_doctor_version_failure_is_not_hidden_by_valid_stdout(self) -> None:
        failed = self.make_provider("failed-codex", "codex-cli 1.2.3", CODEX_HELP, version_exit=1)
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace), codex=failed)
        self.assertEqual(result.returncode, 1)
        check = next(row for row in json.loads(result.stdout)["checks"] if row["id"] == "provider.codex")
        self.assertEqual(check["status"], "fail")

    def test_doctor_rejects_missing_provider_capability(self) -> None:
        broken = self.make_provider("broken-claude", "4.5.6", "--print --output-format --agent --worktree")
        result = self.invoke("doctor", "--json", "--workspace", str(self.workspace), claude=broken)
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("--json-schema", payload["capabilities"]["claude"]["missing"])

    def test_doctor_rejects_incomplete_grok_headless_contract(self) -> None:
        broken = self.make_provider(
            "broken-grok",
            "grok 1.0.3 [stable]",
            "--agent --output-format --permission-mode --prompt-file --sandbox stdio",
        )
        result = self.invoke(
            "doctor", "--json", "--workspace", str(self.workspace), grok=broken
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("--json-schema", payload["capabilities"]["grok"]["missing"])

    def test_doctor_warns_without_failing_when_optional_provider_auth_is_missing(self) -> None:
        unauthenticated = self.make_provider(
            "unauthenticated-claude",
            "4.5.6 (Claude Code)",
            CLAUDE_HELP,
            auth_ready=False,
        )
        result = self.invoke(
            "doctor", "--json", "--workspace", str(self.workspace), claude=unauthenticated
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        auth = payload["capabilities"]["claude"]["auth"]
        self.assertFalse(auth["ready"])
        check = next(
            item for item in payload["checks"] if item["id"] == "provider.claude.auth"
        )
        self.assertEqual(check["status"], "warn")

    def test_legacy_inventory_is_read_only_and_lists_evidence(self) -> None:
        session = self.workspace / ".codex-second-agent" / "key" / "agents" / "reviewer" / "session_id"
        session.parent.mkdir(parents=True)
        session.write_text("session-id", encoding="utf-8")
        log = session.parent / "logs" / "events.jsonl"
        log.parent.mkdir()
        log.write_text("{}\n", encoding="utf-8")
        worktree = self.workspace / ".codex-worktrees" / "reviewer"
        worktree.mkdir(parents=True)
        subprocess.run(["git", "-C", str(self.workspace), "branch", "agent/reviewer"], check=True)

        before = session.read_text(encoding="utf-8")
        result = self.invoke("legacy", "inventory", "--json", "--workspace", str(self.workspace))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        codex = payload["backends"]["codex"]
        self.assertFalse(payload["destructive"])
        self.assertEqual(codex["session_count"], 1)
        self.assertEqual(codex["worktree_count"], 1)
        self.assertEqual(codex["branches"], ["agent/reviewer"])
        self.assertEqual(session.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
