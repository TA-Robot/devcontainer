"""Real Byobu lifecycle checks with fake providers and an isolated socket."""

import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import tempfile
import termios
import time
import unittest


MIRA = Path(os.environ.get("MIRA_TEST_BIN", str(Path(__file__).with_name("mira"))))
PROVIDERS = ("codex", "claude", "gemini", "grok", "opencode")


class MiraTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mira-test-")
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.socket = f"mira-test-{os.getpid()}-{self.root.name[-6:]}"
        self.env = os.environ.copy()
        for name in ("TMUX", "BYOBU_CONFIG_DIR", "BYOBU_RUN_DIR", "BYOBU_BACKEND"):
            self.env.pop(name, None)
        self.env.update(HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
                        TERM="xterm-256color", MIRA_SOCKET=self.socket)
        for provider in PROVIDERS:
            binary = self.root / f"{provider}-fake"
            log = self.root / f"{provider}-args.json"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import json,sys,time\n"
                f"with open({str(log)!r}, 'a') as out: out.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                "time.sleep(60)\n"
            )
            binary.chmod(0o755)
            self.env[f"MIRA_{provider.upper()}_BIN"] = str(binary)

    def tearDown(self):
        subprocess.run(["byobu-tmux", "-L", self.socket, "kill-server"],
                       env=self.env, capture_output=True, timeout=10)
        self.temp.cleanup()

    def run_mira(self, *args, cwd=None):
        return subprocess.run([str(MIRA), *args], cwd=cwd or self.workspace,
                              env=self.env, capture_output=True, text=True, timeout=15)

    def sessions(self):
        result = subprocess.run(["byobu-tmux", "-L", self.socket, "list-sessions",
                                 "-F", "#{session_name}"], env=self.env,
                                capture_output=True, text=True, timeout=10)
        return result.stdout.splitlines() if result.returncode == 0 else []

    def wait_for_log(self, provider):
        path = self.root / f"{provider}-args.json"
        deadline = time.monotonic() + 6
        while not path.exists():
            self.assertLess(time.monotonic(), deadline, f"{provider} did not start")
            time.sleep(.05)
        return json.loads(path.read_text().splitlines()[0])

    def test_reuses_provider_and_workspace_and_passes_flags(self):
        expected = {"codex": ["--model", "two words"], "claude": [],
                    "gemini": ["--approval-mode=yolo", "--no-sandbox"], "grok": [],
                    "opencode": ["--auto"]}
        for provider in PROVIDERS:
            extra = ["--model", "two words"] if provider == "codex" else []
            result = self.run_mira(provider, *extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.wait_for_log(provider), expected[provider])
        self.assertEqual(len(self.sessions()), len(PROVIDERS))
        again = self.run_mira("codex", "--model", "changed")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("startup arguments were not applied", again.stderr)
        self.assertEqual(len(self.sessions()), len(PROVIDERS))
        self.assertEqual(len((self.root / "codex-args.json").read_text().splitlines()), 1)
        listing = self.run_mira("list")
        self.assertEqual(listing.returncode, 0, listing.stderr)
        for provider in PROVIDERS:
            self.assertIn(provider, listing.stdout)
        self.assertIn(str(self.workspace), listing.stdout)
        other = self.root / "other-project"
        other.mkdir()
        self.assertEqual(self.run_mira("codex", cwd=other).returncode, 0)
        self.assertEqual(len(self.sessions()), len(PROVIDERS) + 1)

    def test_list_selection_survives_terminal_disconnect(self):
        self.assertEqual(self.run_mira("codex").returncode, 0)
        self.wait_for_log("codex")
        self.assertEqual(self.run_mira("claude").returncode, 0)
        self.wait_for_log("claude")
        sessions = self.sessions()
        self.assertEqual(len(sessions), 2)
        session = sessions[1]
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(self.workspace)
            os.execvpe(str(MIRA), [str(MIRA), "list"], self.env)
        try:
            fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
            output = b""
            deadline = time.monotonic() + 10
            while b"Select session" not in output:
                self.assertLess(time.monotonic(), deadline, output[-300:])
                readable, _, _ = select.select([master], [], [], .2)
                if readable:
                    output += os.read(master, 4096)
            os.write(master, b"2\n")
            deadline = time.monotonic() + 10
            while True:
                clients = subprocess.run(
                    ["byobu-tmux", "-L", self.socket, "list-clients", "-F", "#{client_session}"],
                    env=self.env, capture_output=True, text=True, timeout=10)
                if session in clients.stdout.splitlines():
                    break
                self.assertLess(time.monotonic(), deadline, clients.stderr)
                time.sleep(.1)
            os.kill(pid, signal.SIGHUP)
            deadline = time.monotonic() + 6
            while True:
                finished, _ = os.waitpid(pid, os.WNOHANG)
                if finished:
                    pid = 0
                    break
                self.assertLess(time.monotonic(), deadline)
                time.sleep(.1)
            self.assertEqual(self.sessions(), sessions)
            self.assertEqual(self.run_mira("codex").returncode, 0)
            self.assertEqual(len((self.root / "codex-args.json").read_text().splitlines()), 1)
        finally:
            if pid:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            os.close(master)

    def test_empty_list_and_invalid_provider(self):
        result = self.run_mira("list")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no running sessions", result.stdout)
        result = self.run_mira("unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.sessions(), [])


if __name__ == "__main__":
    unittest.main()
