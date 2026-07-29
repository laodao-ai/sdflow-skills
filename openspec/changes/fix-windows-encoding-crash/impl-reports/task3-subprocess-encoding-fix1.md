# Task 3 — subprocess encoding follow-up

## Scope

Addressed the two Important review findings in the remaining direct text-mode
subprocess sites:

- `sdflow-issues/scripts/migrate_legacy.py:322` (`run_reindex`)
- `sdflow-issues/scripts/sdflow_issues_core/__init__.py:1059` (`detect_change`)

Both already selected UTF-8 and now also use `errors="replace"`, so malformed
child-process bytes cannot turn diagnostics or branch detection into a decoding
crash on Windows.

## Regression guard

`hack/tests/test_subprocess_encoding_contract.py` now discovers every authored
production Python module (excluding tests and generated `openspec/` copies),
rather than relying on the earlier fixed 13-site file map. It inventories all
15 direct `subprocess.run(..., text=True)` call sites and requires explicit
`encoding="utf-8"` plus `errors="replace"` at each site. The raw-byte git
wrapper contract remains separately asserted.

## Verification

```text
pytest hack/tests/test_subprocess_encoding_contract.py -q
```
