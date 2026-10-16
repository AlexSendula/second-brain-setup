"""Tests for the 99 System content (type definitions and config), read from an installed vault."""

import os
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import yaml

import install
from helpers import isolated_git_env

TODAY = date(2026, 10, 16)
SYSTEM = Path("99 System")
KINDS = [
    "inbox", "area", "project", "task", "appointment", "list", "note", "person",
    "people", "conversation", "week-plan", "config", "rules", "commitment", "type",
]
ADDON_KINDS = ["time-log"]
FORMATS = {
    "date", "datetime", "time", "duration", "repeat", "weekdays", "when", "week",
    "birthday", "link", "text", "boolean", "number", "list",
}
SPEC_KEYS = {"format", "values", "values_from"}
REQUIRED_WHEN = re.compile(r"^\w+ is [^ ]+( or [^ ]+)*$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_frontmatter(path: Path) -> dict:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if match is None:
        raise AssertionError(f"{path.name} has no frontmatter")
    return yaml.safe_load(match.group(1))


def read_body(path: Path) -> str:
    return FRONTMATTER.sub("", path.read_text(encoding="utf-8"), count=1)


class InstalledVaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        # Install runs git: hide the developer's global config (hooks included) while it runs.
        patch = mock.patch.dict(os.environ, isolated_git_env(Path(tmp.name)), clear=True)
        patch.start()
        cls.addClassCleanup(patch.stop)
        cls.vault = Path(tmp.name) / "vault"
        install.install(cls.vault, ["claude-code", "codex"], plugins_from=None, pins={}, today=TODAY)

    def test_every_type_definition_parses(self):
        paths = sorted((self.vault / SYSTEM / "types").glob("*.md"))
        paths.append(self.vault / SYSTEM / "addons" / "capacity" / "types" / "time-log.md")
        self.assertEqual(sorted(p.stem for p in paths), sorted(KINDS + ADDON_KINDS))
        for path in paths:
            with self.subTest(file=path.name):
                meta = read_frontmatter(path)
                self.assertEqual(meta["type"], "type")
                self.assertEqual(meta["name"], path.stem)
                self.assertIn("folder", meta)
                self.assertIn("filename", meta)
                self.assertIsInstance(meta["fields"], dict)
                for field, spec in meta["fields"].items():
                    with self.subTest(field=field):
                        self.assertEqual(len(SPEC_KEYS & spec.keys()), 1)
                        formats = spec.get("format", [])
                        for name in [formats] if isinstance(formats, str) else formats:
                            self.assertIn(name, FORMATS)
                        if "required_when" in spec:
                            self.assertRegex(spec["required_when"], REQUIRED_WHEN)
                self.assertRegex(path.read_text(encoding="utf-8"), r"(?m)^## Template$")

    def test_allowed_words_are_written_in_the_body(self):
        inbox = read_body(self.vault / SYSTEM / "types" / "inbox.md")
        config = read_body(self.vault / SYSTEM / "types" / "config.md")
        self.assertIn("a feed's name", inbox)
        self.assertIn("vscode", config)

    def test_cross_field_rules_are_written_in_words(self):
        task = read_body(self.vault / SYSTEM / "types" / "task.md")
        commitment = read_body(self.vault / SYSTEM / "types" / "commitment.md")
        self.assertIn("repeat requires due", task)
        self.assertIn("length is required", commitment)

    def test_task_type_matches_the_spec(self):
        fields = read_frontmatter(self.vault / SYSTEM / "types" / "task.md")["fields"]
        self.assertEqual(fields["status"]["values"], ["open", "doing", "waiting", "someday", "done", "dropped"])
        self.assertEqual(fields["waiting_on"]["required_when"], "status is waiting")
        self.assertEqual(fields["chase"]["required_when"], "status is waiting")
        self.assertEqual(fields["done"]["required_when"], "status is done or dropped")
        self.assertEqual(fields["points"]["values"], [1, 2, 3, 5, 8])
        self.assertEqual(fields["if_missed"]["default"], "carry")

    def test_config_type_lists_every_key(self):
        keys = set(read_frontmatter(self.vault / SYSTEM / "types" / "config.md")["fields"])
        self.assertEqual(keys, {
            "system_version", "format_version", "update_source", "agent_tools", "addons",
            "contexts", "weekly_review", "daily_briefing", "week_plan", "timezone",
            "points_per_week", "available", "available_days",
        })

    def test_config_after_install(self):
        meta = read_frontmatter(self.vault / SYSTEM / "config.md")
        self.assertEqual(list(meta), [
            "type", "created", "system_version", "format_version", "update_source",
            "agent_tools", "addons", "contexts", "weekly_review", "daily_briefing",
            "week_plan", "timezone",
        ])
        self.assertEqual(meta["type"], "config")
        self.assertEqual(meta["created"], TODAY)
        self.assertEqual(meta["agent_tools"], ["claude-code", "codex"])
        self.assertEqual(meta["system_version"], "0.1.0")
        self.assertEqual(meta["update_source"], "https://github.com/AlexSendula/second-brain-setup")
        self.assertEqual(meta["format_version"], 1)


class KitTextTests(unittest.TestCase):
    """The agent-facing text in the kit: the skills and AGENTS.md, read from the kit folder."""

    def test_skill_frontmatter(self):
        paths = sorted(install.SKILLS.glob("*/SKILL.md"))
        self.assertIn(install.SKILLS / "brain" / "SKILL.md", paths)
        self.assertIn(install.SKILLS / "brain-setup" / "SKILL.md", paths)
        for path in paths:
            with self.subTest(skill=path.parent.name):
                meta = read_frontmatter(path)
                self.assertEqual(meta["name"], path.parent.name)
                self.assertIsInstance(meta["description"], str)
                self.assertTrue(meta["description"].strip())
                self.assertLess(len(meta["description"]), 1024)

    def test_agents_md(self):
        text = (install.TEMPLATE / "vault" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 120)
        for phrase in (
            ".memory/MEMORY.md", "99 System/rules.md", "brain.py", "references/system-design.md",
            "update my brain", "Never", "Outside the vault", "setup has not run",
            "(the person's request covers those edits)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertNotIn("{{", text)  # install fills placeholders; AGENTS.md must not carry any

    def test_setup_md(self):
        text = (install.KIT_ROOT / "SETUP.md").read_text(encoding="utf-8")
        for phrase in (
            "0.9.0", "1.10.2", "xcode-select --install", "winget install --id Git.Git -e",
            "Trust author and enable plugins", "brain-setup/SKILL.md", "OneDrive", "--depth 1 --branch",
            "2.28 or newer", "--accept-package-agreements", "drag it to Applications", "--tools none",
            "answer yes", "quit", "its five dashboard notes come from the same release",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
