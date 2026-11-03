# Generic Integration Adapter

This directory documents the **only** allowed shape of an agent integration in
dev-vault. Every integration must stay a *thin adapter*: it tells a specific
agent how to consume the shared catalog and resource tree. It never contains
copies of resources — one resource, one source of truth.

## What belongs in `integrations/<agent>/`

- A short instruction file (e.g. `INSTRUCTIONS.md`) explaining, in the target
  agent's native idiom, how to:
  1. Read `catalog/index.json` to discover resources
  2. Open a resource's `RESOURCE.md` or `SKILL.md` before using it
  3. Respect lifecycle `status` and `dependencies`
- Optionally, a configuration file in the agent's native format that points at
  this repository (paths only — no resource content)

## What never belongs here

- Copies or forks of any resource, however small
- Duplicated metadata that already lives in the catalog
- Anything that requires a build step, network service, or credentials

## Example instruction file

```markdown
# Using dev-vault with <agent>

1. Discover: read catalog/index.json and filter by type/language/use_cases.
2. Evaluate: open the resource directory and read RESOURCE.md (or SKILL.md).
3. Check status: use only `stable` resources unattended; treat `experimental`
   as read-and-review-first.
4. Adapt: copy the resource into the target project and modify there.
   Never edit resources inside dev-vault to fit one project.
5. Contribute improvements back via pull request (see CONTRIBUTING.md).
```
