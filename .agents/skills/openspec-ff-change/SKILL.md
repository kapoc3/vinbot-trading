---
name: openspec-ff-change
description: Fast-forward through OpenSpec artifact creation. Use when the user wants to quickly create all artifacts needed for implementation.
---

# OpenSpec Fast-Forward Change

Create all artifacts needed for a change in one go using OpenSpec CLI.

## When to Use This Skill

- Starting a new feature or fix that needs specs
- Creating proposal, design, tasks, and specs quickly
- Fast-forwarding through the full artifact creation workflow

## Prerequisites

Requires OpenSpec CLI installed:
```bash
npm install -g @openspec/cli
```

## Steps

### 1. Identify or Create Change

**If user provides change name:**
```bash
openspec new change "<name>"
```

This creates scaffolded change at `openspec/changes/<name>/`.

**If no clear input provided**, ask user what they want to build and derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

### 2. Get Artifact Build Order

```bash
openspec status --change "<name>" --json
```

Parse JSON to get:
- `applyRequires`: artifact IDs needed before implementation
- `artifacts`: list of all artifacts with status and dependencies

### 3. Create Artifacts in Sequence

Use the Todo tool to track progress.

Loop through artifacts in dependency order:

**For each artifact that is `ready`:**
```bash
openspec instructions <artifact-id> --change "<name>" --json
```

The JSON response includes:
- `context`: project constraints
- `rules`: artifact-specific constraints
- `template`: structure for output file
- `instruction`: schema-specific guidance
- `outputPath`: where to write
- `dependencies`: completed artifacts to read

**Read dependency files** for context, then create the artifact.

### 4. Continue Until Apply-Ready

Re-run status after each artifact:
```bash
openspec status --change "<name>" --json
```

Stop when all `applyRequires` artifacts are `status: "done"`.

### 5. Show Final Status

```bash
openspec status --change "<name>"
```

## Output Summary

After completing, provide:
- Change name and location
- List of artifacts created
- Status: "All artifacts created! Ready for implementation."
- Prompt: "Run `/opsx:apply` or ask me to implement to start working on the tasks."

## Important Notes

- Follow the `instruction` field from `openspec instructions`
- Read dependency artifacts before creating new ones
- Use `template` as the structure
- **DO NOT** copy `<context>`, `<rules>`, `<project_context>` blocks into artifacts - these are constraints for you, not content

## Guardrails

- Create ALL artifacts needed (as defined by schema's `apply.requires`)
- Always read dependency artifacts first
- If context is unclear, ask user - but prefer reasonable decisions
- If change already exists, suggest continuing that one
- Verify each artifact file exists after writing