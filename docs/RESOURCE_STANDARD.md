# Dev Vault Resource Standard

> This document defines the contract every resource must satisfy. It is
> enforced by `scripts/validate.py` and CI.

## 1. The standard in one line

A resource must let an unfamiliar agent **discover, understand, evaluate,
adapt, validate, and reuse** it without asking a human anything the files
should have answered.

## 2. Resource types

Exactly seven, one directory each under `resources/`:

`skills` · `snippets` · `configurations` · `templates` · `prompts` ·
`workflows` · `references`

Classification is by consumption, not file extension. When two types fit,
choose the simpler one. Do not force a snippet into the Agent Skills format.

## 3. Directory and naming rules

- Path: `resources/<type>/<resource-name>/`
- `resource-name` and resource `id`: kebab-case (`[a-z0-9-]+`, no leading or
  trailing hyphen, no consecutive hyphens)
- One resource per directory; id is unique across the vault and never reused

## 4. Documentation contract

### 4a. Skills

Follow the [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)
(pinned at commit `217be548739f21d6008915c29aefe320ea1a90af`):

- `SKILL.md` at the skill directory root, YAML frontmatter first
- `name`: required, 1–64 chars, lowercase letters/digits/hyphens, no leading
  or trailing or consecutive hyphens, **must match the directory name**
- `description`: required, 1–1024 chars, states what the skill does **and
  when to use it**, with keywords an agent can match against
- Optional fields (`license`, `compatibility`, `metadata`, `allowed-tools`)
  only when they add information
- Optional `scripts/`, `references/`, `assets/` only when actually used
- `SKILL.md` body under 500 lines; push detail into `references/`

### 4b. Everything else — `RESOURCE.md`

Every non-skill resource directory contains a `RESOURCE.md` with these
sections. Omit a section only when it is genuinely empty, never by accident.

```markdown
# <Resource Name>

## Purpose
What problem this solves, in two sentences or fewer.

## Use cases
When to reach for this — and when not to.

## Requirements
Runtime, tools, versions, permissions, environment assumptions.

## Usage
How to inspect, adapt, and run it. Include a minimal working example.

## Validation
What was actually tested, how, and on what date. No evidence, no claim.

## Limitations
Known constraints, edge cases, unsupported environments.

## Attribution and license
Original author/source if adapted; license (`inherit` for vault MIT
unless stated otherwise).
```

Do not duplicate the catalog's metadata in prose; the catalog is the
machine-readable projection of this file, not the other way around.

## 5. Catalog entry contract

Every resource has exactly one entry in `catalog/index.json`, validated by
`catalog/schema.json` (full field table there). Shape:

```json
{
  "id": "example-resource",
  "name": "Example Resource",
  "type": "snippet",
  "description": "One-sentence summary of what it does and when to use it.",
  "path": "resources/snippets/example-resource/",
  "language": ["python"],
  "technologies": [],
  "use_cases": [],
  "compatibility": ["universal"],
  "dependencies": [],
  "license": "inherit",
  "status": "experimental",
  "version": "0.1.0"
}
```

Rules: `path` must exist and match `resources/<type>/<name>/`; `id` must be
unique and kebab-case; `status` must be a valid lifecycle value; the catalog
describes resources and never embeds their implementation.

## 6. Lifecycle and the stability bar

Lifecycle: `experimental` → `stable` → (`deprecated` → `archived`).

A resource may be marked `stable` only after all of the following are true
and recorded under "Validation":

1. **Correctness** — does what the documentation claims on realistic inputs
2. **Security** — reviewed against §7; no secrets, no destructive surprises
3. **Portability** — no unexplained hard-coded paths, hosts, or identities
4. **Documentation** — complete per §4, with a working example
5. **Dependency transparency** — every dependency listed in the catalog entry
6. **Maintainability** — readable; a stranger could modify it safely
7. **Compatibility** — supported environments stated, not implied
8. **Verification evidence** — commands and results someone can re-run

Deprecation names its replacement when one exists. Archived resources state
why they are retired.

## 7. Security rules (non-negotiable)

- No hardcoded credentials, tokens, or personal data — ever
- Configuration templates use `*.example` files with placeholder values
- Destructive commands are explained and, in scripts, gated behind an explicit
  flag with a dry-run default where feasible
- No hidden execution behavior: a resource does only what its documentation says
- External dependencies are named and justified; none are fetched blind
- Environment-specific assumptions and required permissions are documented
- License and attribution are preserved when adapting third-party work

**A resource must never be executed merely because it exists in dev-vault.**
Review first; the vault optimizes for evaluation speed, not blind trust.

## 8. Adding a resource (checklist)

- [ ] Searched `catalog/index.json` — no existing resource covers this
- [ ] Type chosen by consumption; directory created under `resources/<type>/`
- [ ] `RESOURCE.md` or `SKILL.md` complete per §4
- [ ] Catalog entry added, schema-valid, unique id
- [ ] `python3 scripts/validate.py` passes
- [ ] `python3 -m unittest discover -s tests` passes
- [ ] Status set honestly (almost always `experimental`)
- [ ] No secrets, no unrelated changes in the commit
