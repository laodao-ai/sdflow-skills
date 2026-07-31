---
task: 6
status: DONE_WITH_CONCERNS
---

# Task 6 implementer report — documentation boundaries

## Scope

Implemented only the Task 6 documentation and known-boundary synchronization. `tickets.md` was not edited and no task checkpoint was created.

## Changes

- Updated the canonical generation-process guide and the dogfood copy with the project-local schema boundary:
  - schema supplies artifact/dependency/`skip_specs` structure and delegation prompts;
  - delegation is prompt-layer routing, not a mechanical execution guarantee;
  - the version gate keeps built-in `spec-driven` when the project-local schema cannot be installed;
  - migration writes in-flight change schema data before switching `config.schema`, and failed backfill does not switch config;
  - fork drift detection and automatic rebase are explicitly out of scope.
- Updated `README.md` to describe the same consumer-project behavior and limitations.
- Updated `openspec/roadmaps/openspec-1.7.0-followup/roadmap.md` to mark P1 delivered and retain the fork-drift item as a follow-up, without expanding into P2/P3.
- Recorded the follow-up as todolist `T264`.

## Verification

- `git diff --check`: passed.
- Full `pytest`: intentionally not run, per user instruction.
- `setup.sh` / bundle refresh: intentionally not run. The attempted `init.py update --dev` was aborted immediately; the dogfood generation-process copy was synchronized directly in this change.
- `issues.py reindex`: passed; regenerated `openspec/issues/INDEX.md` with T264 included.
- `tickets.md`: unchanged by this implementer.
- Task checkpoint: not created.

## Concerns

The documentation and canonical/dogfood workflow copies were updated, but the normal installer refresh and full test suite were skipped at the user's direction. The next verification pass should run the focused documentation/sync checks and `git diff --check` before review.
