"""Prepare edge CLI generations and atomically publish their executable directory.

The prefix itself stays a physical directory: its parent (usually /opt) need not
be writable. Linux renameat2 exchanges a legacy physical bin directory with the
new symlink without a missing-bin window. Later publications use os.replace.
Only Python's standard library and the existing npm/curl programs are used.
"""

import ctypes
import errno
import fcntl
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


TOOLS = {
    "CODEX_CLI_VERSION": ("codex", "@openai/codex"),
    "CLAUDE_CODE_VERSION": ("claude", "@anthropic-ai/claude-code"),
    "GEMINI_CLI_VERSION": ("gemini", "@google/gemini-cli"),
    "GROK_CLI_VERSION": ("grok", None),
    "OPENCODE_CLI_VERSION": ("opencode", None),
}
VERSION = re.compile(r"(?<![\w.+-])v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)(?![\w.+-])")
# A hung --version must not hold the startup lock forever. This is a per-probe
# cost cap, not a provider performance assumption.
PROBE_TIMEOUT = 20


def run(argv, lock_fd, **kwargs):
    # Descendants keep the directory lock if the coordinating process is killed.
    # It disappears automatically once that execution group has stopped, even
    # after a container restart; no PID files or stale-lock deletion are needed.
    return subprocess.run(argv, check=True, pass_fds=(lock_fd,), **kwargs)


def version(root, name, lock_fd):
    binary = root / "bin" / name
    args = [str(binary)]
    if name == "grok":
        args.append("--no-auto-update")
    args.append("--version")
    try:
        result = run(args, lock_fd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     text=True, timeout=PROBE_TIMEOUT)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    found = VERSION.search(result.stdout.strip())
    return found.group(1) if found else None


def requested_tool(key, wanted):
    name, package = TOOLS[key]
    if key == "OPENCODE_CLI_VERSION":
        # OpenCode 2 moved its npm distribution without changing the CLI name.
        package = "@opencode/cli" if int(wanted.split(".", 1)[0]) >= 2 else "opencode-ai"
    return name, package, wanted


def remove(path):
    if path.is_symlink() or not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path)


def copy(source, destination):
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def runtime_root(prefix):
    """Recognize only generations published by this helper, not arbitrary links."""
    binary_dir = prefix / "bin"
    if binary_dir.is_symlink():
        target = binary_dir.resolve()
        if (target.name == "bin" and target.parent.parent == prefix
                and target.parent.name.startswith(".ai-cli-generation-")):
            return target.parent
    return prefix


def relocate_links(root, mappings):
    """Rebase absolute internal links; keep ordinary npm relative links verbatim."""
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            target = os.readlink(path)
            if not os.path.isabs(target):
                continue
            for source, destination in mappings:
                try:
                    relative = Path(target).relative_to(source)
                except ValueError:
                    continue
                path.unlink()
                path.symlink_to(destination / relative)
                break


def snapshot(prefix, destination):
    source = runtime_root(prefix)
    destination.mkdir(mode=0o755)
    mappings = [(source / name, destination / name) for name in ("bin", "lib")]
    mappings += [((source / name).resolve(), destination / name) for name in ("bin", "lib")]
    for name in ("bin", "lib"):
        path = source / name
        if path.exists():
            # Copy the root directory even for legacy bin/lib symlink layouts.
            copy(path.resolve(), destination / name)
            for directory, dirs, files in os.walk(destination / name, followlinks=False):
                for entry in dirs + files:
                    link = Path(directory) / entry
                    if not link.is_symlink():
                        continue
                    target = os.readlink(link)
                    original = path.resolve() / link.relative_to(destination / name)
                    absolute = Path(os.path.abspath(original.parent / target))
                    replacement = absolute
                    for old, new in mappings:
                        try:
                            replacement = new / absolute.relative_to(old)
                            break
                        except ValueError:
                            continue
                    else:
                        # Relative links to other prefix resources still use
                        # the resource links below; escaping links stay outside.
                        if not os.path.isabs(target) and absolute.is_relative_to(source):
                            replacement = destination / absolute.relative_to(source)
                    if replacement.is_relative_to(destination) and not os.path.isabs(target):
                        replacement = (target if Path(os.path.abspath(link.parent / target)) == replacement
                                       else os.path.relpath(replacement, link.parent))
                    link.unlink()
                    link.symlink_to(replacement)
        else:
            (destination / name).mkdir()
    # Keep other prefix resources at their original paths, including user files.
    # Nothing outside bin/lib is installed into or copied over by the updater.
    for path in prefix.iterdir():
        if path.name not in ("bin", "lib") and not path.name.startswith(".ai-cli-"):
            (destination / path.name).symlink_to(path)


def private_directory(path):
    """Materialize a copied directory link before mutating any of its children."""
    if path.is_symlink():
        source = path.resolve(strict=True)
        path.unlink()
        copy(source, path)
    path.mkdir(exist_ok=True)


def overlay(source, destination):
    """Merge a clean npm installation without ever following old package links."""
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir() and not item.is_symlink() and target.is_dir():
            private_directory(target)
            overlay(item, target)
        else:
            remove(target)
            copy(item, target)


def verify(root, requests, lock_fd):
    for name, _, wanted in requests:
        actual = version(root, name, lock_fd)
        if actual != wanted:
            raise RuntimeError(f"{name} executable version is {actual or 'missing or unusable'}; "
                               f"expected {wanted}")


def publish(prefix, generation):
    link = prefix / (".ai-cli-previous-bin-" + uuid.uuid4().hex)
    link.symlink_to(generation.name + "/bin")
    try:
        live = prefix / "bin"
        if live.is_dir() and not live.is_symlink():
            libc = ctypes.CDLL(None, use_errno=True)
            exchange = libc.renameat2
            exchange.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                 ctypes.c_char_p, ctypes.c_uint]
            exchange.restype = ctypes.c_int
            if exchange(-100, os.fsencode(link), -100, os.fsencode(live), 2) != 0:
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error), str(live))
            # Retain the old physical bin, just like old runtime generations.
        else:
            os.replace(link, live)
    except Exception:
        link.unlink(missing_ok=True)
        raise


def synchronize(prefix, npm, requests, lock_fd):
    changed = []
    for name, package, wanted in requests:
        actual = version(prefix, name, lock_fd)
        if actual == wanted:
            print(f"devcontainer: {name} {wanted} already matches the host", flush=True)
        else:
            print(f"devcontainer: syncing {name} {actual or 'not-installed'} -> {wanted}", flush=True)
            changed.append((name, package, wanted))
    if not changed:
        return

    # Install into a *clean* prefix. Even absolute symlinks in an existing npm
    # tree cannot cause an installer to modify a live package through a copy.
    with tempfile.TemporaryDirectory(prefix="devcontainer-ai-cli-") as temporary:
        work = Path(temporary)
        installed = work / "installed"
        (installed / "bin").mkdir(parents=True)
        specs = [f"{package}@{wanted}" for _, package, wanted in changed if package]
        if specs:
            run([npm, "install", "--global", "--prefix", str(installed),
                 "--no-audit", "--no-fund", *specs], lock_fd)
        for name, _, wanted in changed:
            if name != "grok":
                continue
            arch = {"x86_64": "x86_64", "amd64": "x86_64",
                    "aarch64": "aarch64", "arm64": "aarch64"}.get(platform.machine())
            if not arch:
                raise RuntimeError(f"unsupported architecture for Grok edge sync: {platform.machine()}")
            base = os.environ.get("DEVCONTAINER_GROK_DOWNLOAD_BASE") or "https://x.ai/cli"
            curl = os.environ.get("DEVCONTAINER_AI_CLI_CURL_BIN") or "curl"
            output = installed / "bin/grok"
            run([curl, "-fsSL", f"{base}/grok-{wanted}-linux-{arch}", "-o", str(output)], lock_fd)
            output.chmod(0o755)
        verify(installed, changed, lock_fd)

        candidate = work / "candidate"
        snapshot(prefix, candidate)
        # Replace changed packages completely so files removed by a newer release
        # cannot survive an overlay. Unspecified packages remain in the snapshot.
        for name, package, _ in changed:
            replaced = ("opencode-ai", "@opencode/cli") if name == "opencode" else (package,)
            for old_package in replaced:
                if old_package:
                    path = candidate
                    relative = Path("lib/node_modules") / old_package
                    for part in relative.parent.parts:
                        path = path / part
                        private_directory(path)
                    remove(candidate / relative)
        overlay(installed, candidate)
        relocate_links(candidate, [(installed, candidate)])
        verify(candidate, requests, lock_fd)

        generation = Path(tempfile.mkdtemp(prefix=".ai-cli-generation-", dir=prefix))
        try:
            shutil.copytree(candidate, generation, symlinks=True, dirs_exist_ok=True)
            relocate_links(generation, [(candidate, generation)])
            # An embedded absolute install path can appear to work while the
            # temporary installation still exists. Remove both preparation
            # trees before the final check so it cannot mask that dependency.
            remove(installed)
            remove(candidate)
            # Verify at the durable path too: a package may embed its install
            # location. Publication never relies on package.json or temp paths.
            verify(generation, requests, lock_fd)
            publish(prefix, generation)
        except Exception:
            remove(generation)
            raise
        # No garbage collection: older running CLIs may still load their files.


def main():
    prefix = Path(sys.argv[1]).resolve()
    requests = [requested_tool(key, value) for key, value in
                (entry.split("=", 1) for entry in sys.argv[3:])]
    prefix.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(prefix, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno not in (errno.EAGAIN, errno.EACCES):
                raise
            raise RuntimeError(f"AI CLI sync already running for {prefix}; "
                               "retry after the previous execution group has stopped") from error
        synchronize(prefix, sys.argv[2], requests, lock_fd)
        print("devcontainer: host AI CLI versions synchronized")
    finally:
        os.close(lock_fd)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"error: AI CLI sync failed: {error}", file=sys.stderr)
        sys.exit(1)
