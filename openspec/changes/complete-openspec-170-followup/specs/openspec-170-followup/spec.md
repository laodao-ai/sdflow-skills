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

#### Scenario: downstream projects receive guidance via template

WHEN `sdflow-init update` runs on a downstream project
THEN `openspec/workflow/config.template.yaml` SHALL contain the same `operations.archive.guidance` entries
AND the downstream `openspec/config.yaml` SHALL be updated accordingly

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

### Requirement: fallback-ladder-slim

The `sdflow-done` archive fallback description SHALL remove references to REMOVED-requirement abort as a trigger condition (fixed in CLI 1.7.0), while preserving the Chinese legacy format fallback path.

#### Scenario: fallback triggers documented accurately

WHEN reading `sdflow-done/SKILL.md` archive fallback section
THEN the documented trigger conditions SHALL NOT mention REMOVED-requirement abort
AND Chinese legacy format validation errors SHALL remain as a valid fallback trigger

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
