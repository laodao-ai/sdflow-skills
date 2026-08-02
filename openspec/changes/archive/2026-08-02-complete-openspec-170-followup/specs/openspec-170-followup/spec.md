# openspec-170-followup Specification

## Purpose

Complete the remaining openspec CLI 1.7.0 follow-up items: inject archive hard-constraints into the CLI operationGuidance channel, modernize sdflow-done's archive step to use structured JSON output, and extend spec-review amendment write-back to cover all four artifacts bidirectionally.

## ADDED Requirements

### Requirement: archive-guidance-injection

The system SHALL inject archive operation guidance into `openspec/config.yaml` via `operations.archive.guidance` (string array) containing two hard constraints: (1) archive MUST use `openspec archive` CLI, manual `mv` is forbidden; (2) archive MUST reconcile `tasks.md` checkboxes first.

#### Scenario: archive guidance appears in CLI output

WHEN `openspec/config.yaml` has `operations.archive.guidance` configured
AND `openspec instructions archive --change X --json` is called
THEN the response SHALL contain `operationGuidance` array with the configured entries

#### Scenario: new projects receive guidance via template [spec-review-amendment]

WHEN a new project runs `sdflow-init` (init mode, generating config.yaml from template)
THEN the generated `openspec/config.yaml` SHALL contain the `operations.archive.guidance` entries from `config.template.yaml`

Note: `sdflow-init update` does not merge new config keys into existing `config.yaml` (by design — `init.py:handle_config` only touches `schema:` on update). Already-provisioned projects receive a "next steps" prompt to manually merge the `operations` section.

### Requirement: purpose-rule-in-specs

The system SHALL add a rule to `rules.specs` in both `openspec/config.yaml` and `config.template.yaml` requiring new capability delta specs to start with `## Purpose` (at least 50 characters).

#### Scenario: purpose rule present in config

WHEN `openspec/config.yaml` is read
THEN `rules.specs` SHALL contain a rule about `## Purpose` requirement for new capability delta specs

### Requirement: archive-json-warnings

The `sdflow-done` archive sub-agent prompt SHALL use `openspec archive {change_name} -y --json` and read the `warnings` array from JSON output instead of parsing `tail -30` text output.

#### Scenario: archive uses structured output

WHEN the archive sub-agent runs `openspec archive` with `--json` flag
THEN warnings SHALL be read from the JSON `warnings` array
AND text-based pattern matching on `tail` output SHALL NOT be used

### Requirement: fallback-ladder-slim [spec-review-amendment]

The `sdflow-done` archive fallback description SHALL accurately reflect CLI 1.7.0 behavior: REMOVED-requirement abort was fixed in the CLI itself (no longer triggers abort), and `sdflow-done/SKILL.md` never referenced this condition. The Chinese legacy format fallback path SHALL be preserved.

#### Scenario: fallback triggers documented accurately

WHEN reading `sdflow-done/SKILL.md` archive fallback section
THEN the documented trigger conditions SHALL only reference Chinese legacy format validation errors (the sole remaining trigger)
AND no changes to existing fallback text are required (REMOVED-abort was a CLI behavior fix, not a SKILL.md text change)

### Requirement: archive-recognizes-skipped

The `sdflow-done` archive sub-agent prompt SHALL recognize `skip_specs` changes (specs status = skipped) and treat the absence of delta as normal, not as an error requiring fallback.

#### Scenario: skipped change archives without fallback

WHEN archiving a change that declared `skip_specs: true`
AND specs artifact status is `skipped`
THEN the archive step SHALL proceed normally without entering the fallback path
AND the absence of delta specs SHALL NOT be treated as an anomaly

### Requirement: amendment-bidirectional-coherence

The `sdflow-spec-review` amendment write-back SHALL cover all four artifacts (proposal, design, specs, tasks), not only design/specs. The principle is: build order is a useful reading order, not a constraint on which artifacts may be revised.

#### Scenario: amendment can modify proposal

WHEN a spec-review finding has its root cause in proposal (e.g. Non-Goals boundary error)
THEN the amendment SHALL modify proposal.md with `[spec-review-amendment]` marker
AND SHALL NOT be limited to only design.md and specs/

#### Scenario: amendment does not call opsx:update

WHEN performing amendment write-back
THEN the system SHALL NOT invoke `/opsx:update` directly
AND SHALL instead apply the bidirectional principle manually to preserve `reviewed_sha` timing contract (ADR-7(b))
