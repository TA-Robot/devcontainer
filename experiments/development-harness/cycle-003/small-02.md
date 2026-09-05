Repair structured-log secret redaction in the existing agentctl log viewer.

The current `_redact_log_text` in `scripts/agentctl_jobs.py` masks plain assignments
but leaves values visible in JSON such as `{"api_key":"fixture-private-value-123"}`.
Operational logs contain JSON objects and arrays, sometimes after a log prefix.
Keep the existing function signature and the real job-log view using it.

Requirements:

- Redact nonempty JSON string values whose decoded keys match the existing
  `SECRET_ENV_NAME` rule, plus `Authorization`, case-insensitively. Traverse nested
  objects and arrays. JSON string escapes in keys and values must work.
- Preserve valid JSON structure for complete JSON input. Preserve ordinary fields,
  numeric/boolean/null values, arrays and Unicode text; do not hide the whole log
  just because one field is sensitive. An exact whitespace format is not required.
- Handle JSON payloads after ordinary text prefixes and multiple log lines. Keep
  useful nonsensitive prefixes and neighboring log messages visible.
- Preserve existing plain assignment, Bearer/Basic Authorization, known token
  patterns and environment-value redaction. Do not change the raw log file or
  claim that every possible secret format can be recognized.
- Return a nonnegative integer redaction count; report a positive count when
  sensitive content is removed. Keep the public CLI/result contract compatible.
- Add meaningful regressions, including escaped strings, mixed ordinary/sensitive
  content, nested structures and existing formats. Run the relevant agentctl
  tests; report actual failures or unavailable checks without marking them passed.

Use only synthetic secret values in tests. No new runtime dependency, logging
service, provider/model change, or permission bypass is needed for this repair.
The expected scope is the log-redaction implementation and its tests/docs.
