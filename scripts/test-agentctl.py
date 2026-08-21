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
GROK_HELP = """--agent --allow --cwd --deny --json-schema --max-turns --no-memory --no-subagents
--output-format --permission-mode --prompt-file --sandbox stdio
"""


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

    def make_provider(self, name: str, version: str, help_text: str) -> Path:
        path = self.bin_dir / name
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"version = {version!r}\n"
            f"help_text = {help_text!r}\n"
            "print(version if '--version' in sys.argv else help_text)\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    def invoke(
        self,
        *arguments: str,
        claude: Path | None = None,
        grok: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "AGENTCTL_CODEX_BIN": str(self.codex),
                "AGENTCTL_CLAUDE_BIN": str(claude or self.claude),
                "AGENTCTL_GROK_BIN": str(grok or self.grok),
                "DEVCONTAINER_AI_CLI_CHANNEL": "stable",
                "DEVCONTAINER_CODEX_CLI_VERSION": "1.2.3",
                "DEVCONTAINER_CLAUDE_CODE_VERSION": "4.5.6",
                "DEVCONTAINER_GROK_CLI_VERSION": "1.0.3",
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
        scheduler = next(
            check for check in payload["checks"] if check["id"] == "scheduler.config"
        )
        self.assertEqual(scheduler["status"], "pass")
        self.assertEqual(scheduler["capacity"]["integration"], 1)
        self.assertEqual(scheduler["port_range"], [24000, 24999])

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
