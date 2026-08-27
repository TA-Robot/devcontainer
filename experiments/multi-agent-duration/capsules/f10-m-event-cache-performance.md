# F10-M-PY-001: instrument event summarizer performance

Complete `instrumentation.py` and write `performance.json` comparing I/O, decode, and cache hypotheses. Production, tests, benchmark, and validator are frozen.

Requirements:

- record query, open, byte, line, decode, cache-hit, and cache-miss counters;
- preserve the line iterator and functional summaries;
- run separate cold and repeated logically-identical-path workloads in rotated order;
- retain multiple raw blocks and the identity-reuse counterfactual;
- identify identity-keyed cache misses as conditionally dominant for repeated distinct `Path` objects;
- quantify reopen and duplicate-decode work as cold/secondary costs;
- record environment and uncertainty without treating local timing as portable gold.

Only `instrumentation.py` and `performance.json` may be changed. Do not modify source, tests, validator, or add contract-external files.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 bench.py --instrument instrumentation.py --output observations.json
python3 tools/validate_performance.py performance.json observations.json
```

Return the cold/warm counter comparison and validation results.
