# Contributing to Dev Vault

Thank you for contributing. This vault stays useful through small, verified,
well-documented resources — not volume.

Read [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for how the repository is
organized and [docs/RESOURCE_STANDARD.md](./docs/RESOURCE_STANDARD.md) for the
standard every resource must meet. AI agents should also read
[AGENTS.md](./AGENTS.md).

## Before you add a resource

1. **Search first.** Check `catalog/index.json` and the `resources/` tree for
   an existing resource that solves the problem. Do not add a duplicate.
2. **Pick the right type.** A code snippet is not automatically a skill; a
   configuration is not automatically a skill. Only package something as an
   Agent Skill when it genuinely fits that format.
3. **Keep it minimal.** Solve one problem well. No speculative abstractions.

## Required structure

Every resource lives in `resources/<type>/<resource-name>/` and contains:

- `RESOURCE.md` — required for all resources (see the template in
  [docs/RESOURCE_STANDARD.md](./docs/RESOURCE_STANDARD.md)); for skills,
  `SKILL.md` per the [Agent Skills specification](https://github.com/agentskills/agentskills)
  may replace it, but resource metadata is still required
- The resource files themselves

Every resource must also have an entry in `catalog/index.json` with a unique
`id` and a valid `path`. The catalog describes resources; it never duplicates
their implementation.

## Validation

Run before opening a pull request:

```bash
# Catalog and structure validation (Python 3 stdlib only)
python3 scripts/validate.py

# Unit tests for the validator
python3 -m unittest discover -s tests -v

# Markdown lint and link check (same as CI)
npx markdownlint-cli2 --config .github/linters/.markdownlint.jsonc "**/*.md"
python3 .github/scripts/check_links.py --allowlist .github/linters/link-check-allowlist.txt .
```

CI runs the same checks plus YAML lint, workflow lint, and a full-history
secret scan.

## Workflow

1. Fork / branch using `feat/`, `fix/`, `docs/`, `chore/` prefixes
2. Make one logically isolated change per pull request
3. Validate locally — paste real output in the PR template, not claims
4. Commit with [Conventional Commits](https://www.conventionalcommits.org/)
5. Open a pull request; do not bypass CI

## Security

Never commit credentials or personal data. See
[SECURITY.md](./SECURITY.md) for how to report vulnerabilities privately.
