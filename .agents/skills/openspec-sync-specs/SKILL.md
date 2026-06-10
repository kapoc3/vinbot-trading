---
name: openspec-sync-specs
description: Sync delta specs from a change to main specs. Use when user wants to update main specs with changes without archiving the change.
---

# OpenSpec Sync Specs

Sync delta specs from a change to main specs. Agent-driven operation - read delta specs and directly edit main specs.

## When to Use This Skill

- Updating main specs with new requirements
- Merging delta specs into main
- Before archiving a change

## Prerequisites

Requires OpenSpec CLI and change with delta specs in `openspec/changes/<name>/specs/`.

## Steps

### 1. Identify Change

**If user specifies change name**, use it.

**If not**, prompt:
```bash
openspec list --json
```

Show changes with delta specs (under `specs/` directory).

### 2. Find Delta Specs

Look for delta spec files:
```
openspec/changes/<name>/specs/<capability>/spec.md
```

Each delta spec contains:
- `## ADDED Requirements` - New requirements
- `## MODIFIED Requirements` - Changes to existing
- `## REMOVED Requirements` - Requirements to remove
- `## RENAMED Requirements` - FROM:/TO: format

If no delta specs found, inform user and stop.

### 3. Apply Changes to Main Specs

For each capability with delta spec:

**a. Read delta spec** to understand changes

**b. Read main spec** at `openspec/specs/<capability>/spec.md` (may not exist)

**c. Apply changes intelligently:**

- **ADDED**: If requirement doesn't exist → add it. If exists → update to match.

- **MODIFIED**: Find in main spec, apply changes (add scenarios, modify existing). Preserve content not mentioned.

- **REMOVED**: Remove entire requirement block from main spec.

- **RENAMED**: Find FROM requirement, rename to TO.

**d. Create new main spec** if capability doesn't exist:
- Create `openspec/specs/<capability>/spec.md`
- Add Purpose section
- Add Requirements section with ADDED requirements

### 4. Show Summary

```
## Specs Synced: <change-name>

Updated main specs:

**<capability-1>**:
- Added requirement: "New Feature"
- Modified requirement: "Existing Feature" (added 1 scenario)

**<capability-2>**:
- Created new spec file
- Added requirement: "Another Feature"

Main specs updated. Change remains active.
```

## Delta Spec Format

```markdown
## ADDED Requirements

### Requirement: New Feature
The system SHALL do something new.

#### Scenario: Basic case
- **WHEN** user does X
- **THEN** system does Y

## MODIFIED Requirements

### Requirement: Existing Feature
#### Scenario: New scenario to add
- **WHEN** user does A
- **THEN** system does B

## REMOVED Requirements

### Requirement: Deprecated Feature

## RENAMED Requirements

- FROM: `### Requirement: Old Name`
- TO: `### Requirement: New Name`
```

## Key Principle: Intelligent Merging

- Partial updates allowed - to add a scenario, just include that scenario
- Delta represents *intent*, not wholesale replacement
- Use judgment to merge sensibly

## Guardrails

- Read both delta and main specs before changes
- Preserve existing content not in delta
- If unclear, ask for clarification
- Show changes as you go
- Operation should be idempotent