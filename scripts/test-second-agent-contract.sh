#!/usr/bin/env bash
# 実 CLI のフラグ表面（second-agent が依存している部分）が存在するかを確認する契約テスト。
# codex / claude が PATH に無い環境では各バックエンドをスキップする（CI smoke 用）。
set -euo pipefail

fail=0

check() {
  local label="$1" haystack="$2" needle="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    printf 'ok - %s: contains %s\n' "$label" "$needle"
  else
    printf 'not ok - %s: missing %s\n' "$label" "$needle" >&2
    fail=1
  fi
}

if command -v codex >/dev/null 2>&1; then
  help="$(codex exec --help 2>&1 || true)"
  check "codex exec" "$help" "--json"
  check "codex exec" "$help" "resume"
else
  printf 'skip - codex not in PATH\n'
fi

if command -v claude >/dev/null 2>&1; then
  help="$(claude --help 2>&1 || true)"
  check "claude" "$help" "--print"
  check "claude" "$help" "--output-format"
  check "claude" "$help" "stream-json"
  check "claude" "$help" "--resume"
  check "claude" "$help" "--dangerously-skip-permissions"
  check "claude" "$help" "--add-dir"
  check "claude" "$help" "--model"
else
  printf 'skip - claude not in PATH\n'
fi

if [[ $fail -ne 0 ]]; then
  printf 'CONTRACT TEST FAILED: a backend CLI flag we depend on is missing.\n' >&2
  exit 1
fi
printf 'ok - backend CLI contract satisfied (or skipped)\n'
