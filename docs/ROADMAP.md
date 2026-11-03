# Dev Vault Roadmap

> Deliberately minimal. Entries are added only when the foundation supports
> them and real need exists. Statuses: done / next / candidate / future.

## Phase 0 — Foundation ✅ done

Established 2026-11:

- Repository audit and architectural decisions ([ARCHITECTURE.md](./ARCHITECTURE.md))
- Resource standard and lifecycle ([RESOURCE_STANDARD.md](./RESOURCE_STANDARD.md))
- Directory skeleton: `resources/`, `catalog/`, `schemas/`, `scripts/`,
  `tests/`, `integrations/`
- `AGENTS.md` agent operating instructions
- Machine-readable catalog (`catalog/index.json` + `catalog/schema.json`)
- Resource metadata schema (`schemas/resource.schema.json`)
- Validation tooling (`scripts/validate.py`, `scripts/catalog.py`,
  Python stdlib only) with unit tests
- Missing governance files committed: `LICENSE`, `CONTRIBUTING.md`,
  `SECURITY.md`
- GitHub governance aligned with the new structure

## Phase 1 — First real resources ▶ next

The foundation is unproven until it holds real content.

- Add the first 3–5 resources across at least three different types,
  following [RESOURCE_STANDARD.md](./RESOURCE_STANDARD.md)
- Keep nearly all of them `experimental` until verification evidence exists
- Let real resources — not speculation — drive schema refinements
- First skill following the Agent Skills spec, validated with
  `skills-ref validate`

## Phase 2 — Validation hardening ○ candidate

Only if Phase 1 shows the need:

- CI workflow running `scripts/validate.py` on every PR
- Catalog `path` → `type` consistency checks tightened as real edge cases appear
- Optional duplicate-detection helper (description/name similarity) if
  duplication becomes an actual problem

## Phase 3 — Thin agent integrations ○ candidate

- `integrations/<agent>/` adapters for agents the owner actually uses, each a
  short instruction file pointing at the shared catalog — never resource copies
- Generic adapter pattern documented in `integrations/generic/`

## Future — explicitly not planned now ◌ future

Recorded so they are not re-proposed without new evidence; see
[ARCHITECTURE.md §10](./ARCHITECTURE.md):

- MCP server, hosted API, database, web dashboard, authentication
- Complex search engine or automatic installation platform
- Large-scale migration tooling

## Scope discipline

A phase starts only when its predecessor's deliverables are real and verified.
Features are added on evidence of need, not speculation.
