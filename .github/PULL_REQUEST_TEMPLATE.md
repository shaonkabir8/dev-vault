# Pull Request

## Purpose

<!-- What changed, and why is this change needed? One or two sentences. -->

## Scope

<!-- Which directories or resources does this touch? -->

- [ ] `snippets/`
- [ ] `scripts/`
- [ ] `configs/`
- [ ] `docs/`
- [ ] `patterns/`
- [ ] `prompts/`
- [ ] `commands/`
- [ ] `templates/`
- [ ] `.github/` (automation and configuration)

## Change type

- [ ] `feat` — new resource or capability
- [ ] `fix` — bug or incorrect behavior
- [ ] `docs` — documentation only
- [ ] `refactor` — implementation improvement, same behavior
- [ ] `test` — tests added or updated
- [ ] `chore` — maintenance and housekeeping
- [ ] `security` — security-related improvement

## Verification

<!-- Evidence, not claims. Paste command output or name the check you ran. -->

- [ ] Relevant checks were run locally and are reproduced below
- [ ] Markdown lint passes (`Markdown Lint` workflow)
- [ ] Internal link and anchor check passes (`Link Check` workflow)
- [ ] Secret scan passes (`Secret Scan` workflow)

```text
# paste check output here
```

## Review checklist

- [ ] PR title follows Conventional Commits (`type(scope): description`)
- [ ] Purpose and impact are described above
- [ ] Unrelated changes are excluded from this PR
- [ ] No secrets, credentials, personal data, or proprietary content
- [ ] New resources have a documented purpose, usage, and known limitations
- [ ] No duplicate implementation of an existing resource
