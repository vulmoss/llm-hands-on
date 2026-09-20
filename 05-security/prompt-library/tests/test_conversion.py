import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import convert_skills as converter  # noqa: E402


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_full_library_keeps_every_body_and_valid_metadata(self):
        sources = sorted((converter.ROOT / "Skills").glob("*/*/SKILL.md"))
        skills = converter.discover(converter.ROOT / "Skills")
        self.assertEqual(len(skills), len(sources))
        for skill in skills:
            with self.subTest(skill=skill.name):
                files = converter.render_codex(skill)
                entry = files[Path(skill.name) / "SKILL.md"]
                metadata = converter.parse_frontmatter(entry)
                self.assertEqual(metadata["name"], skill.name)
                self.assertTrue(metadata["description"])
                self.assertLessEqual(len(metadata["description"]), 1024)
                self.assertLess(len(entry.encode()), 4096)
                source = skill.source.read_text(encoding="utf-8-sig")
                if source.startswith("---\n"):
                    source = source.split("\n---\n", 1)[1].lstrip("\n")
                expected = source.replace(
                    "## Instructions for Claude", "## Instructions for the assistant"
                )
                self.assertTrue(
                    files[Path(skill.name) / "references/methodology.md"].endswith(expected)
                )
                chat = converter.render_chatgpt(skill, "Shared instructions")
                self.assertTrue(chat[Path(skill.name + ".md")].endswith(expected))

    def test_folded_metadata_and_legacy_headings(self):
        for name, text in (
            (
                "folded",
                "---\nname: folded\ndescription: >\n  First line\n  second line.\n---\n\n## Keep heading\n",
            ),
            (
                "legacy",
                "# Skill\n## Metadata\n- **Folder**: legacy\n## Description\nUseful reference.\n## Instructions for Claude\n## Full Methodology\n## Keep heading\n```python\nprint(1)\n```\n",
            ),
        ):
            source = self.root / "utility" / name / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text(text)
            skill = converter.load_skill(source)
            self.assertIn("## Keep heading", skill.body)
            self.assertNotIn(">", skill.description)
        self.assertEqual(converter.discover(self.root)[0].description, "First line second line.")

    def test_filters_and_unknown_category(self):
        skills = converter.discover(converter.ROOT / "Skills", ["utility"])
        self.assertTrue(skills)
        self.assertTrue(all(s.category == "utility" for s in skills))
        with self.assertRaises(ValueError):
            converter.discover(converter.ROOT / "Skills", ["../web"])

    def test_conflict_preflight_and_force(self):
        target = self.root / "export"
        target.mkdir()
        (target / "existing.md").write_text("user content")
        files = {Path("new.md"): "new", Path("existing.md"): "generated"}
        with self.assertRaises(ValueError):
            converter.write_outputs(target, files)
        self.assertFalse((target / "new.md").exists())
        self.assertEqual((target / "existing.md").read_text(), "user content")
        converter.write_outputs(target, files, force=True)
        converter.write_outputs(target, files)
        self.assertEqual((target / "existing.md").read_text(), "generated")

    def test_symlink_is_not_overwritten(self):
        original = self.root / "original.md"
        original.write_text("keep")
        (self.root / "linked.md").symlink_to(original)
        with self.assertRaises(ValueError):
            converter.write_outputs(self.root, {Path("linked.md"): "replace"}, force=True)
        self.assertEqual(original.read_text(), "keep")

    def test_dry_run_and_source_protection(self):
        output = self.root / "not-created"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                converter.main(["--category", "utility", "--output", str(output), "--dry-run"]), 0
            )
        self.assertFalse(output.exists())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                converter.main(["--output", str(converter.ROOT / "Skills"), "--force"]), 1
            )

    def test_installer_from_different_cwd_with_spaces(self):
        output = self.root / "installed skills"
        result = subprocess.run(
            [
                "bash",
                str(converter.ROOT / "install.sh"),
                "--category",
                "utility",
                "--target",
                str(output),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(output.glob("*/SKILL.md"))), 2)
        self.assertEqual(len(list(output.glob("*/references/methodology.md"))), 2)

    def test_missing_argument_does_not_write(self):
        result = subprocess.run(
            ["bash", str(converter.ROOT / "install.sh"), "--target"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(list(self.root.iterdir()))

    def test_chatgpt_export_and_manifest(self):
        output = self.root / "chatgpt"
        with contextlib.redirect_stdout(io.StringIO()):
            result = converter.main(
                ["--format", "chatgpt", "--skill", "offensive-reporting", "--output", str(output)]
            )
        self.assertEqual(result, 0)
        self.assertEqual(len(list(output.glob("*.md"))), 1)
        self.assertIn("安全研究助手", (output / "offensive-reporting.md").read_text())
        manifest_path = self.root / "skills.json"
        result = subprocess.run(
            [
                sys.executable,
                str(converter.ROOT / "tools/build_manifest.py"),
                "--output",
                str(manifest_path),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(
            manifest["skill_count"], len(converter.discover(converter.ROOT / "Skills"))
        )
        self.assertTrue(all(s["description"] for s in manifest["skills"]))


if __name__ == "__main__":
    unittest.main()
