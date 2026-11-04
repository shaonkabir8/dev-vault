"""Unit tests for the Dev Vault foundation validator.

Run: python3 -m unittest discover -s tests -v
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "validate.py"

# A minimal valid catalog entry, used as the base for mutation tests.
VALID_ENTRY = {
    "id": "test-resource",
    "name": "Test Resource",
    "type": "snippets",
    "description": "A valid test resource used only by the test suite.",
    "path": "resources/snippets/test-resource/",
    "language": ["python"],
    "compatibility": ["universal"],
    "dependencies": [],
    "license": "inherit",
    "status": "experimental",
    "version": "0.1.0",
}


class ValidatorTestCase(unittest.TestCase):
    """Runs scripts/validate.py against temporary repository fixtures."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dev-vault-test-"))
        self.addCleanup(shutil.rmtree, self.tmp)
        # Minimal valid repository fixture.
        for d in ["catalog", "schemas", "scripts", "tests", "docs", "resources",
                  "resources/snippets/test-resource"]:
            (self.tmp / d).mkdir(parents=True)
        for name in ["AGENTS.md", "LICENSE", "README.md", "CONTRIBUTING.md",
                     "SECURITY.md"]:
            (self.tmp / name).write_text("placeholder\n", encoding="utf-8")
        shutil.copy(REPO_ROOT / "schemas" / "resource.schema.json",
                    self.tmp / "schemas" / "resource.schema.json")
        (self.tmp / "resources" / "snippets" / "test-resource" / "RESOURCE.md").write_text(
            "# Test Resource\n", encoding="utf-8")

    def write_catalog(self, resources):
        catalog = {"$schema": "./schema.json", "version": 1, "resources": resources}
        (self.tmp / "catalog" / "index.json").write_text(
            json.dumps(catalog, indent=2), encoding="utf-8")
        shutil.copy(REPO_ROOT / "catalog" / "schema.json",
                    self.tmp / "catalog" / "schema.json")

    def run_validator(self):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.tmp)],
            capture_output=True, text=True)

    # -- valid cases -------------------------------------------------------

    def test_valid_catalog_passes(self):
        self.write_catalog([VALID_ENTRY])
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_empty_catalog_passes(self):
        self.write_catalog([])
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    # -- invalid metadata --------------------------------------------------

    def test_missing_required_field_fails(self):
        broken = {k: v for k, v in VALID_ENTRY.items() if k != "description"}
        self.write_catalog([broken])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("description", result.stdout)

    def test_invalid_status_fails(self):
        entry = {**VALID_ENTRY, "status": "wip"}
        self.write_catalog([entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("status", result.stdout)

    def test_bad_id_format_fails(self):
        entry = {**VALID_ENTRY, "id": "Test Resource"}
        self.write_catalog([entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("id", result.stdout)
        self.assertIn("'Test Resource'", result.stdout)

    def test_unknown_field_fails(self):
        entry = {**VALID_ENTRY, "extra": "not allowed"}
        self.write_catalog([entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("extra", result.stdout)

    def test_type_path_mismatch_fails(self):
        entry = {**VALID_ENTRY, "path": "resources/prompts/test-resource/"}
        self.write_catalog([entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not start with resources/snippets/", result.stdout)

    # -- missing paths / docs ----------------------------------------------

    def test_missing_resource_path_fails(self):
        shutil.rmtree(self.tmp / "resources" / "snippets" / "test-resource")
        self.write_catalog([VALID_ENTRY])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("path does not exist", result.stdout)

    def test_missing_resource_md_fails(self):
        (self.tmp / "resources" / "snippets" / "test-resource" / "RESOURCE.md").unlink()
        self.write_catalog([VALID_ENTRY])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("RESOURCE.md", result.stdout)

    def test_skill_without_skill_md_fails(self):
        (self.tmp / "resources" / "snippets" / "test-resource" / "RESOURCE.md").unlink()
        (self.tmp / "resources" / "skills" / "test-skill").mkdir(parents=True)
        entry = {**VALID_ENTRY, "id": "test-skill", "type": "skills",
                 "path": "resources/skills/test-skill/"}
        self.write_catalog([entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SKILL.md", result.stdout)

    # -- duplicate ids / broken references ---------------------------------

    def test_duplicate_ids_fail(self):
        self.write_catalog([VALID_ENTRY, VALID_ENTRY])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate resource id", result.stdout)

    def test_invalid_json_fails(self):
        self.write_catalog([VALID_ENTRY])
        (self.tmp / "catalog" / "index.json").write_text(
            '{"resources": [ oops', encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stdout)
        self.assertIn("line", result.stdout)  # actionable: points at the line

    def test_unknown_schema_keyword_is_flagged(self):
        self.write_catalog([VALID_ENTRY])
        schema = json.loads((REPO_ROOT / "catalog" / "schema.json").read_text())
        schema["properties"]["resources"]["frobnicate"] = True
        (self.tmp / "catalog" / "schema.json").write_text(
            json.dumps(schema), encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported schema keyword", result.stdout)

    # -- failure messages are actionable -----------------------------------

    def test_failures_are_actionable(self):
        """Every failure line names the offending path/field, not just 'error'."""
        self.write_catalog([VALID_ENTRY, VALID_ENTRY])
        entry = {**VALID_ENTRY, "id": "second", "path": "resources/nowhere/"}
        self.write_catalog([VALID_ENTRY, entry])
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        for token in ("catalog.resources[1]", "second", "path does not exist"):
            self.assertIn(token, result.stdout)


if __name__ == "__main__":
    unittest.main()
