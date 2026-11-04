# Dev Vault Architecture

> Status: foundational · Established: 2026-11 · Decisions here are binding for
> everything under `resources/`, `catalog/`, and `integrations/`.

## 1. Purpose and boundaries

Dev Vault is a **Universal Agent Resource Vault**: a version-controlled
collection of reusable engineering resources — code snippets, configurations,
templates, prompts, skills, workflows, and technical references — made
discoverable, understandable, adaptable, and reusable by AI coding agents,
autonomous agents, developers, and vibe coders.

**The principle:** One Resource. One Source of Truth. Any Agent. Any Project.

Dev Vault **is**:

- A plain Git repository, readable with ordinary filesystem access
- A machine-readable catalog of resources (`catalog/index.json`)
- A set of standards that make resources safe to evaluate before use

Dev Vault **is not**:

- A package registry, hosted API, database, or web service
- An MCP server or agent framework (explicitly out of scope for this phase)
- A dump of unverified snippets — every resource carries metadata and a
  lifecycle status
- A place where agent-specific copies of resources are kept (see §6)

## 2. Directory structure

```text
dev-vault/
├── README.md            # Human-facing landing page
├── AGENTS.md            # Agent-facing operating instructions
├── LICENSE              # MIT; applies to the whole vault unless stated
├── CONTRIBUTING.md      # Contribution workflow
├── SECURITY.md          # Vulnerability reporting
├── catalog/
│   ├── index.json       # Machine-readable resource catalog
│   └── schema.json      # Validation contract for catalog entries
├── resources/           # Single source of truth for all resources
│   ├── skills/          # Agent Skills (SKILL.md format)
│   ├── snippets/        # Small reusable code
│   ├── configurations/  # Configuration templates (*.example)
│   ├── templates/       # Project and document scaffolds
│   ├── prompts/         # AI prompts and instruction templates
│   ├── workflows/       # Multi-step processes and runbooks
│   └── references/      # Engineering notes and technical references
├── integrations/        # Thin agent-specific adapters (instructions only)
│   └── generic/
├── schemas/
│   └── resource.schema.json   # Shared resource metadata contract
├── scripts/             # Lightweight maintenance/validation utilities
├── tests/               # Tests for repository tooling and structure
├── docs/                # Architecture, standards, roadmap
└── .github/             # CI, linting, governance (pre-existing)
```

Rules:

- `resources/` is the single source of truth. The catalog describes it; it
  never duplicates it.
- No empty directories exist merely to complete the tree. A directory holds a
  `.gitkeep` only while it has no resources and is expected to receive them.
- `integrations/` contains only adapters, instruction files, or pointers. If an
  integration needs more than that, it is a design error.

## 3. Resource taxonomy

| Type | Directory | Native format |
|---|---|---|
| Skill | `resources/skills/` | Agent Skills (`SKILL.md`, per the pinned spec — see §6) |
| Snippet | `resources/snippets/` | `RESOURCE.md` + source file(s) |
| Configuration | `resources/configurations/` | `RESOURCE.md` + `*.example` files |
| Template | `resources/templates/` | `RESOURCE.md` + scaffold |
| Prompt | `resources/prompts/` | `RESOURCE.md` + prompt file |
| Workflow | `resources/workflows/` | `RESOURCE.md` + steps |
| Reference | `resources/references/` | `RESOURCE.md` (or self-documenting) |

Classification rule: choose the type by **how the resource is consumed**, not
by file extension. A shell script that orchestrates a multi-step process is a
workflow; a single-purpose function is a snippet. Something executable that
carries its own agent-facing instructions and fits the Agent Skills format is a
skill. Nothing is forced into the skill format.

## 4. Resource identity, naming, and metadata

- **Directory name:** kebab-case (`kebab-case`, lowercase, hyphens), matching
  the skill `name` field for skills per the spec.
- **Resource id:** stable, unique, kebab-case string recorded in the catalog.
  Once published, an id is never reused for a different resource.
- **Metadata contract:** every resource carries a `RESOURCE.md` (or, for
  skills, `SKILL.md` frontmatter) plus a catalog entry. The full contract is
  defined in [RESOURCE_STANDARD.md](./RESOURCE_STANDARD.md) and validated by
  `schemas/resource.schema.json` / `catalog/schema.json`.
- **Version:** resource-level semantic versions live in the catalog entry;
  the Git history is the real changelog.

## 5. Discovery model

An unfamiliar agent must be able to discover a resource without reading the
repository. Three layers, in order of cost:

1. **`AGENTS.md`** — tells an agent what the vault is and where to look first.
2. **`catalog/index.json`** — a flat, validated JSON array of resource
   summaries (id, name, type, path, description, status, compatibility).
   An agent scans one file instead of walking the tree.
3. **Per-resource files** — loaded only when a resource is a candidate.

No custom API, server, or search index is involved. Git, the filesystem, JSON
parsing, and `grep` are sufficient. Agents that prefer richer tooling can build
it on top of the catalog; the vault itself never depends on one.

## 6. Agent interoperability strategy

- **Skills** follow the open [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)
  (spec file pinned at commit `217be548739f21d6008915c29aefe320ea1a90af`,
  2026-08-04): required `name`/`description` frontmatter, name matching the
  directory, optional `scripts/`, `references/`, `assets/` used only when
  needed, progressive disclosure respected.
- **Non-skill resources** follow the `RESOURCE.md` convention (§7 of
  [RESOURCE_STANDARD.md](./RESOURCE_STANDARD.md)).
- **Agent-specific integrations** live in `integrations/<agent>/` as *thin
  adapters*: instruction files that tell an agent how to consume the shared
  catalog and resource tree. They never contain copies of resources. This keeps
  one implementation per resource while letting each agent integrate natively.

## 7. Validation strategy

`scripts/validate.py` (Python 3 standard library only) checks: JSON validity,
catalog conformance to its schema, unique ids, path existence, required
metadata, lifecycle status, documentation presence, and basic structure.
`tests/` verifies the validator and repository integrity. CI runs the same
checks plus the pre-existing Markdown, link, YAML, workflow, and secret scans.

Validation proves **structure and metadata integrity**, not that a resource's
code is correct for your environment. Agents must still review a resource
before executing it. Nothing in this vault is auto-executed.

## 8. Resource lifecycle

| Status | Meaning |
|---|---|
| `experimental` | New or unproven. Use with review. Default for new resources. |
| `stable` | Meets the stability bar in [RESOURCE_STANDARD.md](./RESOURCE_STANDARD.md) with documented verification evidence. |
| `deprecated` | Superseded or no longer recommended; a replacement may be named. |
| `archived` | Retained for history only; not expected to work. |

Transitions are deliberate, recorded in Git history, and reflected in the
catalog in the same change.

## 9. Licensing and attribution

The vault is MIT-licensed; `license: "inherit"` in a catalog entry means the
resource is covered by the repository LICENSE. Third-party resources must state
their license explicitly and preserve original attribution. The owner's Git
authorship is part of the record and is never rewritten.

## 10. Decisions rejected

Recorded so they are not re-proposed without new evidence:

- **MCP server / hosted API** — violates "zero unnecessary dependencies";
  the catalog + filesystem already satisfies discovery.
- **Per-agent resource copies** — violates one-source-of-truth; thin adapters
  in `integrations/` cover the need.
- **Git submodules for resources** — coupling without benefit at current scale.
- **A build step to generate the catalog** — hand-maintained with schema
  validation is simpler and reviewable in PRs at this size; revisit only if the
  catalog exceeds ~100 entries or drift becomes a real problem.
