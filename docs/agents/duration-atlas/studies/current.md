# Agent Duration Study Report

This is a deterministic, content-free observational report built from a validated aggregate atlas. It does not read raw run payloads or artifact content.

## Methodology

- Aggregate method: <code>case-nested-observed-v2</code>
- Duration values are emitted only as raw case points and aggregate-provided observed min/max ranges.
- One observation is shown only as one raw point. A range requires at least two points in the same case stratum.
- Requested generation values remain distinct from applied values; an applied value appears only when the atlas records status `applied`.
- Criterion scores and failed criterion IDs are emitted only from each sample's content-free quality evidence. Missing scores remain unavailable and are not inferred.
- The report is descriptive only. It produces no provider/model ranking, automatic route, or preferred configuration.

## Observation window and provenance

- First observed: <code>2026-08-26T11:34:19.672Z</code>
- Last observed: <code>2026-08-27T06:07:15.461Z</code>
- Source run-set digest: <code>sha256:402b7a5bb5efa351bd31f768a0058f296a2902a5586d327347bf8fac86244b3f</code>
- Source run schema: <code>2</code>
- Source records: 108
- Canonical source bytes: 808990
- Atlas counts: series=104; case-strata=104; samples=108
- Report resource caps: max-series=500; max-cases=500; max-output-bytes=8388608

## Family and size coverage

- Supplied catalog: <code>duration-atlas-calibration</code>, revision <code>3</code>
- Supplied catalog digest: <code>sha256:c89c127d5b02d0e72989508f6a7d7c0b9d1ed828ca61aa616db41ad90cb0f7d0</code>
- Atlas case catalog digest(s): <code>sha256:5e1f6f6f3d29ab4e9d0e73bacb870d2bec32d05d6edabcebe784a15e445f6c79</code>, <code>sha256:c89c127d5b02d0e72989508f6a7d7c0b9d1ed828ca61aa616db41ad90cb0f7d0</code>, <code>sha256:d339d14fff72cf7ac4d1213805d3e049adedc0e2268242b19d26dbae5aafb73d</code>
- Digest compatibility: mismatch; the atlas digest set does not identify supplied catalog revision <code>3</code>. The earlier catalog revision number is not encoded in the atlas.
- Observed supplied-catalog cells: 36 / 36
- Unmeasured supplied-catalog cells: 0 / 36
- Reference corpus check: 36 supplied cells; the checked-in target is 36.

| Family | S | M | L |
| --- | --- | --- | --- |
| repository-trace | F01-S-PY-001: observed (4 strata, 4 runs) | F01-M-PYJS-001: observed (1 stratum, 1 run) | F01-L-PYBASHJS-001: observed (1 stratum, 1 run) |
| code-review | F02-S-PY-001: observed (1 stratum, 1 run) | F02-M-PY-001: observed (4 strata, 4 runs) | F02-L-PYBASHJS-001: observed (1 stratum, 1 run) |
| failing-test-diagnosis | F03-S-PY-001: observed (1 stratum, 1 run) | F03-M-PY-001: observed (1 stratum, 1 run) | F03-L-PYBASH-001: observed (7 strata, 7 runs) |
| bounded-implementation | F04-S-PY-001: observed (13 strata, 17 runs) | F04-M-PY-001: observed (1 stratum, 1 run) | F04-L-PYBASH-001: observed (10 strata, 10 runs) |
| refactor-migration | F05-S-PY-001: observed (1 stratum, 1 run) | F05-M-PY-001: observed (4 strata, 4 runs) | F05-L-PYBASH-001: observed (1 stratum, 1 run) |
| test-design | F06-S-PY-001: observed (1 stratum, 1 run) | F06-M-PY-001: observed (1 stratum, 1 run) | F06-L-PYBASH-001: observed (4 strata, 4 runs) |
| documentation-runbook | F07-S-MD-001: observed (4 strata, 4 runs) | F07-M-MDBASH-001: observed (1 stratum, 1 run) | F07-L-MDPYBASH-001: observed (1 stratum, 1 run) |
| architecture-design | F08-S-MDJSON-001: observed (1 stratum, 1 run) | F08-M-MDJSON-001: observed (4 strata, 4 runs) | F08-L-MDJSON-001: observed (4 strata, 4 runs) |
| security-isolation | F09-S-PY-001: observed (2 strata, 2 runs) | F09-M-PYBASH-001: observed (1 stratum, 1 run) | F09-L-PYBASHDOCKER-001: observed (7 strata, 7 runs) |
| performance-resource | F10-S-PY-001: observed (4 strata, 4 runs) | F10-M-PY-001: observed (1 stratum, 1 run) | F10-L-PYBASH-001: observed (1 stratum, 1 run) |
| devcontainer-operations | F11-S-BASH-001: observed (1 stratum, 1 run) | F11-M-BASH-001: observed (4 strata, 4 runs) | F11-L-BASHDOCKER-001: observed (1 stratum, 1 run) |
| evidence-synthesis | F12-S-MDJSON-001: observed (1 stratum, 1 run) | F12-M-MDJSON-001: observed (1 stratum, 1 run) | F12-L-MDJSON-001: observed (8 strata, 8 runs) |

Unmeasured catalog case IDs (0):
- none

Atlas case IDs absent from supplied catalog (0):
- none

Case revision differences (0):
- none

Case identity/profile differences (0):
- none

## Series 1

- Series ID: <code>sha256:00cb4a0c341f4e78b1a3bbd7d173ec2125391ffd030cdadd20a2857fbd17ca2d</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:02:47.109Z</code> to <code>2026-08-27T02:02:47.109Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 1: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:411e61f1802c9123d6ea4d496f379da7d651c6161f536e972ace9aa3e0f284de</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:02:47.109Z</code> to <code>2026-08-27T02:02:47.109Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-006-81f4af8229d34d0f=236879.158 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-006-81f4af8229d34d0f | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=236879.158 ms; declared-cap=1800000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 2

- Series ID: <code>sha256:01f5e3fc0e2bb4b42fca5b24beecd4141e6e4a2ea6cd6a2e90bc85809dce2d17</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:21:46.054Z</code> to <code>2026-08-27T03:21:46.054Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 2: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:d1e3ce8659044143457e43370a1394f6ed71c15100dba2fb3817d8fc8a27810f</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:21:46.054Z</code> to <code>2026-08-27T03:21:46.054Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-923734856e7421d3=364107.089 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-923734856e7421d3 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=364107.089 ms; declared-cap=1800000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 3

- Series ID: <code>sha256:02e00b6709c3e26abc157dfb63b98f5b94245ada19141cda6043f40f7014c359</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:57:36.271Z</code> to <code>2026-08-27T02:57:36.271Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "M-coupled-instrumented-performance-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 3: F10-M-PY-001 revision 1

- Stratum ID: <code>sha256:b6f93915c197ef89552d10a331d4892e6928e92d632c90e49fe11f8dcf9bfc11</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:57:36.271Z</code> to <code>2026-08-27T02:57:36.271Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:f26bdbacdde56e7c93df771a0c93cf78d7b37da75be33618272bc54b2be4432a",
      "case_id": "F10-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "917e78db55172162ddb3410722605ef931adf419",
        "bundle_digest": "sha256:6230bb40eb33719765be0d3ac238120550adb07ec7ef82a89387483013e73194",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-029-e8988878c3986d64=164556.497 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-029-e8988878c3986d64 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=164556.497 ms; declared-cap=1800000 ms | fail | 8 | criterion; 2/8; ratio=0.25; public=2/2; hidden=0/6; all-checks-required=true | perf-instrumentation-consistency, perf-cold-warm-separation, perf-cache-diagnosis, perf-secondary-costs, perf-distribution, perf-output-equivalence |

## Series 4

- Series ID: <code>sha256:034d3ed5ec309fba2f21958dbb69b59524168ed9688555efa0379e775b76fe80</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:52:59.928Z</code> to <code>2026-08-27T02:52:59.928Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "M-coupled-deterministic-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 4: F04-M-PY-001 revision 1

- Stratum ID: <code>sha256:55e9665eb2b3f483e11593151feb2840d7e23a17f8211f8767e098da76c28f9d</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:52:59.928Z</code> to <code>2026-08-27T02:52:59.928Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c1ed30e6ed80274aa12edf5a8609591b58a3a60ad083984a1b4c74c219263c23",
      "case_id": "F04-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "72480b48af065c493ea3f46675221430d8567b0b",
        "bundle_digest": "sha256:d409759532c0b2a35bbe8884eef4e1dc0facf905ffe871518f62e7031e29aa72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-026-39f72c8bd04ecf35=68438.135 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-026-39f72c8bd04ecf35 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=68438.135 ms; declared-cap=1800000 ms | fail | 3 | criterion; 2/3; ratio=0.666667; public=1/1; hidden=1/2; all-checks-required=true | hidden-round-trip-storage |

## Series 5

- Series ID: <code>sha256:04f7e96f129809f486c0fd797e9dbdde62bbccd87b74e2de48cde9e9bff06dcd</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:38:37.856Z</code> to <code>2026-08-27T03:38:37.856Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "S-local-benchmark-diagnosis-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 5: F10-S-PY-001 revision 1

- Stratum ID: <code>sha256:0362a20c3390e55dd3e203228ab79d73fd71000042ba93dec9bb97ab0ef4e5e9</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:38:37.856Z</code> to <code>2026-08-27T03:38:37.856Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c0efce6cb9cc78eda89064eb70cc2c2634495c331e19263b4fa38d57b25d3242",
      "case_id": "F10-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6d14dfbff162662b293ebe74acbbbfcacd4bcb64",
        "bundle_digest": "sha256:f16e55ddfe14f59a8d93568e3dab48cbf2415d3e35e93e12ed5c6e52ae322ceb",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-006-1fb427e3921a635c=118368.565 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-006-1fb427e3921a635c | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=118368.565 ms; declared-cap=1800000 ms | fail | 7 | criterion; 2/7; ratio=0.285714; public=2/2; hidden=0/5; all-checks-required=true | perf-repro-command, perf-scaling-evidence, perf-root-cause, perf-distractor-rejected, perf-claim-bounded |

## Series 6

- Series ID: <code>sha256:062e300b7339c145ce4c1a9be35ce8eb2e9ec3ef3e801552b9a4e2669c783db0</code>
- Study ID: <code>duration-atlas-wave1</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:34:19.672Z</code> to <code>2026-08-26T11:34:19.672Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "low",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-terra",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d"
      }
    ]

### Case observations

### Case 6: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:d3ccc539968edd745364797e53e468a5156e18a89653ede0bc7d9b489f9704e6</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:34:19.672Z</code> to <code>2026-08-26T11:34:19.672Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | codex-f04-s-terra-low-20260826-r02=40936.286 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-s-terra-low-20260826-r02 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=40936.286 ms; declared-cap=300000 ms | fail | 2 | aggregate-check; 1/2; ratio=0.5; public=0/0; hidden=0/0; all-checks-required=true | f04-s-python-hidden-v1 |

## Series 7

- Series ID: <code>sha256:0886910fe86c8ebd03e24528755295143f8cd380ff9a699489a82e350d49e281</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>same-case-repeat</code>
- Observation window: <code>2026-08-26T18:11:27.450Z</code> to <code>2026-08-26T18:13:12.638Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "claude",
        "cli_source": "container-image",
        "cli_version": "2.1.220",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "claude.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "opus",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "claude",
        "role": "implementer",
        "runtime_image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d"
      }
    ]

### Case observations

### Case 7: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:2895e1c9e5bbcf9b449b1367fabc5e6e4a2af0db8980d0c794f50f334a971a6a</code>
- Evidence state: <code>same-case-repeat</code>
- Observation window: <code>2026-08-26T18:11:27.450Z</code> to <code>2026-08-26T18:13:12.638Z</code>
- Runs / observation blocks: 3 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=3 |
| Censoring | complete=3; right=0; administrative=0 |
| First artifact | progress=0; not-observed=3; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | 3 same-case observations; raw points | claude-f04-s-opus-medium-20260827-r01=2004.757 ms; claude-f04-s-opus-medium-20260827-r02=2162.787 ms; claude-f04-s-opus-medium-20260827-r03=1951.568 ms | 1951.568–2162.787 ms (observed min/max) |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| claude-f04-s-opus-medium-20260827-r01 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=configuration | complete-terminal; observed-terminal=2004.757 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |
| claude-f04-s-opus-medium-20260827-r02 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=configuration | complete-terminal; observed-terminal=2162.787 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |
| claude-f04-s-opus-medium-20260827-r03 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=configuration | complete-terminal; observed-terminal=1951.568 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |

## Series 8

- Series ID: <code>sha256:0ae47f4c17a544001afc52016194f8452db585a59014dde0860e3cdfcbd2b145</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:03:55.741Z</code> to <code>2026-08-27T03:03:55.741Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "S-local-mutation-test-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 8: F06-S-PY-001 revision 1

- Stratum ID: <code>sha256:ad455650fb2534392fa27878d8e62d2b0472ddaf22ad5059275365d73e053ca3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:03:55.741Z</code> to <code>2026-08-27T03:03:55.741Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:83f6dabffa995d10d05d2531e0689686bc80428b1a0e723944903d28db183a69",
      "case_id": "F06-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "2dbf6b5603028e4654793e0b8614c7820002093c",
        "bundle_digest": "sha256:c2af8beb7a0da33398edbdc6bd5ce648d7f1216539b7e7543b04743d2c1416e0",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-031-981e1065e16f96d7=65814.743 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-031-981e1065e16f96d7 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=65814.754 ms; declared-cap=1800000 ms | pass | 7 | criterion; 7/7; ratio=1.0; public=2/2; hidden=5/5; all-checks-required=true | none |

## Series 9

- Series ID: <code>sha256:0c3edc3341ac554d37ff6a36cf67253f735022e341eae9bfc4a0c199fe2b5313</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:41:39.372Z</code> to <code>2026-08-26T18:41:39.372Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 9: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:b4d0bed8ec56822ed8b7ad149c2de413993def49087c25c1b63a795d15c08ee6</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:41:39.372Z</code> to <code>2026-08-26T18:41:39.372Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | grok-f04-l-46-medium-20260827-r01=86564.209 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-l-46-medium-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=86564.216 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 10

- Series ID: <code>sha256:0d9984d767237975edcf687a2b6b11c6102f4a332d8e87a2610757b31e93a12c</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:03:47.728Z</code> to <code>2026-08-27T05:03:47.728Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 10: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:ec1b7c9d3bc70c817f1784ecc1ca9e548865826e5049fc725563725c9c817485</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:03:47.728Z</code> to <code>2026-08-27T05:03:47.728Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-005-02d98291e743f9fc=335103.998 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-005-02d98291e743f9fc | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=335103.998 ms; declared-cap=1800000 ms | fail | 12 | criterion; 6/12; ratio=0.5; public=3/3; hidden=3/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 11

- Series ID: <code>sha256:15926ec0410cfa8b3896c721c50526dfba999d754e9a05b76f2beabb1a736c8b</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:58:32.215Z</code> to <code>2026-08-27T03:58:32.215Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "xhigh",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 11: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:69d4e628b9c18ee8da323468cb737f4ad533f6237caa25dfcc7c63208f386261</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:58:32.215Z</code> to <code>2026-08-27T03:58:32.215Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-b4b5e02070295756=400639.065 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-b4b5e02070295756 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=400639.065 ms; declared-cap=3600000 ms | fail | 11 | criterion; 4/11; ratio=0.363636; public=3/3; hidden=1/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-bind-injection, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-unknown-honesty |

## Series 12

- Series ID: <code>sha256:16fe63b0a036fe985c5bc34b0346f4273c18f5694d78bba65e288fd4db2c7dc8</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:33:32.385Z</code> to <code>2026-08-27T02:33:32.385Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "L-cross-boundary-structured-trace-devcontainer",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 12: F01-L-PYBASHJS-001 revision 1

- Stratum ID: <code>sha256:a172ea3278fbd89278ca330031841250273c55afdff57b2238a53e2754eb901a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:33:32.385Z</code> to <code>2026-08-27T02:33:32.385Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:1559861896e50ee5d7bb4c485f167cfa7bf21b0ead29c5b017d736b0c9815081",
      "case_id": "F01-L-PYBASHJS-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "c5e72460d4f5fd2d3905a5eaeb283638b1bc235e",
        "bundle_digest": "sha256:a4cfe9b18d7b4c77e48083bc1ab2fce14457184d4b54fad7b2c64009e35cbb1b",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-018-db68c23ca7e2058f=178055.788 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-018-db68c23ca7e2058f | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=178055.788 ms; declared-cap=1800000 ms | fail | 10 | criterion; 5/10; ratio=0.5; public=4/4; hidden=1/6; all-checks-required=true | trace-lifecycle-nodes, trace-boundary-artifacts, trace-runtime-chain, trace-recovery-ownership, trace-evidence-integrity |

## Series 13

- Series ID: <code>sha256:175ab37808b88de8baf5e30e473d46c862ee3b04b689354b1cf9b46e827bf852</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:56:28.843Z</code> to <code>2026-08-27T02:56:28.843Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 13: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:d8124f3c13de3fbfab8d0b43eeb09ab37ae6f70f50114cd3ef03505778d4204d</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:56:28.843Z</code> to <code>2026-08-27T02:56:28.843Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-028-dbd23105c9d8f9c2=62955.684 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-028-dbd23105c9d8f9c2 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=62955.684 ms; declared-cap=1800000 ms | fail | 5 | criterion; 4/5; ratio=0.8; public=1/1; hidden=3/4; all-checks-required=true | hidden-empty-result |

## Series 14

- Series ID: <code>sha256:187b1c94ac2af82c509c88a80ae322a63461afff5a943586cd93ea5205606c38</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:38:53.848Z</code> to <code>2026-08-27T05:38:53.848Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 14: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:a897fe3d44230ba259edc7a540aa0a74955f45187a386077a0996f35d19b70ca</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:38:53.848Z</code> to <code>2026-08-27T05:38:53.848Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-011-2af82cf0bd3c0e93=288450.221 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-011-2af82cf0bd3c0e93 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=288450.221 ms; declared-cap=1800000 ms | fail | 11 | criterion; 5/11; ratio=0.454545; public=3/3; hidden=2/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-unknown-honesty |

## Series 15

- Series ID: <code>sha256:1c2de44e2a2520d54f9cafa12926926970b1625fa5bfa8752a56d1c70dccba19</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:28:34.896Z</code> to <code>2026-08-27T05:28:34.896Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 15: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:98f4b4834e2eb45c6b0ebd7c5651a1ed6bc19aae8c5e9089b5f565c472ec2ccf</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:28:34.896Z</code> to <code>2026-08-27T05:28:34.896Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-008-13a21f3548bff40a=278896.326 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-008-13a21f3548bff40a | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=278896.326 ms; declared-cap=1800000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 16

- Series ID: <code>sha256:1ea4d57e641423811b6a424f3fd6c8ae3a33491216e498f9babdcea0f976ef03</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:18:16.190Z</code> to <code>2026-08-26T18:18:16.190Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:4a09987c2dc43d2d214f4358bbd6fb4d8495d8ed31e680d5cc1a30a3981d38f9",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "claude",
        "cli_source": "container-image",
        "cli_version": "2.1.220",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "claude.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "opus",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "claude",
        "role": "implementer",
        "runtime_image_digest": "sha256:4a09987c2dc43d2d214f4358bbd6fb4d8495d8ed31e680d5cc1a30a3981d38f9"
      }
    ]

### Case observations

### Case 16: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:f4ab1e17626d1ae75af07994ab3b1a717260703acf927b262b8edeb0648e778b</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:18:16.190Z</code> to <code>2026-08-26T18:18:16.190Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | claude-f04-s-opus-medium-20260827-r04=4024.107 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| claude-f04-s-opus-medium-20260827-r04 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=sandbox | complete-terminal; observed-terminal=4024.107 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |

## Series 17

- Series ID: <code>sha256:20b03449302fa307a406736fe70c2ce48d63fbc69954995ecd97c339a13434c9</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>same-case-repeat</code>
- Observation window: <code>2026-08-26T18:21:40.671Z</code> to <code>2026-08-26T18:23:21.886Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "claude",
        "cli_source": "container-image",
        "cli_version": "2.1.220",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "claude.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "opus",
          "requested_source": "flag",
          "resolved_id": "claude-opus-5"
        },
        "permission_mode": "automatic",
        "provider": "claude",
        "role": "implementer",
        "runtime_image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01"
      }
    ]

### Case observations

### Case 17: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:97ae203f00ecd8e3090936ffb9afa62f5052bd5dd050e11e4b8785290f484182</code>
- Evidence state: <code>same-case-repeat</code>
- Observation window: <code>2026-08-26T18:21:40.671Z</code> to <code>2026-08-26T18:23:21.886Z</code>
- Runs / observation blocks: 3 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=3 |
| Censoring | complete=3; right=0; administrative=0 |
| First artifact | progress=0; not-observed=3; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | 3 same-case observations; raw points | claude-f04-s-opus-medium-20260827-r05=6636.095 ms; claude-f04-s-opus-medium-20260827-r06=6389.315 ms; claude-f04-s-opus-medium-20260827-r07=6384.674 ms | 6384.674–6636.095 ms (observed min/max) |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| claude-f04-s-opus-medium-20260827-r05 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-startup-unknown | complete-terminal; observed-terminal=6636.095 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |
| claude-f04-s-opus-medium-20260827-r06 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-startup-unknown | complete-terminal; observed-terminal=6389.315 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |
| claude-f04-s-opus-medium-20260827-r07 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-startup-unknown | complete-terminal; observed-terminal=6384.674 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |

## Series 18

- Series ID: <code>sha256:2e8fd628e27afc97cb2eab7e9b630690afe4367f939807cfa2c9dd210d39bfa6</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:10:04.130Z</code> to <code>2026-08-27T05:10:04.130Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "M-coupled-interface-migration-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 18: F05-M-PY-001 revision 1

- Stratum ID: <code>sha256:73ff9f68efb1016a1f7a1b75e274a507fc8da3a7fe6c49e8b95f9a82cb686b38</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:10:04.130Z</code> to <code>2026-08-27T05:10:04.130Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:4e93974668ce5719b2b52f07d19b5be28cd26be01add5b7ab05763e7c313e9d7",
      "case_id": "F05-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0dac3f22518b2044bc1e5be41c147adf01fb5b74",
        "bundle_digest": "sha256:fa4d0981251cacf99ac21298ff3b4bc8d36bd98e4e5b54b8b6c4be968cbdec98",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-007-5ef5a801077ce49c=57595.624 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-007-5ef5a801077ce49c | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=57595.624 ms; declared-cap=1800000 ms | fail | 7 | criterion; 2/7; ratio=0.285714; public=2/2; hidden=0/5; all-checks-required=true | migration-all-callers, migration-policy-lifecycle, migration-compat-bytes, migration-warning-once, migration-api-surface |

## Series 19

- Series ID: <code>sha256:3863f64410644d02ab5d10f4c67b3419b07f2d55489714e616ed25c762868814</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:41:37.237Z</code> to <code>2026-08-27T04:41:37.237Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "max",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 19: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:f741ca3adc6f78773f35df20c53c9d539d96541d9bb20287a6a184ddf3f2c80d</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:41:37.237Z</code> to <code>2026-08-27T04:41:37.237Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-5f81d658366f99c7=657648.615 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-5f81d658366f99c7 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=657648.615 ms; declared-cap=3600000 ms | fail | 11 | criterion; 3/11; ratio=0.272727; public=3/3; hidden=0/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-bind-injection, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-control-counterexamples, threat-unknown-honesty |

## Series 20

- Series ID: <code>sha256:3a58f50f97791b5b885e3ca7215dba382b583f48b3169b2daed4ef84f8a18ee0</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:56:07.727Z</code> to <code>2026-08-27T03:56:07.727Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "xhigh",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 20: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:dabdc909274058e8b6a51cab79e36e24645d80a8bcb597173801e3ed9c52da2a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:56:07.727Z</code> to <code>2026-08-27T03:56:07.727Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-183a3c863cef1999=140109.287 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-183a3c863cef1999 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=140109.287 ms; declared-cap=3600000 ms | fail | 9 | criterion; 7/9; ratio=0.777778; public=3/3; hidden=4/6; all-checks-required=true | diagnosis-ordering-cause, diagnosis-cleanup-bounded |

## Series 21

- Series ID: <code>sha256:3abff7201275379fede76d7a918a4771c09ed6925f8a06bfcb390ad97f47e391</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:26:23.410Z</code> to <code>2026-08-27T05:26:23.410Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "M-coupled-calibrated-architecture",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 21: F08-M-MDJSON-001 revision 1

- Stratum ID: <code>sha256:209e2e7353a421c6366ff663a89b5e6a2516421d2d92df3dfd6a07e8b7985890</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:26:23.410Z</code> to <code>2026-08-27T05:26:23.410Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:b387c811c5371e97f84eba0e6793e2ad86f743c6eb3e3f45109f1b66092d2c62",
      "case_id": "F08-M-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1508653b1462b14f5ac7d145ee36cb821a0f5373",
        "bundle_digest": "sha256:bddda853cc6aebed863694e3dcfd79a3b562ce026f31c2e66d1ce3fd9822fc0d",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-007-6ba767ed3c7f3033=128448.926 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-007-6ba767ed3c7f3033 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=128448.926 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | design-invariant-coverage, design-option-counterexamples, design-migration-observability, design-unknown-honesty |

## Series 22

- Series ID: <code>sha256:3f9c182aa42361a8fa377c2c9b87995b6898c2c5faceac8cb89bfbb840f80f3a</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:14:14.806Z</code> to <code>2026-08-27T02:14:14.806Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "S-local-seeded-bypass-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 22: F09-S-PY-001 revision 1

- Stratum ID: <code>sha256:5f2c5cadee481d33686313534fff35f9f3b4aa650ac7042b1b1f5a79b4e088a5</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:14:14.806Z</code> to <code>2026-08-27T02:14:14.806Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d5f69e1314f77f79cf86fd20623aa7170e6a9b4e688534c5e74481b0ea99139a",
      "case_id": "F09-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e1c135a9951c95047cd10b954916efe050c67f92",
        "bundle_digest": "sha256:1c4d59bc328976f88b0b9d94832f320bb5203413ccbc7ec9bb94d20b21b37915",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | run-010-ddfa3e87bf3ce516=14638.748 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-010-ddfa3e87bf3ce516 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-startup-unknown | complete-terminal; observed-terminal=14638.748 ms; declared-cap=1800000 ms | not-run | 0 | unavailable | unavailable |

## Series 23

- Series ID: <code>sha256:42704be884542d6ea822d6741fb79290e9f4f97d8eef4eecb6f8c5b1a553d75d</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:51:53.647Z</code> to <code>2026-08-27T05:51:53.647Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "xhigh",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "xhigh",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 23: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:d2a8953168182ddd4f7a362838128a7a6ac0bf925b1cfba777c43f6d1223fbfd</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:51:53.647Z</code> to <code>2026-08-27T05:51:53.647Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-e4d72e12f812a802=277973.04 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-e4d72e12f812a802 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=277973.04 ms; declared-cap=1800000 ms | fail | 11 | criterion; 5/11; ratio=0.454545; public=3/3; hidden=2/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-unknown-honesty |

## Series 24

- Series ID: <code>sha256:45b877afa1138361394250f2dbe0a86b0d20333860b0a64639771e4477e56f75</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:40:39.003Z</code> to <code>2026-08-27T03:40:39.003Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "M-coupled-lifecycle-operations-bash",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 24: F11-M-BASH-001 revision 1

- Stratum ID: <code>sha256:fed8b272c68b90eb86f0ddc09aa7fb3ad58698072ee22a976adffd4fcb012061</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:40:39.003Z</code> to <code>2026-08-27T03:40:39.003Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:380c36ba746ff4efaa2256f421f797f1aed7afeb9bd0aff7919d21662bf94ca4",
      "case_id": "F11-M-BASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "c60da3b5ffa23c7c1fe7361646b7ce719c2f31a3",
        "bundle_digest": "sha256:34a6d9fed3637bf283a1b9bb96c7427d1304d7ea3e39907745dac0e4e2ff9513",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-007-c3f8b69c171a79e5=200243.599 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-007-c3f8b69c171a79e5 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=200243.599 ms; declared-cap=1800000 ms | fail | 7 | criterion; 6/7; ratio=0.857143; public=2/2; hidden=4/5; all-checks-required=true | ops-ready-after-verify |

## Series 25

- Series ID: <code>sha256:45be82ef143532655d6ab9fdb03ff4db52332f7ee5c30b30113b294863fabb17</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:54:12.056Z</code> to <code>2026-08-27T02:54:12.056Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "L-cross-boundary-lifecycle-review",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 25: F02-L-PYBASHJS-001 revision 1

- Stratum ID: <code>sha256:1bd396160019f4e8fdb1165ee37fd5deedcee80ea8a1c5dc17316cf5d40cc7af</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:54:12.056Z</code> to <code>2026-08-27T02:54:12.056Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:cfae31a9caae417953e194a3ed0ec282ba6d3846ce6b829e79b42f4ac0f2325e",
      "case_id": "F02-L-PYBASHJS-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "7579974e296a58227f43210421e4b954a66e9182",
        "bundle_digest": "sha256:549aa6ab20763ec5ec160b2c130e6e49141bdb8cf48baddd9b4bd1c0038ed72b",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-027-c7b66ee0a4c79b37=134528.766 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-027-c7b66ee0a4c79b37 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=134528.766 ms; declared-cap=1800000 ms | fail | 11 | criterion; 6/11; ratio=0.545455; public=4/4; hidden=2/7; all-checks-required=true | review-redaction-order, review-stale-restart, review-cleanup-owner, review-lifecycle-model, review-evidence-integrity |

## Series 26

- Series ID: <code>sha256:4e27512934491c47347eeadd36de996176d674ba928973a8ebaeab109a588924</code>
- Study ID: <code>duration-atlas-wave5-identity-recovery</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T06:07:15.461Z</code> to <code>2026-08-27T06:07:15.461Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "L-cross-process-lifecycle-test-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 26: F06-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:181778215be4cf755832c783d5dae3f1be5e7b130808bbdc79de495af334abfd</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T06:07:15.461Z</code> to <code>2026-08-27T06:07:15.461Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:5dc9de1e14cd90c4ef03a3e19f561c4ec0134a8db07099e7a7e34efaddc2d807",
      "case_id": "F06-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a41685e60ec9e83713a0682e1209e09c7085e200",
        "bundle_digest": "sha256:4663cb59494a727556365cfe615251121817906daa9b0f98de76e7ccc062caac",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-758f6d400a39baad=678286.534 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-758f6d400a39baad | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=678286.534 ms; declared-cap=1800000 ms | fail | 11 | criterion; 3/11; ratio=0.272727; public=2/4; hidden=1/7; all-checks-required=true | workspace-2, workspace-3, test-kills-lost-wakeup, test-kills-stale-lease, test-kills-duplicate-owner, test-kills-broad-cleanup, test-repeatability, test-bounded-cleanup |

## Series 27

- Series ID: <code>sha256:4f12faf2e8bc428718fe9256d68f3b4290940b4b59d63cd51d18488b9f1e1a78</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:48:22.783Z</code> to <code>2026-08-27T02:48:22.783Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "M-coupled-calibrated-architecture",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 27: F08-M-MDJSON-001 revision 1

- Stratum ID: <code>sha256:74ba4911c324880fa8d18ca71f4c09e7752988e47bff698f5d549ed067100b66</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:48:22.783Z</code> to <code>2026-08-27T02:48:22.783Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:b387c811c5371e97f84eba0e6793e2ad86f743c6eb3e3f45109f1b66092d2c62",
      "case_id": "F08-M-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1508653b1462b14f5ac7d145ee36cb821a0f5373",
        "bundle_digest": "sha256:bddda853cc6aebed863694e3dcfd79a3b562ce026f31c2e66d1ce3fd9822fc0d",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-023-40f2340957975477=116919.829 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-023-40f2340957975477 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=116919.829 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | design-invariant-coverage, design-option-counterexamples, design-migration-observability, design-unknown-honesty |

## Series 28

- Series ID: <code>sha256:5407e21a98f6fc33b0cce70b160cb7edc0df2e733634d1f770ee58d0fb4c8b1d</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:22:01.931Z</code> to <code>2026-08-27T02:22:01.931Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "S-local-static-operations-bash",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 28: F11-S-BASH-001 revision 1

- Stratum ID: <code>sha256:0b52fc5b9003cc231467ee722edbbefe22c58c0eabdba96bfc653e1603075d8d</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:22:01.931Z</code> to <code>2026-08-27T02:22:01.931Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:bd8f792101fe4771222d69f3ab8a95929831a4ccc127964bdd616a8e8f345247",
      "case_id": "F11-S-BASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6b92ac22bcb9b2a8e3bb1d22116936016d453538",
        "bundle_digest": "sha256:7cd352f1ec896227c9b270f8019b07a81b10cec3f00a8aa90cc485dbd9ddb766",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-013-960048619f36327b=24325.882 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-013-960048619f36327b | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=24325.887 ms; declared-cap=1800000 ms | pass | 5 | criterion; 5/5; ratio=1.0; public=2/2; hidden=3/3; all-checks-required=true | none |

## Series 29

- Series ID: <code>sha256:5a40bba3e68e9004f60e06aed646d795bc4dc16109ff828c71de9539fdbc4f91</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:36:19.251Z</code> to <code>2026-08-27T05:36:19.251Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "M-coupled-lifecycle-operations-bash",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 29: F11-M-BASH-001 revision 1

- Stratum ID: <code>sha256:fa174cb40735a7e3bcbeeb472bc976c5c41224aeabb5d2bb998faacb7b372733</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:36:19.251Z</code> to <code>2026-08-27T05:36:19.251Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:380c36ba746ff4efaa2256f421f797f1aed7afeb9bd0aff7919d21662bf94ca4",
      "case_id": "F11-M-BASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "c60da3b5ffa23c7c1fe7361646b7ce719c2f31a3",
        "bundle_digest": "sha256:34a6d9fed3637bf283a1b9bb96c7427d1304d7ea3e39907745dac0e4e2ff9513",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-010-b7f2aefde4b0d672=150938.446 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-010-b7f2aefde4b0d672 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=150938.446 ms; declared-cap=1800000 ms | fail | 7 | criterion; 6/7; ratio=0.857143; public=2/2; hidden=4/5; all-checks-required=true | ops-ready-after-verify |

## Series 30

- Series ID: <code>sha256:5e233468a3d0ab7e7d66232fd18d4c78bf5a59823cb1b0ad9d7d90954f0e2eab</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:11:40.336Z</code> to <code>2026-08-27T03:11:40.336Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "M-coupled-lifecycle-operations-bash",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 30: F11-M-BASH-001 revision 1

- Stratum ID: <code>sha256:b93a3f82dfda88660fc3f8c2f1aa2e9af893ca5a6bbab3c5f376ceaa049e3176</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:11:40.336Z</code> to <code>2026-08-27T03:11:40.336Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:380c36ba746ff4efaa2256f421f797f1aed7afeb9bd0aff7919d21662bf94ca4",
      "case_id": "F11-M-BASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "c60da3b5ffa23c7c1fe7361646b7ce719c2f31a3",
        "bundle_digest": "sha256:34a6d9fed3637bf283a1b9bb96c7427d1304d7ea3e39907745dac0e4e2ff9513",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-035-428b05a832bea50f=136402.672 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-035-428b05a832bea50f | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=136402.672 ms; declared-cap=1800000 ms | fail | 7 | criterion; 6/7; ratio=0.857143; public=2/2; hidden=4/5; all-checks-required=true | ops-ready-after-verify |

## Series 31

- Series ID: <code>sha256:62a7228f012a732e62606fca9f4d395a2dbe6a5aa6a6800775a1f44334b1e587</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:19:32.272Z</code> to <code>2026-08-27T04:19:32.272Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "max",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 31: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:7ba1c7e0fcc949e18c4e454d70b3f0f9f477b00f2db8fdfd652704282d2936b6</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:19:32.272Z</code> to <code>2026-08-27T04:19:32.272Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-f2d7073edac558ff=722083.503 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-f2d7073edac558ff | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=722083.503 ms; declared-cap=3600000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 32

- Series ID: <code>sha256:641bea6ee085bf543d53f4041ad4b6e653542704505ce36112fee22386b7445a</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:31:31.232Z</code> to <code>2026-08-27T03:31:31.232Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "L-cross-process-lifecycle-test-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 32: F06-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:50eb807c61f1db4016ddec3bdcb0009d27e285bf9b95dadcadd588519c35b13b</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:31:31.232Z</code> to <code>2026-08-27T03:31:31.232Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:5dc9de1e14cd90c4ef03a3e19f561c4ec0134a8db07099e7a7e34efaddc2d807",
      "case_id": "F06-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a41685e60ec9e83713a0682e1209e09c7085e200",
        "bundle_digest": "sha256:4663cb59494a727556365cfe615251121817906daa9b0f98de76e7ccc062caac",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-005-8d34b88f024eda13=423969.817 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-005-8d34b88f024eda13 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=423969.821 ms; declared-cap=1800000 ms | pass | 11 | criterion; 11/11; ratio=1.0; public=4/4; hidden=7/7; all-checks-required=true | none |

## Series 33

- Series ID: <code>sha256:657c1ded80f343e4e7fa87ba66d09101e72145f3d9dcee2b56897ab26110a7b6</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:14:09.245Z</code> to <code>2026-08-27T05:14:09.245Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 33: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:bc4a418b2fb3f6ecc57061cb7e6c6de21c63049b0415fc2acf1b34f12c043374</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:14:09.245Z</code> to <code>2026-08-27T05:14:09.245Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-011-16e30cd1a1c95aa0=35550.239 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-011-16e30cd1a1c95aa0 | infrastructure=success; artifact=missing; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=35550.239 ms; declared-cap=1800000 ms | fail | 9 | criterion; 0/9; ratio=0.0; public=0/3; hidden=0/6; all-checks-required=true | workspace-1, workspace-2, workspace-3, diagnosis-deterministic-barrier, diagnosis-ordering-cause, diagnosis-restart-state, diagnosis-regression-reliable, diagnosis-cleanup-bounded, diagnosis-semantics-honest |

## Series 34

- Series ID: <code>sha256:669cb17be0388ff375d327633050a2cec03b323091070a849f61226b7cb39dcf</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:47:17.641Z</code> to <code>2026-08-27T02:47:17.641Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "S-local-seeded-review-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 34: F02-S-PY-001 revision 1

- Stratum ID: <code>sha256:548ff6213ef501cbd532859f6502f58252de40caaaba5fd2744ef8a084d1bfc9</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:47:17.641Z</code> to <code>2026-08-27T02:47:17.641Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:0ebfeeeed554ebb24e5292b30fd1183f4a2938de83ad9697288aa94eae5b382d",
      "case_id": "F02-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b9cfb7af1a6a0448033ec2f083a7888cce417591",
        "bundle_digest": "sha256:7a9b20ff9ca86587f9dd6efb832d6676b2e2fc486834b48b789e716de7403049",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-022-f8fc43a390c18674=61555.492 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-022-f8fc43a390c18674 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=61555.492 ms; declared-cap=1800000 ms | fail | 7 | criterion; 6/7; ratio=0.857143; public=2/2; hidden=4/5; all-checks-required=true | review-evidence-line |

## Series 35

- Series ID: <code>sha256:676d9695a738d3fc904a82c296d0df5640af451b2facaa1e1b6d3fe8ac931525</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:00:24.662Z</code> to <code>2026-08-27T03:00:24.662Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "L-cross-boundary-backend-schema-migration",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 35: F05-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:176945cce636bf1c5153afa7cbc4d557fccc5fb1f721e9fef48ba4f13149c935</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:00:24.662Z</code> to <code>2026-08-27T03:00:24.662Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:4e1314a06bb7893b13a14c39e85c1f6c0c98512a23eff242cc36a0a3d1636db6",
      "case_id": "F05-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "d801efb92e1bba49dd969c5f3c207747c13b3edd",
        "bundle_digest": "sha256:3feed8109dcffb30c2ecbf97cf891e07b9be07bafa61ac0bf7c67ad611733576",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-030-8f31d4aa692ecffe=206795.196 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-030-8f31d4aa692ecffe | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=206795.196 ms; declared-cap=1800000 ms | fail | 10 | criterion; 4/10; ratio=0.4; public=4/4; hidden=0/6; all-checks-required=true | migration-v1-compat, migration-backend-boundary, migration-atomic-order, migration-resume, migration-rollback, migration-operations-doc |

## Series 36

- Series ID: <code>sha256:67fc7abfea7b19eb9b56d2026f643917addad31b1dd98fb4f2cbda0972f95540</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:06:44.696Z</code> to <code>2026-08-27T03:06:44.696Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "L-multistage-resource-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 36: F10-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:ad14a3923360eb6275dba54a1b362c01d4a769b88daab3e9ceeb733cc381aaa0</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:06:44.696Z</code> to <code>2026-08-27T03:06:44.696Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c2b4b9bef2505669cb3a278fc24662d989839645cf07048ca0bf674162137fed",
      "case_id": "F10-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "604588309058ae69f5cde17591b88222295040c8",
        "bundle_digest": "sha256:a6a0f0af6867f9a412fc7176288cfdfa5764fec0f956b9e3bebf83683562ef34",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-033-d81bf119d0024dba=237033.765 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-033-d81bf119d0024dba | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=237033.765 ms; declared-cap=1800000 ms | fail | 9 | criterion; 2/9; ratio=0.222222; public=2/2; hidden=0/7; all-checks-required=true | perf-stage-correlation, perf-time-accounting, perf-width-curve, perf-probe-lock-cause, perf-provider-distinction, perf-censoring-resource, perf-claim-bounded |

## Series 37

- Series ID: <code>sha256:68b8df98c0386f1a2e3422fd96eb379ccca6d75cb28ce6d7f734da557bd5c7d7</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:37:52.969Z</code> to <code>2026-08-27T02:37:52.969Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "M-coupled-seeded-isolation-review",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 37: F09-M-PYBASH-001 revision 1

- Stratum ID: <code>sha256:91373bb0d8ef934492225170bd05ad4011dbb61fdb8b2241a1d5b2587ce37784</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:37:52.969Z</code> to <code>2026-08-27T02:37:52.969Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:5c5fef60596257729f21756fb720f8f13b9b31bae9d612ac1af143d6a48a507a",
      "case_id": "F09-M-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "31a8ffe438da0dcf8956d58fbf7ba668f726c315",
        "bundle_digest": "sha256:f76d72495883b1e0ca746be83bd340437b56973e11553a43fa586af1561ae708",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-020-15fb2a0ebf188352=122555.296 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-020-15fb2a0ebf188352 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=122555.296 ms; declared-cap=1800000 ms | fail | 10 | criterion; 5/10; ratio=0.5; public=4/4; hidden=1/6; all-checks-required=true | security-symlink-exploit, security-env-root-exploit, security-composition, security-negative-tests, security-no-false-positive |

## Series 38

- Series ID: <code>sha256:6db2de59aaaf9a8f572c8608be02d62b04d33ff66d667fb968ef3cbdef2ed228</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:10:44.564Z</code> to <code>2026-08-27T03:10:44.564Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "S-local-deterministic-diagnosis-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 38: F03-S-PY-001 revision 1

- Stratum ID: <code>sha256:289231784105ae1d313eaf549f93406f0267fd5773750d3fb8a31652c2a114f2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:10:44.564Z</code> to <code>2026-08-27T03:10:44.564Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d6960fbd299e59fd843012592313d3356cbcd728673d965430eb8c2aa0acc01a",
      "case_id": "F03-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "d7b81c2e46a200a0b68ca38e81f917bc96ba330e",
        "bundle_digest": "sha256:abb7d4c4ddce1be216df1d93c7a360a3cf23488c646c149710c68242c2caac0d",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-034-06f90eaba1a453af=52958.618 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-034-06f90eaba1a453af | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=52958.618 ms; declared-cap=1800000 ms | fail | 6 | criterion; 4/6; ratio=0.666667; public=2/2; hidden=2/4; all-checks-required=true | diagnosis-root-cause, diagnosis-regression |

## Series 39

- Series ID: <code>sha256:6e964cf5aa1de44ac0ffc6c9fee97eaaf9640dba5f1d3e07041c87f631e4fce7</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:17:40.482Z</code> to <code>2026-08-27T02:17:40.482Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "M-coupled-calibrated-adjudication",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 39: F12-M-MDJSON-001 revision 1

- Stratum ID: <code>sha256:9df2aa118da4ec34d2313b4a67bea26cb95d555382eab507e5413517d9cead01</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:17:40.482Z</code> to <code>2026-08-27T02:17:40.482Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:b2222b9213e00dd05d237423dc41a730bcaec60619f4ce8e5106ba2b8860fc23",
      "case_id": "F12-M-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "46955f86e279d0dc8adb55b54ab454e2f017dfba",
        "bundle_digest": "sha256:c57cb2c705c831c64609c686a8a6f41bbfdabbd1c0d40a27bcf13a5f2b5e9e96",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-011-212fc62819d02ecc=130227.713 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-011-212fc62819d02ecc | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=130227.713 ms; declared-cap=1800000 ms | fail | 9 | criterion; 4/9; ratio=0.444444; public=2/2; hidden=2/7; all-checks-required=true | synthesis-provenance, synthesis-race-accepted, synthesis-fix-refuted, synthesis-platform-unknown, synthesis-severity-narrowed |

## Series 40

- Series ID: <code>sha256:707973dcb46df0c2c43c7cf32936789093172605bcc33c1228cbd29649cbec70</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:24:25.229Z</code> to <code>2026-08-27T05:24:25.229Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 40: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:488a4095a6936fedcab1040ed4543452a68d09181f3270450c6dd553ee301954</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:24:25.229Z</code> to <code>2026-08-27T05:24:25.229Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-005-a16270dc591bde8a=65990.167 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-005-a16270dc591bde8a | infrastructure=success; artifact=missing; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=65990.167 ms; declared-cap=1800000 ms | fail | 9 | criterion; 0/9; ratio=0.0; public=0/3; hidden=0/6; all-checks-required=true | workspace-1, workspace-2, workspace-3, diagnosis-deterministic-barrier, diagnosis-ordering-cause, diagnosis-restart-state, diagnosis-regression-reliable, diagnosis-cleanup-bounded, diagnosis-semantics-honest |

## Series 41

- Series ID: <code>sha256:794504ad939b331229441ab72dec93ea2c76d3dd5aa069e27f485b21a69c2081</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:44:01.960Z</code> to <code>2026-08-27T03:44:01.960Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 41: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:957335541eba53c62ee76d3601a4dace7d9233ad590ccb65dd75cf453922c546</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:44:01.960Z</code> to <code>2026-08-27T03:44:01.960Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-008-41f6d565527a0a08=103239.161 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-008-41f6d565527a0a08 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=103239.161 ms; declared-cap=1800000 ms | fail | 9 | criterion; 5/9; ratio=0.555556; public=3/3; hidden=2/6; all-checks-required=true | diagnosis-ordering-cause, diagnosis-restart-state, diagnosis-cleanup-bounded, diagnosis-semantics-honest |

## Series 42

- Series ID: <code>sha256:7bdc45db083df2bc6df03e5da80f13ab27877c4b216327d7f23ef2eff1499b79</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:50:43.912Z</code> to <code>2026-08-26T18:50:43.912Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 42: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:b00919f7be758a91fcda8f93673ec0dd8e2c655e23f11bded413c723598db0a4</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:50:43.912Z</code> to <code>2026-08-26T18:50:43.912Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | codex-f04-l-sol-medium-20260827-r01=96938.046 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-l-sol-medium-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=96938.053 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 43

- Series ID: <code>sha256:7c7996c50183de9e19931d7fadcb8a59a0486f375bc9fb439776b5f5464e9823</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:11:37.108Z</code> to <code>2026-08-27T05:11:37.108Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "S-local-benchmark-diagnosis-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 43: F10-S-PY-001 revision 1

- Stratum ID: <code>sha256:8fe4116d254b1de4a20b37e0059ecbf234e48cce1840be6d4d6bf60d4a78332e</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:11:37.108Z</code> to <code>2026-08-27T05:11:37.108Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c0efce6cb9cc78eda89064eb70cc2c2634495c331e19263b4fa38d57b25d3242",
      "case_id": "F10-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6d14dfbff162662b293ebe74acbbbfcacd4bcb64",
        "bundle_digest": "sha256:f16e55ddfe14f59a8d93568e3dab48cbf2415d3e35e93e12ed5c6e52ae322ceb",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-009-2bb14915b664e5af=46691.145 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-009-2bb14915b664e5af | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=46691.145 ms; declared-cap=1800000 ms | fail | 7 | criterion; 1/7; ratio=0.142857; public=1/2; hidden=0/5; all-checks-required=true | workspace-2, perf-repro-command, perf-scaling-evidence, perf-root-cause, perf-distractor-rejected, perf-claim-bounded |

## Series 44

- Series ID: <code>sha256:7e7e4a684929ee5dd70bb3c54211a29791fbc76790045d393610b4b79e795e5f</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:43:22.390Z</code> to <code>2026-08-26T18:43:22.390Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 44: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:98742ec5cfd3854f4806664708423eb59b788445630f751b4b90fc2adbf70dd5</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:43:22.390Z</code> to <code>2026-08-26T18:43:22.390Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | grok-f04-l-46-high-20260827-r01=100239.958 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-l-46-high-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=100239.97 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 45

- Series ID: <code>sha256:80287988b72a1970babcfe3cd0abd260edb71e0bd4e1547b98a567017b75c938</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:59:15.797Z</code> to <code>2026-08-27T01:59:15.797Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "S-local-benchmark-diagnosis-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 45: F10-S-PY-001 revision 1

- Stratum ID: <code>sha256:e74df3b0ef1ac97b552f0077e854c8d63402e3569509489cf6cc2e611a07074f</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:59:15.797Z</code> to <code>2026-08-27T01:59:15.797Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c0efce6cb9cc78eda89064eb70cc2c2634495c331e19263b4fa38d57b25d3242",
      "case_id": "F10-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6d14dfbff162662b293ebe74acbbbfcacd4bcb64",
        "bundle_digest": "sha256:f16e55ddfe14f59a8d93568e3dab48cbf2415d3e35e93e12ed5c6e52ae322ceb",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-771bcffe5e8c9972=103620.903 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-771bcffe5e8c9972 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=103620.903 ms; declared-cap=1800000 ms | fail | 7 | criterion; 2/7; ratio=0.285714; public=2/2; hidden=0/5; all-checks-required=true | perf-repro-command, perf-scaling-evidence, perf-root-cause, perf-distractor-rejected, perf-claim-bounded |

## Series 46

- Series ID: <code>sha256:806841a7e6b67821a10a7c675348cd05bb741b239bfba2f4dc8d8bd2229bda5c</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:14:46.118Z</code> to <code>2026-08-27T05:14:46.118Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 46: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:af3cf86eae25c7b61b2281176601ca87698f6071de049cb16544ecfd630d0f00</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:14:46.118Z</code> to <code>2026-08-27T05:14:46.118Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-012-06ed7485f4107e51=64269.798 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-012-06ed7485f4107e51 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=64269.798 ms; declared-cap=1800000 ms | fail | 5 | criterion; 4/5; ratio=0.8; public=1/1; hidden=3/4; all-checks-required=true | hidden-empty-result |

## Series 47

- Series ID: <code>sha256:861e92744ddb4e58517018ff20c909be716c95ace4f35cf89c30a7440642bec3</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:33:27.161Z</code> to <code>2026-08-27T01:33:27.161Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "S-local-constraint-design",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 47: F08-S-MDJSON-001 revision 1

- Stratum ID: <code>sha256:027c26b1dc483b31f94fb0b2e6e28632a0cfb16ffb88b5eba02d9b5a8fe51d70</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:33:27.161Z</code> to <code>2026-08-27T01:33:27.161Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:f39b06eabb05f2e1da3125ac55dc8267ed387d5fe7002a97a70256d67ffee2cc",
      "case_id": "F08-S-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "d1b8e034462f1757b91d739c67c7b3312252d382",
        "bundle_digest": "sha256:359c95f99ca132cd401bb6648e6c6229d0dd2be43e2bf529dab33a42fd2539cc",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-8a98736041817333=110968.743 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-8a98736041817333 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=110968.743 ms; declared-cap=1800000 ms | fail | 7 | criterion; 2/7; ratio=0.285714; public=2/2; hidden=0/5; all-checks-required=true | design-constraint-coverage, design-counterexamples, design-selected-contract, design-evidence-entailment, design-doc-json-sync |

## Series 48

- Series ID: <code>sha256:8b5d7fb16c941688b70104f1ff1f9264396aeffbadf56a1855a3a7d805ae0b51</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:25:52.023Z</code> to <code>2026-08-26T18:25:52.023Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01"
      }
    ]

### Case observations

### Case 48: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:9c7e33335d2cb1bab5fce967f64e154b0a498b5c5b61023c19d06c55b62521bc</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:25:52.023Z</code> to <code>2026-08-26T18:25:52.023Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | grok-f04-s-46-medium-20260827-r02=52670.697 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-s-46-medium-20260827-r02 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=52670.704 ms; declared-cap=900000 ms | pass | 5 | criterion; 5/5; ratio=1.0; public=1/1; hidden=4/4; all-checks-required=true | none |

## Series 49

- Series ID: <code>sha256:8c57e59c5fd5190cb6a51f8234c6a854d7f756987b21f009ca806ed9fde163b7</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:36:44.136Z</code> to <code>2026-08-27T02:36:44.136Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "S-local-entailment-synthesis",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 49: F12-S-MDJSON-001 revision 1

- Stratum ID: <code>sha256:3c323c491b0c73d191b357f5ee97b9ce283868609adb2cc4d6a7c10855545102</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:36:44.136Z</code> to <code>2026-08-27T02:36:44.136Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:7f3e2e268961220560f91821b6a3de34ebc26591f124dbd297273aeffd0d45b2",
      "case_id": "F12-S-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6dcd38c497a45eb8fd58afe4bd3f537ac50fa4fb",
        "bundle_digest": "sha256:c8fcd97e1c6e5be6fe4365231cf5d89822b0d52bb82e1c2f1e1964cbb55fbce1",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-019-08b62149616e646f=61960.683 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-019-08b62149616e646f | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=61960.683 ms; declared-cap=1800000 ms | fail | 6 | criterion; 3/6; ratio=0.5; public=1/1; hidden=2/5; all-checks-required=true | synthesis-claim-coverage, synthesis-conflict-adjudication, synthesis-unsupported |

## Series 50

- Series ID: <code>sha256:8dd74aa192fadf7065ad3a12de258406b9f9146574599686970f8748ccf13fc6</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:43:44.595Z</code> to <code>2026-08-27T05:43:44.595Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "performance-resource",
        "profile_id": "S-local-benchmark-diagnosis-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 50: F10-S-PY-001 revision 1

- Stratum ID: <code>sha256:296ed2a22b56ec9b3a5167f8d69c197b814b3d233132072891f740d9662dd412</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:43:44.595Z</code> to <code>2026-08-27T05:43:44.595Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:c0efce6cb9cc78eda89064eb70cc2c2634495c331e19263b4fa38d57b25d3242",
      "case_id": "F10-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6d14dfbff162662b293ebe74acbbbfcacd4bcb64",
        "bundle_digest": "sha256:f16e55ddfe14f59a8d93568e3dab48cbf2415d3e35e93e12ed5c6e52ae322ceb",
        "instruction_set_digest": "sha256:515e1f39556360f1ddfbd903ca45e438a5053cebd86306dc6ac82fae3d1d8fb2"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-012-598bdb7aa67e5c56=56971.561 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-012-598bdb7aa67e5c56 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=56971.561 ms; declared-cap=1800000 ms | fail | 7 | criterion; 1/7; ratio=0.142857; public=1/2; hidden=0/5; all-checks-required=true | workspace-2, perf-repro-command, perf-scaling-evidence, perf-root-cause, perf-distractor-rejected, perf-claim-bounded |

## Series 51

- Series ID: <code>sha256:9648c8c96a8e6eca9a0ae550194b24304b9968d442fc1cc50f944bf62a8d214a</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:54:49.373Z</code> to <code>2026-08-27T01:54:49.373Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "L-cross-boundary-calibrated-execution-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 51: F08-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:9f5bf8f01d249f1a5029b6cde4347f4410c9276fd7d785d3ded8c8289016de64</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:54:49.373Z</code> to <code>2026-08-27T01:54:49.373Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:82ba9e0a704fcb780f381744bd03d9739324d0f4e2d42b5dba1ca16631f878e8",
      "case_id": "F08-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e67c9fade26c86fc47a2655d96ba4c83f7ed6cfa",
        "bundle_digest": "sha256:c62298b5a0cfcf71789d21bd9e6e5bb5537ff7f1ccee3bd70001ef593eeb0fc6",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-456211b1993ac2d2=249148.556 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-456211b1993ac2d2 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=249148.556 ms; declared-cap=1800000 ms | fail | 11 | criterion; 9/11; ratio=0.818182; public=3/3; hidden=6/8; all-checks-required=true | design-security-boundaries, design-alternative-counterexamples |

## Series 52

- Series ID: <code>sha256:973beb264df75368bc4aab9c2b50290e037f39d61b02f7a71141b833eec1bba5</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:31:43.912Z</code> to <code>2026-08-27T02:31:43.912Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "M-coupled-deterministic-diagnosis-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 52: F03-M-PY-001 revision 1

- Stratum ID: <code>sha256:f53142795552604e82d9d520fc7fb7cb82facc8508aeb78c3ee8773826c90da1</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:31:43.912Z</code> to <code>2026-08-27T02:31:43.912Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:e4cb286f996bb727f022a2984b67f654b36923d89ca64b51b0387f747e03d56f",
      "case_id": "F03-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "20a127346b7904020de01ac8cb64d42d788d7ce9",
        "bundle_digest": "sha256:13cb0fb7fb014e14950fe9f527abdc88840ac9c029269ea5ac3e374d616e832d",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-017-999a8eedbe1d1e9f=99825.095 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-017-999a8eedbe1d1e9f | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=99825.095 ms; declared-cap=1800000 ms | fail | 7 | criterion; 3/7; ratio=0.428571; public=2/2; hidden=1/5; all-checks-required=true | diagnosis-reload-contrast, diagnosis-causal-chain, diagnosis-regression-layers, diagnosis-distractor-rejected |

## Series 53

- Series ID: <code>sha256:9a470fd487f45e8e26869b5107acee0a9d700dee687668be118cbd4f4f0814dc</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:52:19.207Z</code> to <code>2026-08-27T02:52:19.207Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "S-local-executable-doc-markdown",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 53: F07-S-MD-001 revision 1

- Stratum ID: <code>sha256:d8241ffc818a93c9cdc02dd433e9477631afbae0f6ddd94557204c2fae22184a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:52:19.207Z</code> to <code>2026-08-27T02:52:19.207Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:7bfe047d68fdc6cb4ec29f3102757ae92bfcd3d29a524290249e0fb1781d52e0",
      "case_id": "F07-S-MD-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1abdeb21a7a282f0c6bbd3190c813b9bb2fa1f4f",
        "bundle_digest": "sha256:e1feeda661711d99adfc9c8e7a0cdd36c046e56377ca84edfe1e36b5b31a00bb",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-025-b2840e4aeb68baa2=37859.725 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-025-b2840e4aeb68baa2 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=37859.725 ms; declared-cap=1800000 ms | fail | 6 | criterion; 5/6; ratio=0.833333; public=2/2; hidden=3/4; all-checks-required=true | doc-constraint-accurate |

## Series 54

- Series ID: <code>sha256:9c0f9430bb360056137f34a2c757c5b6b2f67f663929864d85e26ab2d7237228</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:50:23.410Z</code> to <code>2026-08-26T18:50:23.410Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "max",
            "status": "rejected"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 54: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:b399074d362e7485383847c821ba2fa3b50e5c13163f0fba6949640433132f2a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:50:23.410Z</code> to <code>2026-08-26T18:50:23.410Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | grok-f04-l-46-max-20260827-r03=2358.287 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-l-46-max-20260827-r03 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=generation-setting-rejected | complete-terminal; observed-terminal=2358.287 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |

## Series 55

- Series ID: <code>sha256:9e3cc23e90ce2f9f4172dc2b6f9ab1ad7ddd4b4dfb3a860cbee22505ed2d2d5c</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:48:52.547Z</code> to <code>2026-08-27T03:48:52.547Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 55: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:253d5b2d5829895eb958316645ee719b1b195a5368c64b380f46e7ede0922126</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:48:52.547Z</code> to <code>2026-08-27T03:48:52.547Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-011-52a82583a7ab2da4=360122.581 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-011-52a82583a7ab2da4 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=360122.581 ms; declared-cap=1800000 ms | fail | 11 | criterion; 3/11; ratio=0.272727; public=3/3; hidden=0/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-bind-injection, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-control-counterexamples, threat-unknown-honesty |

## Series 56

- Series ID: <code>sha256:9f46ffaed764413de667479e983ad48b1edffd8731f21e8cacb0c295d1dd84c1</code>
- Study ID: <code>duration-atlas-wave1</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:37:22.576Z</code> to <code>2026-08-26T11:37:22.576Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "low",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d"
      }
    ]

### Case observations

### Case 56: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:377ecfc134e0ff7fba8b5129f2d506c27cfd4731168265d978298cc9162d89ea</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:37:22.576Z</code> to <code>2026-08-26T11:37:22.576Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | codex-f04-s-sol-low-20260826-r04=52766.608 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-s-sol-low-20260826-r04 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=52766.608 ms; declared-cap=300000 ms | fail | 2 | aggregate-check; 1/2; ratio=0.5; public=0/0; hidden=0/0; all-checks-required=true | f04-s-python-hidden-v1 |

## Series 57

- Series ID: <code>sha256:9f4973a9cbeac926bc1022e89d5943a4c97c6d78199d3fb7977131b1c92f6580</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:16:27.059Z</code> to <code>2026-08-27T05:16:27.059Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "M-coupled-interface-migration-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 57: F05-M-PY-001 revision 1

- Stratum ID: <code>sha256:a983c5092148473f7c58bccf0c65d76ea8899e31bfb835bfe92ddaf7507b247e</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:16:27.059Z</code> to <code>2026-08-27T05:16:27.059Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:4e93974668ce5719b2b52f07d19b5be28cd26be01add5b7ab05763e7c313e9d7",
      "case_id": "F05-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0dac3f22518b2044bc1e5be41c147adf01fb5b74",
        "bundle_digest": "sha256:fa4d0981251cacf99ac21298ff3b4bc8d36bd98e4e5b54b8b6c4be968cbdec98",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-9c16b4749bbfca63=71657.485 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-9c16b4749bbfca63 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=71657.485 ms; declared-cap=1800000 ms | fail | 7 | criterion; 2/7; ratio=0.285714; public=2/2; hidden=0/5; all-checks-required=true | migration-all-callers, migration-policy-lifecycle, migration-compat-bytes, migration-warning-once, migration-api-surface |

## Series 58

- Series ID: <code>sha256:a2a81f1650e3931c74ced00b76fafcd1f321cd3502a355bd2ca20808b487d7c5</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:57:27.756Z</code> to <code>2026-08-27T05:57:27.756Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "L-cross-boundary-calibrated-execution-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "xhigh",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "xhigh",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 58: F08-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:56c76ed458e2b6eff4e696dd2db0b44edb4da9ab0e023310be9bf527d86846fa</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:57:27.756Z</code> to <code>2026-08-27T05:57:27.756Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:82ba9e0a704fcb780f381744bd03d9739324d0f4e2d42b5dba1ca16631f878e8",
      "case_id": "F08-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e67c9fade26c86fc47a2655d96ba4c83f7ed6cfa",
        "bundle_digest": "sha256:c62298b5a0cfcf71789d21bd9e6e5bb5537ff7f1ccee3bd70001ef593eeb0fc6",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-a96094fecd70da84=270403.618 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-a96094fecd70da84 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=270403.618 ms; declared-cap=1800000 ms | fail | 11 | criterion; 7/11; ratio=0.636364; public=3/3; hidden=4/8; all-checks-required=true | design-requirement-coverage, design-security-boundaries, design-alternative-counterexamples, design-unknown-honesty |

## Series 59

- Series ID: <code>sha256:a74bb43b8f0676d317e2dd5a7b050c1432847811b04e9f5dfb9c366618fa85cb</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:18:13.759Z</code> to <code>2026-08-27T05:18:13.759Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 59: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:480746b4094fa174dd7f93ea844e1f8b0f2ee93f5552ba13c1d7f8c6039acf31</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:18:13.759Z</code> to <code>2026-08-27T05:18:13.759Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-01b8985244ba715d=87272.838 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-01b8985244ba715d | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=87272.838 ms; declared-cap=1800000 ms | fail | 5 | criterion; 4/5; ratio=0.8; public=1/1; hidden=3/4; all-checks-required=true | hidden-empty-result |

## Series 60

- Series ID: <code>sha256:a8e586e26d25073f1a7aa889e664eb58bd448af544b6594bfe6b2f8db92c54e3</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:24:05.256Z</code> to <code>2026-08-27T02:24:05.256Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 60: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:89614d074dfdbe91a1369055711292025da4a724bbbc43c84e223c8f0894c901</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:24:05.256Z</code> to <code>2026-08-27T02:24:05.256Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-015-a022a158880d7e0a=347100.663 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-015-a022a158880d7e0a | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=347100.663 ms; declared-cap=1800000 ms | fail | 11 | criterion; 3/11; ratio=0.272727; public=3/3; hidden=0/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-bind-injection, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-control-counterexamples, threat-unknown-honesty |

## Series 61

- Series ID: <code>sha256:a95c02e13b4a2f5adb2847656dffd39f3c82d5318a4c16be4ae7fa200f3c8dd1</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:27:52.816Z</code> to <code>2026-08-27T03:27:52.816Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "S-local-gold-trace-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 61: F01-S-PY-001 revision 1

- Stratum ID: <code>sha256:1d2d79ee41d79639f795b12b1003f3eedca6872b92c1b10712342292249ed040</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:27:52.816Z</code> to <code>2026-08-27T03:27:52.816Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:6bb5179f7978f93e1d019d44d35e29a52b004bf7a9d801e8448cbd05bc449841",
      "case_id": "F01-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "31046588bb74aa5af53c80ea82ad2812808ba06a",
        "bundle_digest": "sha256:ca4a54b9e0db7e49da139793e549bcdd3473e486c241eca0df3db6b6a1bdc6c0",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-d15e57bcc079496a=107946.959 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-d15e57bcc079496a | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=107946.959 ms; declared-cap=1800000 ms | fail | 6 | criterion; 4/6; ratio=0.666667; public=2/2; hidden=2/4; all-checks-required=true | trace-required-nodes, trace-required-edges |

## Series 62

- Series ID: <code>sha256:aa23a70759b7189791fe804e2b39fcfa17314af697638ee5bb81241301f194c2</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:17:43.584Z</code> to <code>2026-08-27T05:17:43.584Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "L-cross-process-lifecycle-test-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 62: F06-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:24608857e9734bb8846f206dc32fb3c587e2116768709b7ae2defa24e4bbe280</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:17:43.584Z</code> to <code>2026-08-27T05:17:43.584Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:5dc9de1e14cd90c4ef03a3e19f561c4ec0134a8db07099e7a7e34efaddc2d807",
      "case_id": "F06-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a41685e60ec9e83713a0682e1209e09c7085e200",
        "bundle_digest": "sha256:4663cb59494a727556365cfe615251121817906daa9b0f98de76e7ccc062caac",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-a5c7151046553dac=28870.428 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-a5c7151046553dac | infrastructure=success; artifact=missing; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=28870.428 ms; declared-cap=1800000 ms | fail | 11 | criterion; 5/11; ratio=0.454545; public=4/4; hidden=1/7; all-checks-required=true | test-kills-lost-wakeup, test-kills-stale-lease, test-kills-duplicate-owner, test-kills-broad-cleanup, test-repeatability, test-bounded-cleanup |

## Series 63

- Series ID: <code>sha256:aa99efb276f464fd88ab2118f151152489c7a7f07f6172bb069c2be40456c71d</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:34:26.530Z</code> to <code>2026-08-26T18:34:26.530Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 63: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:09011e8555a2050d8f28870fdbf28848ad7cbeda7dc8d79d34bebb06f1a14f4c</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:34:26.530Z</code> to <code>2026-08-26T18:34:26.530Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | codex-f04-s-sol-medium-20260827-r02=70678.478 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-s-sol-medium-20260827-r02 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=70678.478 ms; declared-cap=900000 ms | fail | 5 | criterion; 4/5; ratio=0.8; public=1/1; hidden=3/4; all-checks-required=true | hidden-empty-result |

## Series 64

- Series ID: <code>sha256:ae5a1da7cbcdff2ccbcd3733b4dd1d778cc1ccaeff4d2e8b433cea22a802810f</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:50:24.441Z</code> to <code>2026-08-27T02:50:24.441Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 64: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:44a5d80bff7fb63a9b58de914f7a6c03288ad1fc9cb2014a5a98529085d0f01d</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:50:24.441Z</code> to <code>2026-08-27T02:50:24.441Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-024-87cd2afe0c349367=109957.872 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-024-87cd2afe0c349367 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=109957.872 ms; declared-cap=1800000 ms | fail | 9 | criterion; 7/9; ratio=0.777778; public=3/3; hidden=4/6; all-checks-required=true | diagnosis-ordering-cause, diagnosis-cleanup-bounded |

## Series 65

- Series ID: <code>sha256:af8e7eccc85fb516fe0e8ae0f562ed81ea6b5b1077d7e4cdd07aa52a3d25cae6</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:54:52.303Z</code> to <code>2026-08-26T18:54:52.303Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "xhigh",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 65: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:a7d5d105ce7fb2dfed19069dd5463815c995ce9c8899d057ef096eec7d9d1af9</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:54:52.303Z</code> to <code>2026-08-26T18:54:52.303Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | codex-f04-l-sol-xhigh-20260827-r01=136639.158 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-l-sol-xhigh-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=136639.17 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 66

- Series ID: <code>sha256:afaa58cf4233d4603bb49888f78c205ce425ce3ebb278f74abecd990c94c1130</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:57:17.229Z</code> to <code>2026-08-26T18:57:17.229Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "max",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 66: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:741f0c421c00a7af371373e8f427250b716c0aebbaa2934ce0aa0b5b2ae99423</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:57:17.229Z</code> to <code>2026-08-26T18:57:17.229Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | codex-f04-l-sol-max-20260827-r01=235214.483 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-l-sol-max-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=235214.495 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 67

- Series ID: <code>sha256:b0587413e9abdf4efe3ef2632ed8dd5a2066e52cc70cbb45b25ed7c2e1d0c68c</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:55:47.439Z</code> to <code>2026-08-27T04:55:47.439Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "L-cross-boundary-threat-model",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 67: F09-L-PYBASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:e4bbd08e566fb661f0a17f4f3a01679112e6094bcb37dcc9de63c4bae028065a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:55:47.439Z</code> to <code>2026-08-27T04:55:47.439Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d8649db2998c9bbb3dfebd54e88d5709133b4732d8b3414bc4ca1faa60d97d89",
      "case_id": "F09-L-PYBASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "09693542f13a55412f01a2a1b528ee55047041b0",
        "bundle_digest": "sha256:5f59d4b3dd55a568f730dc3e66ba86685824ebf1c21506938af391fccd9026e2",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-a43af54d4188cd09=219751.254 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-a43af54d4188cd09 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=219751.254 ms; declared-cap=1800000 ms | fail | 11 | criterion; 5/11; ratio=0.454545; public=3/3; hidden=2/8; all-checks-required=true | threat-assets-boundaries, threat-worktree-race, threat-credential-scope, threat-cleanup-ownership, threat-detection-recovery, threat-unknown-honesty |

## Series 68

- Series ID: <code>sha256:b5f807ea833780f33e6178e1ee7acf2704d25207b88a9fcab47272b45bceb6c6</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:53:17.582Z</code> to <code>2026-08-27T04:53:17.582Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "M-coupled-lifecycle-operations-bash",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 68: F11-M-BASH-001 revision 1

- Stratum ID: <code>sha256:150b999a7d5e1bd83f9e714d5e1c547147bcef5f0c2f3faf814eeb1d9d47720b</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:53:17.582Z</code> to <code>2026-08-27T04:53:17.582Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:380c36ba746ff4efaa2256f421f797f1aed7afeb9bd0aff7919d21662bf94ca4",
      "case_id": "F11-M-BASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "c60da3b5ffa23c7c1fe7361646b7ce719c2f31a3",
        "bundle_digest": "sha256:34a6d9fed3637bf283a1b9bb96c7427d1304d7ea3e39907745dac0e4e2ff9513",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-553053b48f6fd867=146230.102 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-553053b48f6fd867 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=146230.102 ms; declared-cap=1800000 ms | fail | 7 | criterion; 6/7; ratio=0.857143; public=2/2; hidden=4/5; all-checks-required=true | ops-ready-after-verify |

## Series 69

- Series ID: <code>sha256:ba5d862eff748432c84e288b9992f41403ee7a5ad57dc6345cbb09d72ffecae5</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:46:56.871Z</code> to <code>2026-08-27T03:46:56.871Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "M-coupled-interface-migration-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 69: F05-M-PY-001 revision 1

- Stratum ID: <code>sha256:40ecbf7fef16db7410c816fdb8df73c5a4b78c7f0728935efd4b9018930ae867</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:46:56.871Z</code> to <code>2026-08-27T03:46:56.871Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:4e93974668ce5719b2b52f07d19b5be28cd26be01add5b7ab05763e7c313e9d7",
      "case_id": "F05-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0dac3f22518b2044bc1e5be41c147adf01fb5b74",
        "bundle_digest": "sha256:fa4d0981251cacf99ac21298ff3b4bc8d36bd98e4e5b54b8b6c4be968cbdec98",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-010-5c5781cb4a3c9fc2=111445.433 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-010-5c5781cb4a3c9fc2 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=111445.433 ms; declared-cap=1800000 ms | fail | 7 | criterion; 4/7; ratio=0.571429; public=2/2; hidden=2/5; all-checks-required=true | migration-all-callers, migration-warning-once, migration-api-surface |

## Series 70

- Series ID: <code>sha256:be368bc7251067d04b8f2ef75ea77c9ea2d85c9ae86b63ae4738a0d4a8560ff1</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:07:01.359Z</code> to <code>2026-08-27T02:07:01.359Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "S-local-equivalence-refactor-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 70: F05-S-PY-001 revision 1

- Stratum ID: <code>sha256:9428be44d30cecc4e0f1b24826f645fddd39e8692ba1d948f11321dc74db8ef8</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:07:01.359Z</code> to <code>2026-08-27T02:07:01.359Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:276166b476d504579bf8749edfa209116362792d82b00016be7e214bdeed5e29",
      "case_id": "F05-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "2070d2825c0784186af067a96246e5523a444b0a",
        "bundle_digest": "sha256:70d11d1582b0b2bc310bd89fa6da66b4ba8b6c512a6f5a6b951976c489f16254",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-007-f5a79e0d92fdb1db=52693.284 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-007-f5a79e0d92fdb1db | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=52693.291 ms; declared-cap=1800000 ms | pass | 6 | criterion; 6/6; ratio=1.0; public=2/2; hidden=4/4; all-checks-required=true | none |

## Series 71

- Series ID: <code>sha256:bfb61176024a6f420bbd97b34fef8964b562a64b8f20abeb36070ebb682f1def</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:08:03.853Z</code> to <code>2026-08-27T02:08:03.853Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "M-coupled-mutation-test-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 71: F06-M-PY-001 revision 1

- Stratum ID: <code>sha256:089165535ad6554e5c581e679df9d09eb936ff3fee8f2edd332bf4ee7e017748</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:08:03.853Z</code> to <code>2026-08-27T02:08:03.853Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:382c08a96029e368b0c18a95a706cb1e1ded3dd09ebdd037263fcbe7c1c4b2c4",
      "case_id": "F06-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1c6650c345e1597efd1b75d11876d38201a3a4ba",
        "bundle_digest": "sha256:ae6ff40320f66d1831e263a4af0f129f85c1709f49b4c6fc4c72b9e8fb831c9e",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-008-79a7c1108ab317a7=79791.23 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-008-79a7c1108ab317a7 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=79791.241 ms; declared-cap=1800000 ms | pass | 8 | criterion; 8/8; ratio=1.0; public=2/2; hidden=6/6; all-checks-required=true | none |

## Series 72

- Series ID: <code>sha256:c23da073d25f5e91e20b1b67eaf216ed02d8bfd1f064270afa71e8ffc798eb52</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:35:18.969Z</code> to <code>2026-08-27T04:35:18.969Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "L-cross-boundary-calibrated-execution-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "max",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 72: F08-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:8d4ece93dcede5d0e6b2afcf7998ddae367f7e6940b3fae593700754f4afc9a4</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:35:18.969Z</code> to <code>2026-08-27T04:35:18.969Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:82ba9e0a704fcb780f381744bd03d9739324d0f4e2d42b5dba1ca16631f878e8",
      "case_id": "F08-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e67c9fade26c86fc47a2655d96ba4c83f7ed6cfa",
        "bundle_digest": "sha256:c62298b5a0cfcf71789d21bd9e6e5bb5537ff7f1ccee3bd70001ef593eeb0fc6",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-49afd61bc454adc9=372593.588 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-49afd61bc454adc9 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=372593.588 ms; declared-cap=3600000 ms | fail | 11 | criterion; 8/11; ratio=0.727273; public=3/3; hidden=5/8; all-checks-required=true | design-security-boundaries, design-alternative-counterexamples, design-unknown-honesty |

## Series 73

- Series ID: <code>sha256:c25fa54046d7e335935ac128b1d0b458e334776c45dc592e97288b7611fb83cf</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:54:55.762Z</code> to <code>2026-08-27T03:54:55.762Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "S-local-executable-doc-markdown",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 73: F07-S-MD-001 revision 1

- Stratum ID: <code>sha256:7f47a85c4ca7a53bfd0055ac54a9c37b716b54fe2df9028a43a7c926beebed27</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:54:55.762Z</code> to <code>2026-08-27T03:54:55.762Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:7bfe047d68fdc6cb4ec29f3102757ae92bfcd3d29a524290249e0fb1781d52e0",
      "case_id": "F07-S-MD-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1abdeb21a7a282f0c6bbd3190c813b9bb2fa1f4f",
        "bundle_digest": "sha256:e1feeda661711d99adfc9c8e7a0cdd36c046e56377ca84edfe1e36b5b31a00bb",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-012-ce6494b8f453a28e=49031.41 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-012-ce6494b8f453a28e | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=49031.41 ms; declared-cap=1800000 ms | fail | 6 | criterion; 5/6; ratio=0.833333; public=2/2; hidden=3/4; all-checks-required=true | doc-constraint-accurate |

## Series 74

- Series ID: <code>sha256:c281c16b7d891e84521165599310627341d1836389d27a62b79a293cdb18436e</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:45:47.310Z</code> to <code>2026-08-27T03:45:47.310Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 74: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:1bea840af0572007492238de4a64703569f89cafdb405d2b80d5ca6a4bf9c2cb</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:45:47.310Z</code> to <code>2026-08-27T03:45:47.310Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-009-87ca73f14e652da7=66810.307 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-009-87ca73f14e652da7 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=66810.307 ms; declared-cap=1800000 ms | fail | 5 | criterion; 4/5; ratio=0.8; public=1/1; hidden=3/4; all-checks-required=true | hidden-empty-result |

## Series 75

- Series ID: <code>sha256:c7c62d7e7298e1fcdce0090baf18344d7a2d17282e1557d473086149ea3a4a43</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:29:43.723Z</code> to <code>2026-08-27T03:29:43.723Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "M-coupled-seeded-review-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 75: F02-M-PY-001 revision 1

- Stratum ID: <code>sha256:916fda4b1c7585215771614a0ed05d3ed13d407ebf4f36daead40095e749af16</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:29:43.723Z</code> to <code>2026-08-27T03:29:43.723Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:2458ec755c5c1198f87643a08a0c1829e4870448bddf2099fc419fb49af00dcd",
      "case_id": "F02-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6c49a107017f7193d16ae765fee669c1e5c78123",
        "bundle_digest": "sha256:8a063af8c64622c24af22c8eb7123e06e4763507285afe267376165b20f7bc50",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-f9ccfab8da105516=101718.315 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-f9ccfab8da105516 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=101718.315 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | review-symlink-recall, review-ownership-recall, review-interaction, review-evidence |

## Series 76

- Series ID: <code>sha256:c887436052ae9370b7be01cba1e0f126667e9c29e126630d8393247fc9529c44</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T19:01:20.727Z</code> to <code>2026-08-26T19:01:20.727Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "ultra",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 76: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:50cb0ad873794e478b4483393ad49e384645572f3acfbe2d23028477d06b199f</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T19:01:20.727Z</code> to <code>2026-08-26T19:01:20.727Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | codex-f04-l-sol-ultra-20260827-r01=568271.827 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-l-sol-ultra-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=568271.833 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 77

- Series ID: <code>sha256:c91080c1fc8c1968a06d24dc194bd7b95a7d62f8cde5d1aa772f3c28adf1a891</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:22:30.691Z</code> to <code>2026-08-27T02:22:30.691Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "M-coupled-gold-trace-python-js",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 77: F01-M-PYJS-001 revision 1

- Stratum ID: <code>sha256:e1ca1ed992c5d6487387b1c27778a997ab3676525c2b9edb4bf37c2ac310adbb</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:22:30.691Z</code> to <code>2026-08-27T02:22:30.691Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:a8490b3cf30e52857c5edc7871d6cf181bfb2af5ba501c263f3ece99a8b9ef55",
      "case_id": "F01-M-PYJS-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "7a5e4660fc48682c497fcaec4ac2d4738eab15d6",
        "bundle_digest": "sha256:62038f121775e5caa0de935cd5c38f3dcdb11a8478c583a52d8633cbf318f634",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-014-77425a633c6b3587=86416.812 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-014-77425a633c6b3587 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=86416.812 ms; declared-cap=1800000 ms | fail | 8 | criterion; 5/8; ratio=0.625; public=3/3; hidden=2/5; all-checks-required=true | trace-success-chain, trace-fail-open-branches, trace-evidence-integrity |

## Series 78

- Series ID: <code>sha256:cb54632c7e5ab3ad8a0947924c2861d9063069c0899dacfc8f59d3506a5bb0f3</code>
- Study ID: <code>duration-atlas-wave4-recovery</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:17:59.055Z</code> to <code>2026-08-27T03:17:59.055Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "security-isolation",
        "profile_id": "S-local-seeded-bypass-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 78: F09-S-PY-001 revision 1

- Stratum ID: <code>sha256:8cb91e355757194c4c8abfd9b07c9711024be2fd986a6d4404045d4a9c538d83</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:17:59.055Z</code> to <code>2026-08-27T03:17:59.055Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:d5f69e1314f77f79cf86fd20623aa7170e6a9b4e688534c5e74481b0ea99139a",
      "case_id": "F09-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e1c135a9951c95047cd10b954916efe050c67f92",
        "bundle_digest": "sha256:1c4d59bc328976f88b0b9d94832f320bb5203413ccbc7ec9bb94d20b21b37915",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | run-001-40ab8393969ce705=13330.398 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-40ab8393969ce705 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-result-error | complete-terminal; observed-terminal=13330.398 ms; declared-cap=1800000 ms | not-run | 0 | unavailable | unavailable |

## Series 79

- Series ID: <code>sha256:cc1dab82249612b293d8d4d5fa10c940eb89485ac7e7bf822aeffe3d4c0c1572</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:11:02.716Z</code> to <code>2026-08-27T04:11:02.716Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "xhigh",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 79: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:774574f9e776d973b58be7a4ba7ec057e24e91be85f69fb3cc38edfca6f5018c</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:11:02.716Z</code> to <code>2026-08-27T04:11:02.716Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-28eff8f860ac8e39=488483.356 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-28eff8f860ac8e39 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=488483.356 ms; declared-cap=3600000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 80

- Series ID: <code>sha256:cc5c90b91a4adeb862540a124ca21bd0e044922a6155bd78635ecd92b92ddac9</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:45:11.350Z</code> to <code>2026-08-26T18:45:11.350Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "xhigh",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "xhigh",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 80: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:d5242436001479770908463fb14684d0268ad594b0bfd93fdcdb5c4600c4c6b1</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:45:11.350Z</code> to <code>2026-08-26T18:45:11.350Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | grok-f04-l-46-xhigh-20260827-r01=181362.985 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-l-46-xhigh-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=181362.993 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 81

- Series ID: <code>sha256:d0193c90ce4264ce303004ea00454c0d25710219181409dfe4bf298c27154791</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:59:28.963Z</code> to <code>2026-08-27T04:59:28.963Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "S-local-gold-trace-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 81: F01-S-PY-001 revision 1

- Stratum ID: <code>sha256:c92702de2b12e778a09e97b40beb1bf912aee4eb27be8ddfc6c056f59495b099</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:59:28.963Z</code> to <code>2026-08-27T04:59:28.963Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:6bb5179f7978f93e1d019d44d35e29a52b004bf7a9d801e8448cbd05bc449841",
      "case_id": "F01-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "31046588bb74aa5af53c80ea82ad2812808ba06a",
        "bundle_digest": "sha256:ca4a54b9e0db7e49da139793e549bcdd3473e486c241eca0df3db6b6a1bdc6c0",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-e4e5f8e76cc855cb=56650.022 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-e4e5f8e76cc855cb | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=56650.022 ms; declared-cap=1800000 ms | fail | 6 | criterion; 2/6; ratio=0.333333; public=2/2; hidden=0/4; all-checks-required=true | trace-required-nodes, trace-required-edges, trace-evidence-exists, trace-no-distractor |

## Series 82

- Series ID: <code>sha256:d1a117e3c8c6c634982f1c2675e19200ee270cf72e2f4dd6fdfe50a36d85af63</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:01:09.130Z</code> to <code>2026-08-27T02:01:09.130Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "refactor-migration",
        "profile_id": "M-coupled-interface-migration-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 82: F05-M-PY-001 revision 1

- Stratum ID: <code>sha256:e3812079936cf07bbef0e206ae437bbf90072dfa3eb721bbf1177af235808b95</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:01:09.130Z</code> to <code>2026-08-27T02:01:09.130Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:4e93974668ce5719b2b52f07d19b5be28cd26be01add5b7ab05763e7c313e9d7",
      "case_id": "F05-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0dac3f22518b2044bc1e5be41c147adf01fb5b74",
        "bundle_digest": "sha256:fa4d0981251cacf99ac21298ff3b4bc8d36bd98e4e5b54b8b6c4be968cbdec98",
        "instruction_set_digest": "sha256:0c66205f2156339b5ce5a4f38ac3a94becb2a73b839b1da705e4d0650e684b52"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-005-f794c147fee31ef4=90255.067 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-005-f794c147fee31ef4 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=90255.067 ms; declared-cap=1800000 ms | fail | 7 | criterion; 5/7; ratio=0.714286; public=2/2; hidden=3/5; all-checks-required=true | migration-all-callers, migration-warning-once |

## Series 83

- Series ID: <code>sha256:d289ef35be2d242a849a5be60ea0b9113534b725caa4f4a0c9185a8704730bf4</code>
- Study ID: <code>duration-atlas-wave1</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:36:26.352Z</code> to <code>2026-08-26T11:36:26.352Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-terra",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d"
      }
    ]

### Case observations

### Case 83: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:ec4e5aab7b4781f6856920ccf45a47beaa067d72606cfa7b434da36149bae632</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T11:36:26.352Z</code> to <code>2026-08-26T11:36:26.352Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | codex-f04-s-terra-high-20260826-r03=35339.102 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-s-terra-high-20260826-r03 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=35339.102 ms; declared-cap=300000 ms | fail | 2 | aggregate-check; 1/2; ratio=0.5; public=0/0; hidden=0/0; all-checks-required=true | f04-s-python-hidden-v1 |

## Series 84

- Series ID: <code>sha256:d2f6667e7f5b0de6eabec4c0080512cb240508e12159a29415ceb75169e429e8</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:11:06.702Z</code> to <code>2026-08-27T05:11:06.702Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "test-design",
        "profile_id": "L-cross-process-lifecycle-test-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 84: F06-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:ea88c8cdd7bc1b478f48897a319dac9dba996f9a7f78f2f2cbfffcc1be682247</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:11:06.702Z</code> to <code>2026-08-27T05:11:06.702Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:5dc9de1e14cd90c4ef03a3e19f561c4ec0134a8db07099e7a7e34efaddc2d807",
      "case_id": "F06-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a41685e60ec9e83713a0682e1209e09c7085e200",
        "bundle_digest": "sha256:4663cb59494a727556365cfe615251121817906daa9b0f98de76e7ccc062caac",
        "instruction_set_digest": "sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-008-9d2df08335c0b277=28368.778 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-008-9d2df08335c0b277 | infrastructure=success; artifact=missing; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=28368.778 ms; declared-cap=1800000 ms | fail | 11 | criterion; 5/11; ratio=0.454545; public=4/4; hidden=1/7; all-checks-required=true | test-kills-lost-wakeup, test-kills-stale-lease, test-kills-duplicate-owner, test-kills-broad-cleanup, test-repeatability, test-bounded-cleanup |

## Series 85

- Series ID: <code>sha256:d3d36b56dd108c42e149434c3ab643d399b4d21220b570c5b13c52faee8c9422</code>
- Study ID: <code>duration-atlas-wave3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:52:28.869Z</code> to <code>2026-08-26T18:52:28.869Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 85: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:6babb0320fdb5c01490ae6f7c1b0c35fde9727ca5481e346bb3593a8bb2e10c6</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:52:28.869Z</code> to <code>2026-08-26T18:52:28.869Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | codex-f04-l-sol-high-20260827-r01=134933.659 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| codex-f04-l-sol-high-20260827-r01 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=134933.673 ms; declared-cap=900000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 86

- Series ID: <code>sha256:d5781820daf17c746f9ed9d0ad830a2a069d75d9d158b223740465f7670111bc</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:33:15.682Z</code> to <code>2026-08-27T05:33:15.682Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "S-local-gold-trace-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 86: F01-S-PY-001 revision 1

- Stratum ID: <code>sha256:c88d90dfae3ada6785b811b8a6f05bc6579402a4558c6e86276e0e23018b0841</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:33:15.682Z</code> to <code>2026-08-27T05:33:15.682Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:6bb5179f7978f93e1d019d44d35e29a52b004bf7a9d801e8448cbd05bc449841",
      "case_id": "F01-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "31046588bb74aa5af53c80ea82ad2812808ba06a",
        "bundle_digest": "sha256:ca4a54b9e0db7e49da139793e549bcdd3473e486c241eca0df3db6b6a1bdc6c0",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-009-c02f4a4c4f9d3ffe=181656.97 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-009-c02f4a4c4f9d3ffe | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=181656.97 ms; declared-cap=1800000 ms | fail | 6 | criterion; 2/6; ratio=0.333333; public=2/2; hidden=0/4; all-checks-required=true | trace-required-nodes, trace-required-edges, trace-evidence-exists, trace-no-distractor |

## Series 87

- Series ID: <code>sha256:d72f383eb3bbbdb082483f65f9b7890d56a430bb62da0ccfc60ab8ebb645ed2d</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:20:00.197Z</code> to <code>2026-08-27T02:20:00.197Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "L-cross-boundary-deterministic-python-bash",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 87: F04-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:d6c9750b2a8eb7ea40759e93babb787e120c9a06cfd63d802af95ca614eac161</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:20:00.197Z</code> to <code>2026-08-27T02:20:00.197Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:668f0779c196cedddd95c7d4dd14ee43881febb56235ea3b7fea621ac5ff5889",
      "case_id": "F04-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "970464fc8d9bf5825f07bf35288e3058373d63b0",
        "bundle_digest": "sha256:eb7d0d5a1c1fa24983c8ae41afcb3ecfd3ffd9df64607ad47613972feb0c5d77",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=1; fail=0; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-pass-user-result | single observation; raw point | run-012-0da5e12408544291=112737.879 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-012-0da5e12408544291 | infrastructure=success; artifact=valid; online=pass; offline=not-run; basis=strong-online-oracle; failure=None | complete-terminal; observed-terminal=112737.884 ms; declared-cap=1800000 ms | pass | 4 | criterion; 4/4; ratio=1.0; public=2/2; hidden=2/2; all-checks-required=true | none |

## Series 88

- Series ID: <code>sha256:d90338a6438389e2cc5a6a081aa0759f73543b683168bec97b44870138de072a</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:30:15.506Z</code> to <code>2026-08-27T02:30:15.506Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "repository-trace",
        "profile_id": "S-local-gold-trace-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 88: F01-S-PY-001 revision 1

- Stratum ID: <code>sha256:0702ed8c3838df3f4f3d4a340539b8894bd1a90fa3c8f6d22e5ae0759a820800</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:30:15.506Z</code> to <code>2026-08-27T02:30:15.506Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:6bb5179f7978f93e1d019d44d35e29a52b004bf7a9d801e8448cbd05bc449841",
      "case_id": "F01-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "31046588bb74aa5af53c80ea82ad2812808ba06a",
        "bundle_digest": "sha256:ca4a54b9e0db7e49da139793e549bcdd3473e486c241eca0df3db6b6a1bdc6c0",
        "instruction_set_digest": "sha256:495ef09bdc9e57a6d24e686168a3d2e409fecec071caf7d7a0bf4a79cf050edd"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-016-eb96bfd1078b0676=80652.138 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-016-eb96bfd1078b0676 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=80652.138 ms; declared-cap=1800000 ms | fail | 6 | criterion; 4/6; ratio=0.666667; public=2/2; hidden=2/4; all-checks-required=true | trace-required-nodes, trace-required-edges |

## Series 89

- Series ID: <code>sha256:d998ecbf03198e2193344deb6b813eaa0edcdf6fd250ec69abd0418166e5ce4e</code>
- Study ID: <code>duration-atlas-wave2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:25:07.938Z</code> to <code>2026-08-26T18:25:07.938Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "bounded-implementation",
        "profile_id": "S-local-deterministic-python",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "host-sync",
        "cli_version": "1.0.5",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "grok-4.6",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:0af0b04e37859cd04e8dc38f37fc9e8b3f95ff511a6c9a5ce0900922bcfa6f01"
      }
    ]

### Case observations

### Case 89: F04-S-PY-001 revision 1

- Stratum ID: <code>sha256:1f7bcc191a80b293965d707bc65d5d23289bcdb35e0773a0dbcad243661f7815</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-26T18:25:07.938Z</code> to <code>2026-08-26T18:25:07.938Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:62c94e37eaf560b7579b022b488831e52a3ce5f8fdd3e1545a36df8f6178537c",
      "case_id": "F04-S-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a2118775cc5209fac540865f170f576446e33c35",
        "bundle_digest": "sha256:412bf33ac5c012909d1f7cc82b5b1777f28bc9008c0056522c1a3846bbb6f131",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | grok-f04-s-46-medium-20260827-r01=1647.74 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| grok-f04-s-46-medium-20260827-r01 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=provider-startup-unknown | complete-terminal; observed-terminal=1647.74 ms; declared-cap=900000 ms | not-run | 0 | unavailable | unavailable |

## Series 90

- Series ID: <code>sha256:db8fb26bd67a933a8570302054adcf16f665293f74e844d0fbadb2cf3949c1d8</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:35:28.172Z</code> to <code>2026-08-27T01:35:28.172Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "M-coupled-replayable-runbook",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 90: F07-M-MDBASH-001 revision 1

- Stratum ID: <code>sha256:420a491e0956543d050dce405149da9112352f46b933bea03a5702c80a4ec23e</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T01:35:28.172Z</code> to <code>2026-08-27T01:35:28.172Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:50c00b817db762f4cda0202deb1d9fe791cbf365b15993779b2299ac140c2c58",
      "case_id": "F07-M-MDBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "a4a7c2d549b3bf1e3a7ed29719078f54d124353c",
        "bundle_digest": "sha256:ee52600a304e285b974e3b8b3ce7b97080717dc903d5c09ecfe8601c5569d5b5",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-995688fc397ebf01=118243.023 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-995688fc397ebf01 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=118243.023 ms; declared-cap=1800000 ms | fail | 9 | criterion; 7/9; ratio=0.777778; public=3/3; hidden=4/6; all-checks-required=true | runbook-fact-accuracy, runbook-owned-restart |

## Series 91

- Series ID: <code>sha256:e091d24873fbf13546924eab88e840ef984215b9c555eb02731ec3c88bfb04cb</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T06:03:04.823Z</code> to <code>2026-08-27T06:03:04.823Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "max",
            "status": "rejected"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 91: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:96239078e7c76e3ed70e9e4ef7ce8a9278e317b113e6f090c968e570c4d798a2</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T06:03:04.823Z</code> to <code>2026-08-27T06:03:04.823Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=0; unknown=1 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-unknown-terminal | single observation; raw point | run-001-b555a63a5f2dc998=1572.332 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-b555a63a5f2dc998 | infrastructure=failure; artifact=missing; online=unavailable; offline=not-run; basis=unavailable; failure=generation-setting-rejected | complete-terminal; observed-terminal=1572.332 ms; declared-cap=1800000 ms | not-run | 0 | unavailable | unavailable |

## Series 92

- Series ID: <code>sha256:e18033e79ca6da88bed0a146c5bed9f6c6c9c5b4a5317d05264cd6c6407b8c5e</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:00:27.692Z</code> to <code>2026-08-27T05:00:27.692Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "M-coupled-seeded-review-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 92: F02-M-PY-001 revision 1

- Stratum ID: <code>sha256:43e4949f0e490b1ba53407b954bb27f3fcf0135740c9d98f1486c53f5165cf9a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:00:27.692Z</code> to <code>2026-08-27T05:00:27.692Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:2458ec755c5c1198f87643a08a0c1829e4870448bddf2099fc419fb49af00dcd",
      "case_id": "F02-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6c49a107017f7193d16ae765fee669c1e5c78123",
        "bundle_digest": "sha256:8a063af8c64622c24af22c8eb7123e06e4763507285afe267376165b20f7bc50",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-6090cc0ecbc71b38=196820.85 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-6090cc0ecbc71b38 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=196820.85 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | review-symlink-recall, review-ownership-recall, review-interaction, review-evidence |

## Series 93

- Series ID: <code>sha256:e357efc5acdb92e919f10b0c1993180509b75e95a9d010085c01b9d0f662843e</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:56:37.040Z</code> to <code>2026-08-27T05:56:37.040Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "xhigh",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "xhigh",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 93: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:f3abc7682abdc792baa756b61836275c575d62453bd88ef60a104004ee3916b3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:56:37.040Z</code> to <code>2026-08-27T05:56:37.040Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-361a0549df85bf5f=48403.744 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-361a0549df85bf5f | infrastructure=success; artifact=missing; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=48403.744 ms; declared-cap=1800000 ms | fail | 9 | criterion; 0/9; ratio=0.0; public=0/3; hidden=0/6; all-checks-required=true | workspace-1, workspace-2, workspace-3, diagnosis-deterministic-barrier, diagnosis-ordering-cause, diagnosis-restart-state, diagnosis-regression-reliable, diagnosis-cleanup-bounded, diagnosis-semantics-honest |

## Series 94

- Series ID: <code>sha256:e5fc2d0eab090582305661e7ee0032eae576b439301e3ed1ac523438753f38b3</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:19:44.082Z</code> to <code>2026-08-27T05:19:44.082Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "M-coupled-seeded-review-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 94: F02-M-PY-001 revision 1

- Stratum ID: <code>sha256:2d830ce489b91054b52efe6c32845b9d515df1069be59a4978c5e5fe014f24bf</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:19:44.082Z</code> to <code>2026-08-27T05:19:44.082Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:2458ec755c5c1198f87643a08a0c1829e4870448bddf2099fc419fb49af00dcd",
      "case_id": "F02-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6c49a107017f7193d16ae765fee669c1e5c78123",
        "bundle_digest": "sha256:8a063af8c64622c24af22c8eb7123e06e4763507285afe267376165b20f7bc50",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-004-cb1f76abd54ed185=279038.423 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-004-cb1f76abd54ed185 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=279038.423 ms; declared-cap=1800000 ms | fail | 8 | criterion; 2/8; ratio=0.25; public=2/2; hidden=0/6; all-checks-required=true | review-symlink-recall, review-ownership-recall, review-interaction, review-ranking, review-evidence, review-false-positive |

## Series 95

- Series ID: <code>sha256:e69427aab764ef3e95f210fcc39a9a76a9672c6436d1118953c9c088c8681225</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:12:25.897Z</code> to <code>2026-08-27T05:12:25.897Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "M-coupled-calibrated-architecture",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 95: F08-M-MDJSON-001 revision 1

- Stratum ID: <code>sha256:c2247c7bed8231c49edb8acf78225aa7669dd0aa4c589043261e0279217bbe0a</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:12:25.897Z</code> to <code>2026-08-27T05:12:25.897Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:b387c811c5371e97f84eba0e6793e2ad86f743c6eb3e3f45109f1b66092d2c62",
      "case_id": "F08-M-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1508653b1462b14f5ac7d145ee36cb821a0f5373",
        "bundle_digest": "sha256:bddda853cc6aebed863694e3dcfd79a3b562ce026f31c2e66d1ce3fd9822fc0d",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-010-3339588d55d9be29=101045.282 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-010-3339588d55d9be29 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=101045.282 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | design-invariant-coverage, design-option-counterexamples, design-migration-observability, design-unknown-honesty |

## Series 96

- Series ID: <code>sha256:e8c1b948fa9099de6aa1e63f3513ce4fd4da4af9b721c2756dc67534716d1f3d</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:14:00.759Z</code> to <code>2026-08-27T03:14:00.759Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "L-cross-document-migration-runbook",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 96: F07-L-MDPYBASH-001 revision 1

- Stratum ID: <code>sha256:4ba6c72433a9d4f871f2b45064d03caef36044fedf3ae17682fac392e4c6ff18</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:14:00.759Z</code> to <code>2026-08-27T03:14:00.759Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:6bbae94196fc484316bf77595f39c1b76f7fed5e0a85a1550b415248b2bf07c1",
      "case_id": "F07-L-MDPYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "13c61ee74db151852825b87b019b718e5c2dd5e7",
        "bundle_digest": "sha256:26db2a2b4e3190d22f2ba9c19216f7e48d17d1474479d3760ac230a2cf0cf32d",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-036-ece6d80c5700ed21=189818.452 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-036-ece6d80c5700ed21 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=189818.452 ms; declared-cap=1800000 ms | fail | 10 | criterion; 6/10; ratio=0.6; public=3/3; hidden=3/7; all-checks-required=true | docs-current-target-facts, docs-migration-order, docs-ownership-consistency, docs-no-early-removal |

## Series 97

- Series ID: <code>sha256:ebe3750d4505e98b8b112d63efa54958a3cc643599be85874f9e73d6d406fc8a</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:09:25.078Z</code> to <code>2026-08-27T05:09:25.078Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "S-local-executable-doc-markdown",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "medium",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "medium",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 97: F07-S-MD-001 revision 1

- Stratum ID: <code>sha256:ad01902081ec03cae02d4e5052fe6447b65ad903b130b08861577c2ae0e469dc</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:09:25.078Z</code> to <code>2026-08-27T05:09:25.078Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:7bfe047d68fdc6cb4ec29f3102757ae92bfcd3d29a524290249e0fb1781d52e0",
      "case_id": "F07-S-MD-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1abdeb21a7a282f0c6bbd3190c813b9bb2fa1f4f",
        "bundle_digest": "sha256:e1feeda661711d99adfc9c8e7a0cdd36c046e56377ca84edfe1e36b5b31a00bb",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-006-b36e517437e66ec9=37095.261 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-006-b36e517437e66ec9 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=37095.261 ms; declared-cap=1800000 ms | fail | 6 | criterion; 2/6; ratio=0.333333; public=2/2; hidden=0/4; all-checks-required=true | doc-command-replay, doc-constraint-accurate, doc-invalid-form-removed, doc-link-integrity |

## Series 98

- Series ID: <code>sha256:ed3a4bbe6e9ae37aa40a6036c680df305e19ccd14fd4aa0129c07a167518ffec</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:45:22.597Z</code> to <code>2026-08-27T05:45:22.597Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "evidence-synthesis",
        "profile_id": "L-cross-evidence-decision-record",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "xhigh",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "xhigh",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 98: F12-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:b37d6ff5d2a8cfcd5d15e42a6810c3a74fe3b9d772e316bc94d5ab498db3eb8e</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:45:22.597Z</code> to <code>2026-08-27T05:45:22.597Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:362480840d6a640750f7e1e17edc73e1f883086d77a57cd32f56955d85b3908e",
      "case_id": "F12-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "b787c0e9ff8637c53fe217ea416ee6a4226aa529",
        "bundle_digest": "sha256:bc1b15bc617e67347eff21e7268517c7d25e462ecf73d8f60be88dcce497fa23",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-9b3208f07e508e3a=387475.599 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-9b3208f07e508e3a | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=387475.599 ms; declared-cap=1800000 ms | fail | 12 | criterion; 5/12; ratio=0.416667; public=3/3; hidden=2/9; all-checks-required=true | synthesis-claim-provenance, synthesis-incident-security, synthesis-migration-operations, synthesis-decision-trace, synthesis-alternative-rejection, synthesis-unknown-honesty, synthesis-refresh-plan |

## Series 99

- Series ID: <code>sha256:f0b5b1d768ddb3639553a568d690b3e3057cd6979e04d17bf65df164aff5e94c</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:09:34.235Z</code> to <code>2026-08-27T02:09:34.235Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "devcontainer-operations",
        "profile_id": "L-cross-boundary-rebuild-recovery",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 99: F11-L-BASHDOCKER-001 revision 1

- Stratum ID: <code>sha256:0a5fb3ea0406c05f80c71de0f8109f61dfee4c02a702daa6532fc37b691cd678</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T02:09:34.235Z</code> to <code>2026-08-27T02:09:34.235Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:51ab723de0f8cb7ac6970963b1482015e9563e2738e07c4c55ba7608606ee364",
      "case_id": "F11-L-BASHDOCKER-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "f33a8ed2b4f8bd932aeab19b7de865309860ce67",
        "bundle_digest": "sha256:e5bdf742336d33afeb66a9825ac0091fd536b587d50b8544598da31dc8da0ef7",
        "instruction_set_digest": "sha256:e4e2bb7864102d83bc3f0e066d5772c0182c409253bf77542c3f2654b2b6b822"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-009-52e8d594af96b186=262673.3 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-009-52e8d594af96b186 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=262673.3 ms; declared-cap=1800000 ms | fail | 11 | criterion; 6/11; ratio=0.545455; public=4/4; hidden=2/7; all-checks-required=true | ops-lifecycle-ownership, ops-migration-fault-cuts, ops-reopen-resume, ops-marker-verification, ops-recovery-doc |

## Series 100

- Series ID: <code>sha256:f1b8f2174b17805a4f1ac0ad9ab3c66207315709e613371ec1febc15fd337863</code>
- Study ID: <code>duration-atlas-wave6-provider</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:25:33.249Z</code> to <code>2026-08-27T05:25:33.249Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "documentation-runbook",
        "profile_id": "S-local-executable-doc-markdown",
        "size": "S",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "grok",
        "cli_source": "container-image",
        "cli_version": "1.0.3",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "applied_value": "high",
            "key": "effort",
            "namespace": "grok.reasoning",
            "requested_value": "high",
            "status": "applied"
          }
        ],
        "model_identity": {
          "identity_confidence": "exact",
          "requested_alias": "grok-4.6",
          "requested_source": "flag",
          "resolved_id": "grok-4.6"
        },
        "permission_mode": "automatic",
        "provider": "grok",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 100: F07-S-MD-001 revision 1

- Stratum ID: <code>sha256:f576c02b1b1625414179f124f56114ab859c0c6fbe20270e2e588d31c69cb376</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T05:25:33.249Z</code> to <code>2026-08-27T05:25:33.249Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:7bfe047d68fdc6cb4ec29f3102757ae92bfcd3d29a524290249e0fb1781d52e0",
      "case_id": "F07-S-MD-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1abdeb21a7a282f0c6bbd3190c813b9bb2fa1f4f",
        "bundle_digest": "sha256:e1feeda661711d99adfc9c8e7a0cdd36c046e56377ca84edfe1e36b5b31a00bb",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-006-6029cdb4396a27bf=48167.606 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-006-6029cdb4396a27bf | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=48167.606 ms; declared-cap=1800000 ms | fail | 6 | criterion; 2/6; ratio=0.333333; public=2/2; hidden=0/4; all-checks-required=true | doc-command-replay, doc-constraint-accurate, doc-invalid-form-removed, doc-link-integrity |

## Series 101

- Series ID: <code>sha256:f7befba023af9936322d7fd0a5e3ed00565e160cf5622075643938b6e9d30d8c</code>
- Study ID: <code>duration-atlas-wave4-corpus</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:05:05.952Z</code> to <code>2026-08-27T03:05:05.952Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "code-review",
        "profile_id": "M-coupled-seeded-review-python",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "medium",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 101: F02-M-PY-001 revision 1

- Stratum ID: <code>sha256:a23076b8686adc580a533b334dca66c7db2515c020a060b62f8424ee81ae91a8</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:05:05.952Z</code> to <code>2026-08-27T03:05:05.952Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:2458ec755c5c1198f87643a08a0c1829e4870448bddf2099fc419fb49af00dcd",
      "case_id": "F02-M-PY-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "6c49a107017f7193d16ae765fee669c1e5c78123",
        "bundle_digest": "sha256:8a063af8c64622c24af22c8eb7123e06e4763507285afe267376165b20f7bc50",
        "instruction_set_digest": "sha256:9066de8591651471ec73222275ccd5ab79992d9f0d6648ae515a15ed830f1749"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-032-4a12a4754b552ed6=93656.282 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-032-4a12a4754b552ed6 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=93656.282 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | review-symlink-recall, review-ownership-recall, review-interaction, review-evidence |

## Series 102

- Series ID: <code>sha256:f86d03a8b11b15ea26c4b6b88e9a820c472850ac9b22eb5ee9133686fd8005de</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:05:16.602Z</code> to <code>2026-08-27T04:05:16.602Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "L-cross-boundary-calibrated-execution-design",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "xhigh",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 102: F08-L-MDJSON-001 revision 1

- Stratum ID: <code>sha256:a39182e803f87dc2add778ea82375d23043057d97d77b6a4ed8485d23ac0b665</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:05:16.602Z</code> to <code>2026-08-27T04:05:16.602Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:82ba9e0a704fcb780f381744bd03d9739324d0f4e2d42b5dba1ca16631f878e8",
      "case_id": "F08-L-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "e67c9fade26c86fc47a2655d96ba4c83f7ed6cfa",
        "bundle_digest": "sha256:c62298b5a0cfcf71789d21bd9e6e5bb5537ff7f1ccee3bd70001ef593eeb0fc6",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-003-3dab55ace564cde8=342032.799 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-003-3dab55ace564cde8 | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=342032.799 ms; declared-cap=3600000 ms | fail | 11 | criterion; 8/11; ratio=0.727273; public=3/3; hidden=5/8; all-checks-required=true | design-security-boundaries, design-alternative-counterexamples, design-unknown-honesty |

## Series 103

- Series ID: <code>sha256:f9389a11a477be16d74cf0a2c9579cc1984b16425bf5493ba8c9a4bbf65a77f8</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:19:13.689Z</code> to <code>2026-08-27T03:19:13.689Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "architecture-design",
        "profile_id": "M-coupled-calibrated-architecture",
        "size": "M",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "high",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 103: F08-M-MDJSON-001 revision 1

- Stratum ID: <code>sha256:67bd0e5dc9e2e1aec3607ad63f1f27ca2fd7a0c46e13aee5f4ce36b87e31e1d3</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T03:19:13.689Z</code> to <code>2026-08-27T03:19:13.689Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:b387c811c5371e97f84eba0e6793e2ad86f743c6eb3e3f45109f1b66092d2c62",
      "case_id": "F08-M-MDJSON-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "1508653b1462b14f5ac7d145ee36cb821a0f5373",
        "bundle_digest": "sha256:bddda853cc6aebed863694e3dcfd79a3b562ce026f31c2e66d1ce3fd9822fc0d",
        "instruction_set_digest": "sha256:38bd24a8583c37a87fc13adb769833ff2c2f12b6dafe29af3239795568cf56f6"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-001-d017aba0f530eb2c=148137.452 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-001-d017aba0f530eb2c | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=148137.452 ms; declared-cap=1800000 ms | fail | 8 | criterion; 4/8; ratio=0.5; public=2/2; hidden=2/6; all-checks-required=true | design-invariant-coverage, design-option-counterexamples, design-migration-observability, design-unknown-honesty |

## Series 104

- Series ID: <code>sha256:fe4c8eaec3584d934aaea49887d2488801f99fb0cb58e8c383419e66bda8310e</code>
- Study ID: <code>duration-atlas-wave5-depth</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:31:37.639Z</code> to <code>2026-08-27T04:31:37.639Z</code>
- Characterization: <code>not-assessed</code>; <code>study-specific-precision-and-coverage-criteria-unavailable</code>
- Execution surface(s): <code>isolated-provider-container</code>

### Exact profile and configuration

    {
      "configuration": {
        "configuration_id": "C0",
        "independence_policy": "fresh-ephemeral-session",
        "lane": "isolated",
        "nested_delegation": "disabled",
        "participant_plan": "primary-only",
        "participants_actual": 1,
        "peak_concurrent": 0,
        "relation": "primary-only",
        "workers_actual": 0
      },
      "profile": {
        "family": "failing-test-diagnosis",
        "profile_id": "L-cross-process-restart-diagnosis",
        "size": "L",
        "source_type": "fixture"
      }
    }

### Exact environment

    {
      "compaction": "unknown",
      "competing_load": "unknown",
      "dependency_cache": "not-applicable",
      "docker_cache": "warm",
      "image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb",
      "machine_class": "docker-limited-2cpu-2g",
      "provider_prompt_cache": "unknown",
      "repository_cache": "not-applicable",
      "session_context": "fresh",
      "timezone": "UTC"
    }

### Exact participant, model, requested/applied settings, and surface

    [
      {
        "cli_name": "codex",
        "cli_source": "container-image",
        "cli_version": "0.146.0",
        "execution_surface": "isolated-provider-container",
        "generation_settings": [
          {
            "key": "effort",
            "namespace": "codex.reasoning",
            "requested_value": "max",
            "status": "unknown"
          }
        ],
        "model_identity": {
          "identity_confidence": "alias-only",
          "requested_alias": "gpt-5.6-sol",
          "requested_source": "flag"
        },
        "permission_mode": "automatic",
        "provider": "codex",
        "role": "implementer",
        "runtime_image_digest": "sha256:40a4841979bd64d5a991f19e59021cfe350e357f875c17d3456d96eef60ca2fb"
      }
    ]

### Case observations

### Case 104: F03-L-PYBASH-001 revision 1

- Stratum ID: <code>sha256:36348d0d67a61247dd0b1b8f53549bcaed8a87410b07308bf23b02148ead04e5</code>
- Evidence state: <code>single-observation</code>
- Observation window: <code>2026-08-27T04:31:37.639Z</code> to <code>2026-08-27T04:31:37.639Z</code>
- Runs / observation blocks: 1 / 1

#### Exact case identity

    {
      "capsule_digest": "sha256:9ff03488e8d8404e8fbe4d2e214b108e61e6db0bef35d75bab5ca2e288ed4115",
      "case_id": "F03-L-PYBASH-001",
      "revision": 1,
      "snapshot": {
        "base_sha": "0699e11f5ec120792b3db328e3b5de4de1f1b6be",
        "bundle_digest": "sha256:195995c506c7ca932707f6556ccef1f1807b2327f79907d7e12d3a6130d30c72",
        "instruction_set_digest": "sha256:83239308c474dce5e9bcdcf98bf70cdd5631410b63e77e2e16ccceb3782fa700"
      },
      "strong_online_oracle": true
    }

| Count group | Values |
| --- | --- |
| Quality | pass=0; fail=1; unknown=0 |
| Censoring | complete=1; right=0; administrative=0 |
| First artifact | progress=0; not-observed=1; not-applicable=0; unknown=0 |

| Duration view | Evidence | Raw observed points | Observed range |
| --- | --- | --- | --- |
| quality-fail-terminal | single observation; raw point | run-002-8febe3786dc60c0e=217853.034 ms | not available |

#### Content-free quality evidence

| Run | Outcome | Censoring / cap | Evaluator status | Check count | Criterion score | Failed criterion IDs |
| --- | --- | --- | --- | --- | --- | --- |
| run-002-8febe3786dc60c0e | infrastructure=success; artifact=valid; online=fail; offline=not-run; basis=online-fail; failure=online-validation-failed | complete-terminal; observed-terminal=217853.034 ms; declared-cap=3600000 ms | fail | 9 | criterion; 7/9; ratio=0.777778; public=3/3; hidden=4/6; all-checks-required=true | diagnosis-ordering-cause, diagnosis-cleanup-bounded |

## Limitations

- This report preserves the atlas strata and does not generalize beyond the exact environment, model identity, generation-setting status, execution surface, case revision, and observation window shown above.
- Observed min/max values describe only the displayed same-case points; they are not uncertainty or prediction intervals.
- Right- or administratively-censored terminal times are incomplete observations and are counted separately.
- Criterion-level details are limited to the aggregate's content-free score fields and failed IDs; evaluator rubric text is not present and is not reconstructed.
- Unmeasured catalog cells remain unmeasured; no adjacent family, size, model, or provider value is substituted.
- Raw prompts, transcripts, private reasoning, generated artifacts, and evaluator output are outside this content-free report.
