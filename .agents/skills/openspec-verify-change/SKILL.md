---
name: openspec-verify-change
description: Verify implementation matches change artifacts. Use when user wants to validate implementation completeness, correctness, and coherence before archiving.
---

# OpenSpec Verify Change

Verify that implementation matches change artifacts (specs, tasks, design).

## When to Use This Skill

- Before archiving a change
- Validating implementation completeness
- Checking spec coverage
- Ensuring design adherence

## Prerequisites

Requires OpenSpec CLI:
```bash
openspec --version
```

## Steps

### 1. Identify Change

**If user specifies change name**, use it directly.

**If not specified**, prompt for selection:
```bash
openspec list --json
```

Show changes with implementation tasks. Mark incomplete ones as "(In Progress)".

### 2. Check Schema and Artifacts

```bash
openspec status --change "<name>" --json
```

Get:
- `schemaName`: workflow used (e.g., "spec-driven")
- Which artifacts exist

```bash
openspec instructions apply --change "<name>" --json
```

Get change directory and context files. Read all available artifacts.

### 3. Initialize Verification Report

Three dimensions:
- **Completeness**: task and spec coverage
- **Correctness**: requirement and scenario coverage
- **Coherence**: design adherence and pattern consistency

Each dimension: CRITICAL, WARNING, or SUGGESTION issues.

### 4. Verify Completeness

**Task Completion:**
- Read tasks.md
- Parse checkboxes: `- [ ]` (incomplete) vs `- [x]` (complete)
- Count complete vs total
- If incomplete: add CRITICAL issue

**Spec Coverage:**
- Find delta specs in `openspec/changes/<name>/specs/`
- Extract requirements ("### Requirement:")
- Search codebase for implementation evidence
- If unimplemented: add CRITICAL issue

### 5. Verify Correctness

**Requirement Implementation:**
- For each requirement, search for implementation
- Note file paths and line ranges
- If divergence: add WARNING with recommendation

**Scenario Coverage:**
- For each scenario ("#### Scenario:"), check if handled in code
- Check for tests covering scenario
- If uncovered: add WARNING

### 6. Verify Coherence

**Design Adherence:**
- Read design.md
- Extract key decisions
- Verify implementation follows decisions
- If contradiction: add WARNING

**Pattern Consistency:**
- Review code for project patterns
- Check file naming, structure, style
- If deviations: add SUGGESTION

### 7. Generate Report

**Summary Scorecard:**
```
## Verification Report: <change-name>

### Summary
| Dimension    | Status           |
|--------------|------------------|
| Completeness | X/Y tasks, N reqs|
| Correctness  | M/N reqs covered |
| Coherence    | Followed/Issues  |
```

**Issues by Priority:**

1. **CRITICAL**: Incomplete tasks, missing implementations
2. **WARNING**: Spec/design divergences, missing scenarios
3. **SUGGESTION**: Pattern inconsistencies

**Final Assessment:**
- If CRITICAL: "X critical issue(s) found. Fix before archiving."
- If only warnings: "Ready for archive (with noted improvements)."
- If all clear: "All checks passed. Ready for archive."

## Verification Heuristics

- **Completeness**: Focus on checklist items
- **Correctness**: Use keyword search, file analysis - don't require perfect certainty
- **Coherence**: Look for glaring inconsistencies
- When uncertain: SUGGESTION > WARNING > CRITICAL
- Every issue needs specific recommendation with file:line reference

## Graceful Degradation

- Only tasks.md → verify task completion only
- tasks + specs → verify completeness and correctness
- Full artifacts → verify all three dimensions
- Always note which checks were skipped and why

## Output Format

Use markdown with:
- Table for summary scorecard
- Grouped lists for issues
- Code references: `file.ts:123`
- Specific, actionable recommendations
- No vague suggestions