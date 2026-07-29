# Task 4 delivery report: fifth gate and Windows CI

## Delivered

- `setup.sh` now runs `hack/check_encoding_hygiene.py` as an independent fifth
  mechanical gate after the existing four gates. A failure preserves the
  checker's per-file contract diagnostics and adds one repair pointer to the
  four-line template in `CLAUDE.md`.
- The existing `CLAUDE.md` live documentation already contained the required
  entry-script template and fifth-gate explanation; it was verified and left
  unchanged rather than duplicated.
- `.github/workflows/windows-recorder-smoke.yml` now watches every affected
  script directory and uses `shell: bash` for every `run` step. It covers:
  forced-GBK `setup.sh`, forced-GBK `init.py update` in a new Git repository,
  the seven text subprocess call sites reached by `issues.py` (4),
  `retro_report.py` (1), and `ship_gate.py` (2), plus an invalid UTF-8-byte
  replacement fixture.
- The workflow also removes `PYTHONIOENCODING`, sets `chcp 936`, and runs
  `setup.sh` once on the console and once redirected, rejecting encoding
  exceptions and tracebacks in redirected output.
- Registered non-blocking todo `T263` through the repository's
  `sdflow-issues` CLI contract. Its immutable `change` field is
  `fix-windows-encoding-crash`; it records the pre-existing inconsistency
  between `command -v python3` probes and the validated interpreter chooser.

## Validation

| Command | Result |
| --- | --- |
| `python3 hack/check_encoding_hygiene.py` | PASS — all entry scripts satisfy the encoding prelude contract. |
| `bash setup.sh` | PASS — all five gates ran; output had no `UnicodeEncodeError` or traceback. |
| `python3 -m pytest -q hack/tests/test_encoding_hygiene.py hack/tests/test_subprocess_encoding_contract.py` | PASS — 10 passed. |
| `python3 -m pip install --user PyYAML` then `python3 -c "import yaml; yaml.safe_load(...)"` | PASS — workflow YAML syntax parsed locally. PyYAML was absent initially, so it was installed only in the local user environment for this structural check. |
| Local workflow structural assertion | PASS — both path trigger lists include all affected directories; every `run` step declares Bash; required GBK, CP936, subprocess, and fixture commands are present. |
| `bash -n setup.sh` and `git diff --check` | PASS. |

## Windows boundary

This machine cannot execute the `windows-latest` GitHub-hosted runner path,
including its real CP936 console and redirected-pipe behavior. The workflow
has been syntax- and structure-validated locally; the CP936 behavior remains
intentionally verified by the newly expanded Windows CI job.
