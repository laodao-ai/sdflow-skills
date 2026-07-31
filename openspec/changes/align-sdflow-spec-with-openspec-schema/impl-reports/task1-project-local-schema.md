# Task 1 implementation report — project-local schema contract

Status: DONE

## Scope

- Ticket: Task 1 — 建立可验证的 project-local schema 契约
- R-ID: SW-SCHEMA
- Implemented only the schema fork and its contract changes. No `tickets.md` checkbox was changed and no task checkpoint tag was created.

## Red → green vertical slice

### Red

Command:

```text
openspec schema validate sdflow-spec-driven
```

Result: exit 1 — `Schema 'sdflow-spec-driven' not found`; only the built-in `spec-driven` schema was available.

### Green

After running the required fork command, adding the delegation blocks, updating dependency edges, and making `design` unconditional:

```text
openspec schema validate sdflow-spec-driven
```

Result: exit 0 — `✓ Schema 'sdflow-spec-driven' is valid`.

## Implemented contract

- Forked with `openspec schema fork spec-driven sdflow-spec-driven`; did not use `schema init`.
- Added the `sdflow:delegation` start/end block to all four artifact instructions. The block tells the official workflow entry point to stop and ask the human to invoke `/sdflow-spec`.
- Preserved the four artifact IDs and output modes: `proposal.md`, `specs/**/*.md`, `design.md`, and `tasks.md`.
- Changed `specs.requires` to `proposal, design`.
- Changed `tasks.requires` to `proposal, design, specs`.
- Replaced the conditional design guidance with an explicit unconditional `design.md` instruction.
- Copied the identical schema tree to both the bundle authority and this repository's dogfood instance:
  - `sdflow-init/assets/schemas/sdflow-spec-driven/`
  - `openspec/schemas/sdflow-spec-driven/`

## Verification

The following checks passed:

```text
openspec schema validate sdflow-spec-driven
SCHEMA_CONTRACT_PASS
git diff --check
openspec validate align-sdflow-spec-with-openspec-schema --strict
```

`openspec instructions` was also run with `--schema sdflow-spec-driven --json` for all four artifacts. It confirmed:

- all four instructions contain both delegation markers;
- `specs` dependencies are `proposal, design`;
- `tasks` dependencies are `proposal, design, specs`;
- `design` instruction states that `design.md` is unconditional.

The bundle and dogfood schema files were byte-identical in the final contract check.

## Concerns

None. Tasks 2–5 (installer/version gate, `sdflow-spec` consumer changes, dogfood migration, and broader regression coverage) remain outside Task 1 and were not modified.
