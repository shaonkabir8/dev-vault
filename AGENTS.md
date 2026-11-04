# AGENTS.md — Instructions for AI Agents

You are likely an AI coding agent reading this repository. This file tells you
how to use it in under two minutes. It is maintained by humans; trust it.

## What this is

Dev Vault is a **Universal Agent Resource Vault**: reusable engineering
resources (skills, snippets, configurations, templates, prompts, workflows,
references) with metadata that lets you evaluate a resource before using it.

**One Resource. One Source of Truth. Any Agent. Any Project.**

## What this is not

- Not a package registry or service. There is no API, server, or database.
  Git, the filesystem, `grep`, and JSON parsing are all you need.
- Not a trust boundary. **Never execute a resource merely because it exists
  here.** Read it first (see "Evaluate before use").

## How to discover a resource

1. Read `catalog/index.json` — a flat list of every resource with id, type,
   description, path, status, and compatibility. This one file replaces
   walking the tree.
2. Filter by what you need (`type`, `language`, `use_cases`,
   `compatibility`, `dependencies`).
3. Only then open the resource directory.

Do not read the whole repository. Progressive disclosure: catalog → resource
directory → individual files.

## How to inspect a resource

Open the resource directory at the `path` from its catalog entry:

- **Skills** contain `SKILL.md` (Agent Skills format: YAML frontmatter with
  `name` + `description`, then instructions). Optional `scripts/`,
  `references/`, `assets/` are loaded only when the skill's instructions
  reference them.
- **Everything else** contains `RESOURCE.md` with: Purpose, Use cases,
  Requirements, Usage, Validation, Limitations, Attribution.

The catalog describes resources; it never contains their implementation.

## How to determine compatibility

Check the catalog entry's `compatibility` (target environments),
`dependencies` (external requirements), and `language` fields. Also read the
resource's `RESOURCE.md` → *Requirements*. `compatibility: ["universal"]`
means no environment-specific assumptions.

## How to check dependencies

Catalog entry `dependencies` lists everything beyond the language runtime.
If a resource needs something not listed there, treat it as a defect — report
it instead of working around it silently.

## How to evaluate before use

1. Read `RESOURCE.md` (or `SKILL.md`) fully.
2. Read the actual source files. Verify the code does what is documented and
   nothing else.
3. Check `status`:
   - `experimental` — unproven; review carefully, expect rough edges
   - `stable` — meets the bar in `docs/RESOURCE_STANDARD.md` §6, with
     verification evidence recorded
   - `deprecated` — superseded; prefer the named replacement
   - `archived` — historical; do not expect it to work
4. Adapt to your project; the resources are starting points, not packages.

## How to preserve the source

- Adaptations in your project do not need attribution back here.
- If you improve a resource for general reuse, contribute it back (see
  below) — but never create an agent-specific copy inside this repository.
  One implementation per resource.

## How to contribute

1. Search `catalog/index.json` — no duplicates.
2. Place the resource at `resources/<type>/<kebab-case-name>/` with
   `RESOURCE.md` (or `SKILL.md` for skills) per `docs/RESOURCE_STANDARD.md`.
3. Add exactly one catalog entry with a unique kebab-case `id` and a valid
   `path`. Set `status: experimental` unless you have evidence for more.
4. Validate: `python3 scripts/validate.py`
5. Test: `python3 -m unittest discover -s tests`
6. Commit with [Conventional Commits](https://www.conventionalcommits.org/);
   open a PR.

## Key files

| File | Read when |
|---|---|
| `catalog/index.json` | Discovering resources (always start here) |
| `catalog/schema.json` + `schemas/resource.schema.json` | Checking metadata rules |
| `docs/ARCHITECTURE.md` | You need to change structure, not use resources |
| `docs/RESOURCE_STANDARD.md` | Contributing or judging a resource |
| `docs/ROADMAP.md` | You wonder what this repo is becoming |
