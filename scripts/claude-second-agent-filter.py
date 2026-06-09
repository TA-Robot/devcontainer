#!/usr/bin/env python3
"""Claude Code の `--output-format stream-json` イベントを処理するフィルタ。

codex-second-agent-filter.py と同じCLIシグネチャで呼ばれる:
  filter.py <session_file> <raw_json:0|1> <prompt_file> <transcript_log> [agent] [effective_cd]

役割:
  - stream-json イベントから session_id を取り出して session_file に保存（次回 `-r` で resume）
  - assistant のテキストを stdout に出す
  - 1リクエスト=1行で transcript.jsonl に追記
"""
import json
import os
import sys
from datetime import datetime, timezone


def safe_write_session(session_file: str, sid: str) -> None:
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    tmp = session_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(sid)
    os.chmod(tmp, 0o600)
    os.replace(tmp, session_file)


def extract_assistant_text(obj: dict) -> list[str]:
    texts: list[str] = []
    message = obj.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text:
                    texts.append(text)
    return texts


def main() -> int:
    if len(sys.argv) < 5:
        print(
            "usage: claude-second-agent-filter.py <session_file> <raw_json:0|1> <prompt_file> <transcript_log>",
            file=sys.stderr,
        )
        return 2

    session_file = sys.argv[1]
    raw_json = sys.argv[2] == "1"
    prompt_file = sys.argv[3]
    transcript_log = sys.argv[4]
    agent_name = sys.argv[5] if len(sys.argv) >= 6 else None
    effective_cd = sys.argv[6] if len(sys.argv) >= 7 else None

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()
    except Exception:
        prompt = ""

    session_id = None
    written_session = None
    agent_texts: list[str] = []
    result_text = None
    is_error = False
    errors: list[str] = []

    for line in sys.stdin:
        line = line.rstrip("\n")
        if raw_json:
            print(line, flush=True)

        try:
            obj = json.loads(line)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue

        sid = obj.get("session_id")
        if isinstance(sid, str) and sid:
            session_id = sid
            if sid != written_session:
                try:
                    safe_write_session(session_file, sid)
                    written_session = sid
                except Exception as exc:
                    errors.append(
                        f"error: failed to persist session_id to {session_file}: {exc}"
                    )

        t = obj.get("type")
        if t == "assistant":
            for text in extract_assistant_text(obj):
                agent_texts.append(text)
                print(text, flush=True)
        elif t == "result":
            if obj.get("is_error"):
                is_error = True
            res = obj.get("result")
            if isinstance(res, str) and res:
                result_text = res

    # assistant テキストが取れなかった場合は result をフォールバックに使う
    if not agent_texts and result_text:
        print(result_text, flush=True)

    response = "\n\n".join(agent_texts).strip()
    if not response and result_text:
        response = result_text.strip()

    try:
        os.makedirs(os.path.dirname(transcript_log), exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "agent": agent_name,
            "cd": effective_cd,
            "prompt": prompt,
            "response": response,
            "is_error": is_error,
        }
        with open(transcript_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        errors.append(f"error: failed to append transcript to {transcript_log}: {exc}")

    for message in errors:
        print(message, file=sys.stderr, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
