---
name: security-lab-documenter
description: Document the insecure design choices, teaching goals, and detection implications of the local fintech software security lab. Use when Codex needs to annotate vulnerabilities, explain why a weak pattern exists, map user actions to logs, or keep the lab safely scoped to localhost for educational use.
---

# Security Lab Documenter

## Workflow

1. Read `docs/arquitectura-inicial.md` for the current system scope.
2. Read `references/lab-guidelines.md` before documenting a weakness or adding a new scenario.
3. For each insecure feature, record what it demonstrates, where it exists, and what traces it should leave.
4. Keep documentation concise and close to the code or SQL it describes.
5. Avoid exploit playbooks. Focus on design rationale, observable effects, and defensive learning goals.

## Documentation Rules

- State that the lab is for localhost and educational use.
- Name the weak practice directly instead of using vague wording.
- Link the weak practice to concrete files, tables, or flows.
- Describe which user actions or log patterns can later be used for detection exercises.
- Separate business behavior from security-observation behavior.

## Good Outputs

Useful outputs for this skill include:

- short module notes in `docs/`
- comments near intentionally weak code paths
- log-field mapping notes for later analytics
- phase notes describing which scenarios have already been introduced

## References

- Read `references/lab-guidelines.md` for the documentation template.
- Read `docs/arquitectura-inicial.md` for the current module inventory.

