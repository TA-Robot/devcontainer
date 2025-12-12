#!/usr/bin/env python3
import json
import os
import sys


def safe_write_session(session_file: str, tid: str) -> None:
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    tmp = session_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(tid)
    os.chmod(tmp, 0o600)
    os.replace(tmp, session_file)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: codex-second-agent-filter.py <session_file> <raw_json:0|1>", file=sys.stderr)
        return 2

    session_file = sys.argv[1]
    raw_json = sys.argv[2] == "1"

    thread_id = None

    for line in sys.stdin:
        line = line.rstrip("\n")
        if raw_json:
            print(line, flush=True)

        try:
            obj = json.loads(line)
        except Exception:
            continue

        t = obj.get("type")
        if t == "thread.started":
            tid = obj.get("thread_id")
            if isinstance(tid, str) and tid:
                thread_id = tid
                try:
                    safe_write_session(session_file, tid)
                except Exception:
                    pass

        if raw_json:
            continue

        if t == "item.completed":
            item = obj.get("item") or {}
            if item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text:
                    print(text, flush=True)

    # raw_json=0 で agent_message が無いケースでもエラーにはしない
    _ = thread_id
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


