# Security Policy

## Reporting a vulnerability

Do **not** open a public issue for security problems.

Report privately via [GitHub security advisories](https://github.com/shaonkabir8/dev-vault/security/advisories/new)
for this repository. Include:

- The affected file or resource (`path` from `catalog/index.json` if applicable)
- A description of the issue and how it could be exploited
- Any reproduction steps or proof of concept

You will receive a response as soon as possible. Please allow time for a fix
before public disclosure.

## Scope

This repository distributes reusable engineering resources — snippets,
configurations, templates, prompts, skills, workflows, and references. Report:

- Hardcoded credentials, tokens, or secrets in any resource
- Destructive or hidden execution behavior in scripts or commands
- Configuration templates that encourage unsafe defaults
- Resources that misrepresent their validation or compatibility status

## Rules for contributors

Every resource in this vault must follow the security standards in
[docs/RESOURCE_STANDARD.md](./docs/RESOURCE_STANDARD.md). In particular:

- No real secrets in any file — use `*.example` templates with placeholders
- No unexplained destructive commands; destructive actions require a dry-run option
- No hidden execution behavior — a resource must do only what its documentation says
- Environment-specific assumptions and required permissions must be documented

A resource must never be executed blindly simply because it exists in this
repository. Review it before use.

## Tooling

The repository runs `gitleaks` over the full Git history on every push, pull
request, and weekly (see `.github/workflows/secret-scan.yml`). Known false
positives are documented in `.github/linters/.gitleaks.toml` — never weaken a
default rule to silence a finding.
