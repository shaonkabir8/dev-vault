#!/usr/bin/env python3
"""Dev Vault validator — catalog, structure, and resource documentation checks.

Standard library only (Python 3.9+). Exits 0 when everything passes, 1 with
actionable error lines otherwise. The schemas in catalog/schema.json and
schemas/resource.schema.json are the normative metadata contract; this script
implements the JSON-Schema subset they use (see SCHEMA_KEYWORDS below) plus
filesystem checks no schema can express.

Usage:
    python3 scripts/validate.py [REPO_ROOT]
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TOP_LEVEL = [
    "AGENTS.md", "LICENSE", "README.md", "CONTRIBUTING.md", "SECURITY.md",
    "catalog", "schemas", "scripts", "tests", "docs", "resources",
]
RESOURCE_TYPES = [
    "skills", "snippets", "configurations", "templates",
    "prompts", "workflows", "references",
]
VALID_STATUS = {"experimental", "stable", "deprecated", "archived"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LANG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+#.-]*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
PATH_RE = re.compile(r"^resources/([a-z0-9-]+/)+$")

# Keys whose values map arbitrary names to schemas (field names, not keywords).
NAME_MAP_KEYS = {"properties", "definitions", "patternProperties"}

# JSON-Schema keywords implemented by the mini validator below. Any keyword
# outside this set appearing in a schema is a hard error, so schema drift
# cannot silently weaken validation.
SCHEMA_KEYWORDS = {
    "$schema", "title", "description", "type", "required", "additionalProperties",
    "properties", "enum", "const", "pattern", "minLength", "maxLength",
    "minItems", "maxItems", "items", "definitions", "$ref", "$comment",
}


def load_json(path: Path):
    """Parse a JSON file; raise ValueError with an actionable message."""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise ValueError(f"missing required file: {path}")
    except json.JSONDecodeError as exc:
        line, col = exc.lineno, exc.colno
        snippet = path.read_text(encoding="utf-8").splitlines()[line - 1][:80]
        raise ValueError(f"invalid JSON in {path} (line {line}, col {col}): {exc}\n"
                         f"  -> {snippet}")


def check_schema_keywords(node, where: str, errors: list) -> None:
    """Fail on any JSON-Schema keyword the mini validator does not implement."""
    if isinstance(node, dict):
        unknown = set(node) - SCHEMA_KEYWORDS
        if unknown:
            errors.append(f"{where}: unsupported schema keyword(s) {sorted(unknown)} "
                          f"— extend validate.py's mini validator before using them")
        for key, value in node.items():
            if key in NAME_MAP_KEYS and isinstance(value, dict):
                # Values of properties/definitions maps are schemas keyed by
                # arbitrary field names — their keys are not keywords.
                for name, sub in value.items():
                    check_schema_keywords(sub, f"{where}.{key}.{name}", errors)
            else:
                check_schema_keywords(value, f"{where}.{key}", errors)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            check_schema_keywords(value, f"{where}[{i}]", errors)


def resolve_ref(ref: str, base: Path, root_doc=None):
    """Resolve a local $ref. Supports both file refs
    (../schemas/resource.schema.json#/definitions/x) and fragment-only refs
    (#/definitions/kebab-case, resolved against the document the ref lives in).
    """
    file_part, _, pointer = ref.partition("#")
    if file_part:
        doc = root_doc = load_json((base / file_part).resolve())
    elif root_doc is not None:
        doc = root_doc
    else:
        raise ValueError(f"fragment-only $ref '{ref}' with no document context")
    for part in pointer.strip("/").split("/"):
        if part:
            doc = doc[part]
    return doc, root_doc


def validate_against_schema(data, schema, base: Path, where: str, errors: list,
                            root_doc=None) -> None:
    """Validate `data` against the JSON-Schema subset used by this repository."""
    if "$ref" in schema:
        ref = schema["$ref"]
        resolved, root_doc = resolve_ref(ref, base, root_doc)
        schema = {**resolved,
                  **{k: v for k, v in schema.items() if k != "$ref"}}
    root_doc = root_doc if root_doc is not None else schema
    t = schema.get("type")
    if t == "object" and not isinstance(data, dict):
        errors.append(f"{where}: expected an object, got {type(data).__name__}")
        return
    if t == "array" and not isinstance(data, list):
        errors.append(f"{where}: expected an array, got {type(data).__name__}")
        return
    if t == "string" and not isinstance(data, str):
        errors.append(f"{where}: expected a string, got {type(data).__name__}")
        return
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{where}: missing required field '{key}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in data:
                if key not in props:
                    errors.append(f"{where}: unknown field '{key}' (remove it or "
                                  f"update schemas/resource.schema.json deliberately)")
        for key, sub in props.items():
            if key in data:
                validate_against_schema(data[key], sub, base, f"{where}.{key}", errors,
                                        root_doc)
    elif isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"{where}: needs at least {schema['minItems']} item(s), got {len(data)}")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(f"{where}: allows at most {schema['maxItems']} item(s), got {len(data)}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(data):
                validate_against_schema(item, item_schema, base, f"{where}[{i}]", errors,
                                        root_doc)
    elif isinstance(data, str):
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append(f"{where}: '{data}' does not match required pattern {schema['pattern']}")
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{where}: shorter than {schema['minLength']} characters: '{data[:60]}'")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"{where}: longer than {schema['maxLength']} characters ({len(data)})")
    if "const" in schema and data != schema["const"]:
        errors.append(f"{where}: must be exactly {schema['const']!r}")
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{where}: '{data}' is not one of {schema['enum']}")


def check_skill_frontmatter(skill_md: Path, errors: list) -> None:
    """Basic Agent Skills frontmatter checks (spec pinned in docs/ARCHITECTURE.md)."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{skill_md}: must start with YAML frontmatter (---)")
        return
    end = text.find("\n---", 3)
    if end == -1:
        errors.append(f"{skill_md}: frontmatter block is never closed")
        return
    block = text[3:end]
    fields = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    if "name" not in fields:
        errors.append(f"{skill_md}: frontmatter missing required field 'name'")
    elif not KEBAB.match(fields["name"]):
        errors.append(f"{skill_md}: 'name: {fields['name']}' is not valid per the "
                      f"Agent Skills spec (lowercase letters, digits, single hyphens)")
    if "description" not in fields or not fields.get("description"):
        errors.append(f"{skill_md}: frontmatter missing required field 'description'")


def validate_catalog(root: Path) -> list:
    """All catalog-level checks. Returns a list of actionable error strings."""
    errors: list = []
    catalog_path = root / "catalog" / "index.json"

    try:
        catalog = load_json(catalog_path)
        schema = load_json(root / "catalog" / "schema.json")
        resource_schema = load_json(root / "schemas" / "resource.schema.json")
    except ValueError as exc:
        return [str(exc)]

    check_schema_keywords(schema, "catalog/schema.json", errors)
    check_schema_keywords(resource_schema, "schemas/resource.schema.json", errors)

    schema_base = root / "catalog"
    validate_against_schema(catalog, schema, schema_base, "catalog", errors)

    seen: dict = {}
    for i, entry in enumerate(catalog.get("resources", [])):
        where = f"catalog.resources[{i}]"
        rid = entry.get("id", f"<missing at index {i}>")

        # Duplicate ids
        if rid in seen:
            errors.append(f"{where}: duplicate resource id '{rid}' (first used by "
                          f"{seen[rid]}) — ids must be unique and never reused")
        seen[rid] = where

        path = entry.get("path", "")
        rtype = entry.get("type", "")
        # path must exist, be a directory, and start with resources/<type>/
        if path and rtype and not path.startswith(f"resources/{rtype}/"):
            errors.append(f"{where} ('{rid}'): path '{path}' does not start with "
                          f"resources/{rtype}/ — type and location must agree")
        if path:
            resolved = (root / path).resolve()
            if not resolved.is_dir():
                errors.append(f"{where} ('{rid}'): path does not exist: {path}/ "
                              f"— create the directory or fix the catalog entry")
            else:
                has_doc = (resolved / "RESOURCE.md").is_file()
                skill_md = resolved / "SKILL.md"
                if rtype == "skills":
                    if not skill_md.is_file():
                        errors.append(f"{where} ('{rid}'): skill resource has no SKILL.md "
                                      f"at {path}SKILL.md")
                    else:
                        check_skill_frontmatter(skill_md, errors)
                elif not has_doc:
                    errors.append(f"{where} ('{rid}'): missing {path}RESOURCE.md — "
                                  f"every non-skill resource documents itself (see "
                                  f"docs/RESOURCE_STANDARD.md §4b)")

    return errors


def validate_structure(root: Path) -> list:
    """Basic repository-structure checks."""
    errors = []
    for name in REQUIRED_TOP_LEVEL:
        if not (root / name).exists():
            errors.append(f"repository structure: required path '{name}/' is missing")
    if (root / "resources").is_dir():
        for child in (root / "resources").iterdir():
            if child.is_dir() and child.name not in RESOURCE_TYPES:
                errors.append(f"resources/: '{child.name}' is not a known resource type "
                              f"— expected one of {RESOURCE_TYPES}")
    for stale in ("snippets", "configs", "patterns", "commands"):
        # Legacy directory names from the pre-foundation docs; they must not
        # reappear at the root now that resources/ is the single source of truth.
        if (root / stale).is_dir():
            errors.append(f"repository structure: legacy directory '{stale}/' exists at "
                          f"the root — resources live under resources/ now")
    return errors


def main(argv: list) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else REPO_ROOT
    print(f"Validating dev-vault at {root}\n")

    errors = validate_structure(root) + validate_catalog(root)

    if errors:
        print(f"FAILED — {len(errors)} problem(s):\n")
        for err in errors:
            print(f"  ✗ {err}")
        print("\nFix each issue above, or update the schemas deliberately "
              "(see docs/RESOURCE_STANDARD.md).")
        return 1

    print("  ✓ structure: required files and directories present")
    print("  ✓ catalog: valid JSON, schema-conformant, unique ids, "
          "existing paths, documentation present")
    print("\nPASSED — catalog and structure are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
