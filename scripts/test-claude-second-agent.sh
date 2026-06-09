#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sa="${script_dir}/claude-second-agent"

tmp_paths=()

cleanup() {
  local path
  for path in "${tmp_paths[@]}"; do
    [[ -e "$path" || -L "$path" ]] || continue
    rm -rf "$path"
  done
}
trap cleanup EXIT

new_temp_dir() {
  local dir
  dir="$(mktemp -d)"
  tmp_paths+=("$dir")
  printf '%s\n' "$dir"
}

new_temp_file() {
  local file
  file="$(mktemp)"
  tmp_paths+=("$file")
  printf '%s\n' "$file"
}

new_repo() {
  local repo file
  repo="$(new_temp_dir)"
  git -C "$repo" init -q
  git -C "$repo" config user.email test@example.com
  git -C "$repo" config user.name test
  file="${2:-tracked.txt}"
  mkdir -p "$(dirname "$repo/$file")"
  : > "$repo/$file"
  git -C "$repo" add "$file"
  git -C "$repo" commit -qm "${1:-init}"
  printf '%s\n' "$repo"
}

# stream-json を出す claude スタブを作る。argv と PWD を CAPTURE_PATH に書き出す。
make_claude_stub() {
  local stub_dir="$1"
  cat >"$stub_dir/claude" <<'EOF'
#!/usr/bin/env bash
if [[ -n "${CAPTURE_PATH:-}" ]]; then
  {
    printf 'PWD=%s\n' "$PWD"
    printf '%s\n' "$@"
  } > "$CAPTURE_PATH"
fi
printf '%s\n' '{"type":"system","subtype":"init","session_id":"sess-1"}'
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"hello"}]},"session_id":"sess-1"}'
printf '%s\n' '{"type":"result","subtype":"success","is_error":false,"result":"hello","session_id":"sess-1"}'
EOF
  chmod +x "$stub_dir/claude"
}

assert_eq() {
  local expected="$1" actual="$2" message="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'not ok - %s\nexpected: %s\nactual:   %s\n' "$message" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_contains() {
  local haystack="$1" needle="$2" message="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'not ok - %s\nmissing: %s\nin: %s\n' "$message" "$needle" "$haystack" >&2
    exit 1
  fi
}

assert_not_contains() {
  local haystack="$1" needle="$2" message="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    printf 'not ok - %s\nunexpected: %s\nin: %s\n' "$message" "$needle" "$haystack" >&2
    exit 1
  fi
}

test_management_commands_are_side_effect_free() {
  local repo out err rc state_count
  repo="$(new_repo)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  (cd "$repo" && "$sa" agents >"$out" 2>"$err") && rc=0 || rc=$?
  assert_eq "0" "$rc" "agents succeeds before workspace init"
  state_count="$(find "$repo" -maxdepth 2 -name '.claude-second-agent' | wc -l | tr -d ' ')"
  assert_eq "0" "$state_count" "agents must not create state directories"

  (cd "$repo" && "$sa" --agent reviewer paths >"$out" 2>"$err") && rc=0 || rc=$?
  assert_eq "0" "$rc" "paths succeeds before workspace init"
  state_count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "1" "$state_count" "paths must not create a worktree"
  printf 'ok - management commands stay side-effect free\n'
}

test_forced_flags_and_model_overrides() {
  local repo stub_dir capture out err rc argv
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" - -- --model sonnet --output-format text --permission-mode plan --resume bogus <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then rc=0; else rc=$?; fi

  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_eq "0" "$rc" "claude execution should succeed"
  assert_contains "$argv" "-p" "print mode should be forced"
  assert_contains "$argv" "--output-format stream-json" "stream-json output should be forced"
  assert_contains "$argv" "--verbose" "verbose should be forced"
  assert_contains "$argv" "--dangerously-skip-permissions" "permission bypass should be forced"
  assert_contains "$argv" "--model opus" "forced default model should be passed"
  assert_not_contains "$argv" "sonnet" "user model override should be stripped"
  assert_not_contains "$argv" "--permission-mode" "user permission-mode should be stripped"
  assert_not_contains "$argv" "bogus" "user resume override should be stripped"
  printf 'ok - claude forces run flags and strips selection overrides\n'
}

test_model_env_override() {
  local repo stub_dir capture out err rc argv
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  if (cd "$repo" && CLAUDE_SA_MODEL=haiku CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then rc=0; else rc=$?; fi
  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_eq "0" "$rc" "claude execution with model env should succeed"
  assert_contains "$argv" "--model haiku" "CLAUDE_SA_MODEL should override the forced model"
  printf 'ok - CLAUDE_SA_MODEL overrides the forced model\n'
}

test_session_persist_and_resume() {
  local repo stub_dir capture out err rc state key argv session_count
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then rc=0; else rc=$?; fi
  assert_eq "0" "$rc" "first claude run should succeed"
  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_not_contains "$argv" "-r " "first run should not resume"

  state="$repo/.claude-second-agent"
  key="$(printf '%s' "$repo" | sha256sum | awk '{print $1}')"
  session_count="$(find "$state/$key/agents/default" -name session_id -type f | wc -l | tr -d ' ')"
  assert_eq "1" "$session_count" "first run should persist a session id"
  assert_eq "sess-1" "$(cat "$state/$key/agents/default/session_id")" "persisted session id should match event"

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" "again" >"$out" 2>"$err"); then rc=0; else rc=$?; fi
  assert_eq "0" "$rc" "second claude run should succeed"
  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_contains "$argv" "-r sess-1" "second run should resume the persisted session"
  printf 'ok - claude persists session id and resumes it\n'
}

test_subagent_rejects_external_paths() {
  local repo other stub_dir out err rc stderr_text
  repo="$(new_repo init project/file.txt)"
  other="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  (cd "$repo" && "$sa" workspace init . >/dev/null)

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --cd "$other" <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then rc=0; else rc=$?; fi
  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "sub-agent should reject external --cd"
  assert_contains "$stderr_text" "--cd must stay within configured workspace" "external --cd should be rejected"

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --add-dir "$other" <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then rc=0; else rc=$?; fi
  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "sub-agent should reject external --add-dir"
  assert_contains "$stderr_text" "--add-dir must stay within configured workspace" "external --add-dir should be rejected"
  printf 'ok - sub-agent rejects external filesystem paths\n'
}

test_subagent_runs_in_worktree() {
  local repo stub_dir capture out err rc argv pwd_line count
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  (cd "$repo" && "$sa" workspace init . >/dev/null)

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" --agent reviewer "hello" >"$out" 2>"$err"); then rc=0; else rc=$?; fi
  assert_eq "0" "$rc" "nondefault claude run should succeed"
  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  pwd_line="$(grep '^PWD=' "$capture" | sed 's/^PWD=//')"
  assert_not_contains "$argv" "--cd" "claude must not receive a --cd flag"
  assert_contains "$pwd_line" "/worktrees/reviewer" "claude should run inside the agent worktree"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "2" "$count" "nondefault execution should create a worktree"
  printf 'ok - sub-agent runs inside its worktree without a --cd flag\n'
}

test_internal_add_dir_rewritten_into_worktree() {
  local repo stub_dir capture out err rc argv
  repo="$(new_repo init project/shared.txt)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  (cd "$repo" && "$sa" workspace init . >/dev/null)

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --add-dir project <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then rc=0; else rc=$?; fi
  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_eq "0" "$rc" "workspace-internal --add-dir should be allowed"
  assert_contains "$argv" "/worktrees/reviewer/project" "internal --add-dir should be rewritten into the worktree"
  printf 'ok - workspace-internal add-dir is rewritten into worktree path\n'
}

test_transcript_is_recorded() {
  local repo stub_dir capture out err rc state key transcript_line stdout_text
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"
  make_claude_stub "$stub_dir"

  if (cd "$repo" && CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then rc=0; else rc=$?; fi
  state="$repo/.claude-second-agent"
  key="$(printf '%s' "$repo" | sha256sum | awk '{print $1}')"
  transcript_line="$(tail -n 1 "$state/$key/agents/default/logs/transcript.jsonl")"
  stdout_text="$(cat "$out")"
  assert_eq "0" "$rc" "claude run should succeed"
  assert_contains "$stdout_text" "hello" "assistant text should be printed"
  assert_contains "$transcript_line" '"response": "hello"' "transcript should record assistant response"
  assert_contains "$transcript_line" '"session_id": "sess-1"' "transcript should record the session id"
  printf 'ok - transcript records response and session id\n'
}

main() {
  test_management_commands_are_side_effect_free
  test_forced_flags_and_model_overrides
  test_model_env_override
  test_session_persist_and_resume
  test_subagent_rejects_external_paths
  test_subagent_runs_in_worktree
  test_internal_add_dir_rewritten_into_worktree
  test_transcript_is_recorded
}

main "$@"
