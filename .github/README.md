# 🛠️ `.github/` — Centralized Repository Infrastructure

<div align="center">

**Automation, validation, and review plumbing for [Dev Vault](https://github.com/shaonkabir8/dev-vault).**

</div>

---

## Purpose

Every workflow, linter setting, and template for this repository lives here, at the
repository root. Nothing in this directory is decorative: each check exists to catch a
specific class of defect that would otherwise reach `main` unnoticed.

The repository is documentation-only, so the highest-value checks are the ones that
guard writing quality — broken links, inconsistent formatting, committed secrets, and
malformed automation.

---

## Layout

```text
.github/
├── workflows/                    # CI automation
│   ├── markdown-lint.yml         # Markdown formatting standard
│   ├── link-check.yml            # Relative links and heading anchors
│   ├── config-lint.yml           # YAML validity (Dependabot, issue forms)
│   ├── workflow-lint.yml         # actionlint over workflow files
│   └── secret-scan.yml           # gitleaks over full Git history
├── linters/                      # Shared configuration consumed by the workflows
│   ├── .markdownlint.jsonc
│   ├── .yamllint.yml
│   ├── .gitleaks.toml
│   └── link-check-allowlist.txt   # Tracked, visible gaps
├── scripts/                      # Local tooling invoked by CI
│   └── check_links.py
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml
│   ├── resource_request.yml
│   └── config.yml
├── CODEOWNERS                    # Default review ownership
├── dependabot.yml                # Keeps pinned action versions current
└── PULL_REQUEST_TEMPLATE.md
```

---

## Workflows

| Workflow | Trigger | What it guarantees | Fails when |
|---|---|---|---|
| **Markdown Lint** | push to `main`, PR, manual | One formatting standard across all Markdown | A file violates `.markdownlint.jsonc` |
| **Link Check** | push to `main`, PR, manual | No dead relative link or stale `#anchor` | A target file is missing or an anchor has no heading |
| **Config Lint** | push to `main`, PR, manual | Every YAML file parses and is consistently indented | Invalid syntax, duplicate keys, bad indentation |
| **Workflow Lint** | push/PR touching `.github/` | The automation itself is valid | Invalid `uses:` ref, bad expression, bad `needs:` |
| **Secret Scan** | push, PR, weekly cron, manual | No credential in the working tree **or history** | gitleaks matches a rule and is not an allowlisted placeholder |

All workflows declare `permissions: contents: read`. None of them write to the
repository, publish artifacts, or hold a token beyond the checkout scope
(`persist-credentials: false`).

### Toolchain pinning

Every third-party dependency is pinned to an exact release, never a floating major tag:

| Tool | Version | Installed by |
|---|---|---|
| `actions/checkout` | `v7.0.1` | GitHub |
| `actions/setup-python` | `v7.1.0` | GitHub |
| `DavidAnson/markdownlint-cli2-action` | `v25.0.0` | GitHub |
| `gitleaks` | `8.30.1` | Release tarball + SHA-256 check |
| `actionlint` | `1.7.12` | Release tarball + SHA-256 check |
| `yamllint` | `1.35.1` | `pip install` |

The two tools installed from release tarballs are verified against the project's
published `checksums.txt` before execution, so a tampered artifact fails the job
instead of running. `dependabot.yml` opens a grouped weekly PR when a newer release
exists — pins stay exact, but they do not silently rot.

---

## Running the checks locally

The full suite is reproducible without GitHub. Each command mirrors its workflow step.

```bash
# Markdown formatting
npm install --global markdownlint-cli2@0.24.0
markdownlint-cli2 --config .github/linters/.markdownlint.jsonc "**/*.md"

# Relative links and anchors
python3 .github/scripts/check_links.py \
  --allowlist .github/linters/link-check-allowlist.txt \
  .

# YAML validity
python3 -m pip install --quiet "yamllint==1.35.1"
yamllint --config-file .github/linters/.yamllint.yml --strict \
  .github/workflows/*.yml .github/dependabot.yml \
  .github/ISSUE_TEMPLATE/*.yml

# Workflow semantics (optional locally; always run in CI)
actionlint -color=never -verbose .github/workflows/*.yml

# Secret scan (full history)
gitleaks git . --config .github/linters/.gitleaks.toml --redact --verbose
```

---

## `check_links.py`

The link checker is custom rather than borrowed because the available off-the-shelf
options either require network access to remote hosts (non-deterministic in CI) or do
not validate heading anchors.

| Behaviour | Detail |
|---|---|
| **Validates** | Relative file links, image paths, `#fragment` anchors that match a real heading |
| **Ignores** | `http(s)://`, `mailto:`, `data:`, and links inside code fences or inline code |
| **Slug rules** | Mirrors GitHub's algorithm: lowercase, punctuation stripped, spaces → `-`, duplicates suffixed `-1`, `-2` |
| **Failure output** | Human-readable locally; `::error file=…,line=…` annotations on Actions |
| **Exit codes** | `0` all resolved, `1` at least one broken target |

```bash
# Fail on broken links (CI behaviour)
python3 .github/scripts/check_links.py .

# Add a tracked exception to .github/linters/link-check-allowlist.txt
# Format: <source file>|<link target as written>
```

Allowlisted targets still print as warnings every run. They are **known gaps made
visible**, never silenced — the difference matters, because a silently ignored broken
link is indistinguishable from a working one six months later.

---

## Issue forms

Both forms are YAML-based, so their fields are validated in the UI before submission
and arrive structured rather than as free text.

| Form | Use it for | Enforces |
|---|---|---|
| `bug_report.yml` | A script, snippet, config, or doc that behaves incorrectly | Exact error output, reproduction steps, secret removal |
| `resource_request.yml` | A new reusable resource or an improvement | Category, problem statement, and a check that no duplicate exists |
| `config.yml` | Redirects | Documentation link; private security reporting instead of a public issue |

Blank issues are disabled on purpose: an unstructured report costs more to triage than
it saves to write.

---

## Governance notes

- **`CODEOWNERS`** assigns `@shaonkabir8` to the repository and to each resource
  directory, so every path has a named reviewer even before those directories exist.
- **`dependabot.yml`** groups all action updates into one weekly PR to keep review
  load near zero.
- **Change policy** — workflow changes must update this README in the same commit.
  A workflow whose documented behaviour and real behaviour diverge is a latent
  failure, not documentation debt.

---

<div align="center">

[⬅️ Repository home](../README.md) · [📚 Full documentation](../docs/README.md) · [বাংলা](../docs/README.bn.md)

*Store less. Reuse more. Verify everything.*

</div>
