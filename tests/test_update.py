"""Tests for update: dry run, replace and keep aside, dashboards, config, tools, plugins, saved versions."""

import contextlib
import hashlib
import io
import os
import re
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import yaml

import install
from helpers import DASHBOARD_ID, fake_plugins
from test_install import TODAY, git_run, isolate_git

AGENTS = "AGENTS.md"
CONFIG = "99 System/config.md"
V = install.kit_version()
WEEK = "01 Dashboard/02 Week.md"
BACKLOG = "01 Dashboard/04 Backlog.md"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def run_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = install.main(list(args))
    return code, out.getvalue(), err.getvalue()


def snapshot(vault: Path) -> dict[str, bytes]:
    return {path.relative_to(vault).as_posix(): path.read_bytes() for path in vault.rglob("*") if path.is_file()}


def files_outside_git(vault: Path) -> dict[str, bytes]:
    """The vault's files, not its .git folder: a failed update still saves a version before it fails."""
    return {rel: data for rel, data in snapshot(vault).items() if not rel.startswith(".git/")}


def subjects(vault: Path) -> list[str]:
    return git_run(vault, "log", "--format=%s").stdout.splitlines()


def agent_tools(vault: Path) -> list[str]:
    text = (vault / CONFIG).read_text(encoding="utf-8")
    return yaml.safe_load(FRONTMATTER.match(text).group(1))["agent_tools"]


def crlf(data: bytes) -> bytes:
    """The bytes as a Windows editor saves them. Written as bytes, so macOS and Windows run the same test."""
    return data.replace(b"\n", b"\r\n")


class UpdateTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)
        self.vault = self.tmp / "v"
        self.pins, self.folder = fake_plugins(self.tmp)
        self.patch(install, "load_pins", lambda: self.pins)  # update reads the pins: keep every test offline

    def install_vault(self, tools=("claude-code", "codex")):
        install.install(self.vault, list(tools), plugins_from=self.folder, pins=self.pins, today=TODAY)

    def expected_note(self, name: str) -> bytes:
        """The pinned fake dashboard, with its created line set to today: what update writes for a missing note."""
        fixture = (self.folder / DASHBOARD_ID / name).read_bytes()
        return fixture.replace(b"created: 2020-01-01\n", f"created: {date.today().isoformat()}\n".encode("utf-8"))

    def patch(self, target, name, value):
        patch = mock.patch.object(target, name, value)
        patch.start()
        self.addCleanup(patch.stop)

    def patch_template(self) -> Path:
        """Point install.TEMPLATE at a copy of the kit template, so a test can change the new kit."""
        copy = self.tmp / "kit-template"
        shutil.copytree(install.TEMPLATE, copy)
        self.patch(install, "TEMPLATE", copy)
        return copy

    def new_kit_version(self, version: str = "0.2.0"):
        self.patch(install, "kit_version", lambda: version)

    def read(self, rel: str) -> str:
        return (self.vault / rel).read_text(encoding="utf-8")


class DryRunTests(UpdateTestCase):
    def test_dry_run_changes_nothing(self):
        self.install_vault()
        (self.vault / AGENTS).write_text("my edits\n", encoding="utf-8")
        status = git_run(self.vault, "status", "--porcelain").stdout  # also settles the index before the snapshot
        before = snapshot(self.vault)
        code, out, err = run_cli("update", str(self.vault), "--dry-run", "--tools", "vscode")
        self.assertEqual(code, 0, err)
        self.assertNotIn("AGENTS.md", out)  # the kit did not change AGENTS.md, so the edit stays
        self.assertIn("tool  vscode  added to agent_tools\n", out)
        self.assertIn("add  .vscode/settings.json\n", out)
        self.assertTrue(out.endswith("migration: none\n"))
        self.assertEqual(snapshot(self.vault), before)
        self.assertEqual(git_run(self.vault, "status", "--porcelain").stdout, status)


class ReplaceTests(UpdateTestCase):
    def test_unedited_file_is_replaced(self):
        self.install_vault()
        copy = self.patch_template()
        (copy / "vault" / AGENTS).write_text("new agents\n", encoding="utf-8")
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn("replace  AGENTS.md\n", out)
        self.assertEqual(self.read(AGENTS), "new agents\n")
        self.assertFalse((self.vault / "AGENTS.md.mine").exists())
        # the checksum list now holds the new file, so a second update has nothing to do
        self.assertEqual(run_cli("update", str(self.vault))[1], "already up to date\nmigration: none\n")

    def test_edited_file_is_kept_aside(self):
        self.install_vault()
        (self.vault / AGENTS).write_text("my edits\n", encoding="utf-8")
        copy = self.patch_template()
        (copy / "vault" / AGENTS).write_text("new agents\n", encoding="utf-8")
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn("keep-aside  AGENTS.md  kept as AGENTS.md.mine\n", out)
        self.assertEqual(self.read("AGENTS.md.mine"), "my edits\n")
        self.assertEqual(self.read(AGENTS), "new agents\n")

    def test_edit_survives_an_update_the_kit_did_not_change(self):
        self.install_vault()
        recorded = install.read_kit_files(self.vault)[AGENTS]
        (self.vault / AGENTS).write_text("my edits\n", encoding="utf-8")
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(AGENTS), "my edits\n")
        self.assertFalse((self.vault / "AGENTS.md.mine").exists())
        self.assertEqual(install.read_kit_files(self.vault)[AGENTS], recorded)
        # the kit changes the file later: the edit is kept aside, not overwritten
        copy = self.patch_template()
        (copy / "vault" / AGENTS).write_text("new agents\n", encoding="utf-8")
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn("keep-aside  AGENTS.md  kept as AGENTS.md.mine\n", out)
        self.assertEqual(self.read("AGENTS.md.mine"), "my edits\n")
        self.assertEqual(self.read(AGENTS), "new agents\n")

    def test_unedited_file_with_unchanged_kit_content_has_no_change_line(self):
        self.install_vault()
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(out, f"version  99 System/config.md  {V} → 0.2.0\nmigration: none\n")

    def test_kept_aside_names_count_up(self):
        self.install_vault()
        (self.vault / AGENTS).write_text("my edits\n", encoding="utf-8")
        (self.vault / "AGENTS.md.mine").write_text("older\n", encoding="utf-8")
        copy = self.patch_template()
        (copy / "vault" / AGENTS).write_text("new agents\n", encoding="utf-8")
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("AGENTS.md.mine"), "older\n")
        self.assertEqual(self.read("AGENTS.md.mine2"), "my edits\n")
        self.assertEqual(self.read(AGENTS), "new agents\n")

    def test_file_the_kit_no_longer_has_is_removed_when_unedited_and_kept_when_edited(self):
        self.install_vault(("codex",))
        skills = self.tmp / "kit-skills"
        shutil.copytree(install.SKILLS, skills)
        shutil.rmtree(skills / "brain-setup")
        (skills / "brain" / "references" / "system-design.md").unlink()
        self.patch(install, "SKILLS", skills)
        (self.vault / ".agents" / "skills" / "brain-setup" / "SKILL.md").write_text("my edits\n", encoding="utf-8")
        previous = install.read_kit_files(self.vault)[".agents/skills/brain-setup/SKILL.md"]
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn("remove  .agents/skills/brain/references/system-design.md\n", out)
        self.assertNotIn("brain-setup", out)
        self.assertFalse((self.vault / ".agents" / "skills" / "brain" / "references" / "system-design.md").exists())
        self.assertEqual(self.read(".agents/skills/brain-setup/SKILL.md"), "my edits\n")
        # left alone: kit-files keeps the sha the kit last wrote there, never the person's edit
        self.assertEqual(install.read_kit_files(self.vault)[".agents/skills/brain-setup/SKILL.md"], previous)


class ConfigAndDashboardTests(UpdateTestCase):
    def test_dashboards_and_config_untouched(self):
        self.install_vault()
        week = self.vault / WEEK
        text = week.read_text(encoding="utf-8")
        week.write_text(text.replace("type: note\n", "type: note\narrange: today, week\n", 1), encoding="utf-8")
        config = self.vault / CONFIG
        config.write_bytes(crlf(config.read_bytes().replace(
            b"contexts: [home, out, computer, phone]", b"contexts: [home, out]")))
        dashboards = {path: path.read_bytes() for path in (self.vault / "01 Dashboard").glob("*.md")}
        config_before = config.read_bytes()
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn(f"version  99 System/config.md  {V} → 0.2.0\n", out)
        self.assertIn("arrange: today, week", week.read_text(encoding="utf-8"))
        for path, data in dashboards.items():
            with self.subTest(dashboard=path.name):
                self.assertEqual(path.read_bytes(), data)
        self.assertEqual(config.read_bytes(),
                         config_before.replace(f'system_version: "{V}"'.encode(), b'system_version: "0.2.0"'))

    def test_crlf_config_is_read_and_only_its_two_lines_change(self):
        self.install_vault(("codex",))
        config = self.vault / CONFIG
        config.write_bytes(crlf(config.read_bytes()))
        before = config.read_bytes()
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault), "--tools", "claude-code")
        self.assertEqual(code, 0, err)
        self.assertEqual(config.read_bytes(), before
                         .replace(f'system_version: "{V}"'.encode(), b'system_version: "0.2.0"')
                         .replace(b"agent_tools: [codex]", b"agent_tools: [codex, claude-code]"))
        self.assertEqual(agent_tools(self.vault), ["codex", "claude-code"])

    def test_missing_dashboard_is_added_not_rewritten(self):
        self.install_vault()
        (self.vault / BACKLOG).unlink()
        code, out, err = run_cli("update", str(self.vault), "--plugins-from", str(self.folder))
        self.assertEqual(code, 0, err)
        self.assertIn("dashboard  01 Dashboard/04 Backlog.md\n", out)
        self.assertEqual((self.vault / BACKLOG).read_bytes(), self.expected_note("04 Backlog.md"))

    def test_missing_dashboard_is_downloaded_from_its_pin_without_plugins_from(self):
        self.install_vault()
        (self.vault / BACKLOG).unlink()
        fixtures = {pin["url"]: (self.folder / DASHBOARD_ID / name).read_bytes()
                    for name, pin in self.pins[DASHBOARD_ID]["files"].items()}
        with mock.patch.object(install, "download", side_effect=fixtures.__getitem__) as download:
            code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(call.args[0] for call in download.call_args_list), sorted(fixtures))
        self.assertEqual((self.vault / BACKLOG).read_bytes(), self.expected_note("04 Backlog.md"))

    def test_dry_run_plans_a_missing_dashboard_without_downloading(self):
        self.install_vault()
        (self.vault / BACKLOG).unlink()
        with mock.patch.object(install, "download") as download:
            code, out, err = run_cli("update", str(self.vault), "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("dashboard  01 Dashboard/04 Backlog.md\n", out)
        download.assert_not_called()

    def test_missing_dashboard_checksum_mismatch_writes_nothing(self):
        self.install_vault()
        (self.vault / BACKLOG).unlink()
        (self.folder / DASHBOARD_ID / "02 Week.md").write_bytes(b"corrupted\n")
        before = files_outside_git(self.vault)
        code, out, err = run_cli("update", str(self.vault), "--plugins-from", str(self.folder))
        self.assertEqual(code, 1)
        self.assertIn("02 Week.md", err)
        self.assertFalse((self.vault / BACKLOG).exists())
        self.assertEqual(files_outside_git(self.vault), before)

    def test_a_note_folder_is_never_read_as_a_plugin(self):
        self.install_vault()
        folder = self.vault / ".obsidian" / "plugins" / DASHBOARD_ID  # a manifest here must never be read
        folder.mkdir(parents=True)
        (folder / "manifest.json").write_text('{"version": "9.9.9"}', encoding="utf-8")
        changes = install.plan_update(self.vault, tools=None, pins=self.pins)
        self.assertEqual([change for change in changes if change.action == "plugin"], [])


class ToolTests(UpdateTestCase):
    def test_add_a_tool(self):
        self.install_vault(("codex",))
        code, out, err = run_cli("update", str(self.vault), "--tools", "claude-code")
        self.assertEqual(code, 0, err)
        self.assertIn("tool  claude-code  added to agent_tools\n", out)
        self.assertIn("add  CLAUDE.md\n", out)
        self.assertIn("add  .claude/skills  link to .agents/skills\n", out)
        self.assertTrue((self.vault / "CLAUDE.md").is_file())
        self.assertEqual(os.path.realpath(self.vault / ".claude" / "skills"),
                         os.path.realpath(self.vault / ".agents" / "skills"))
        self.assertEqual(agent_tools(self.vault), ["codex", "claude-code"])
        self.assertIn("agent_tools: [codex, claude-code]\n", self.read(CONFIG))

    def test_unknown_tool_in_config_refuses_the_update_and_writes_nothing(self):
        self.install_vault(("codex",))
        config = self.vault / CONFIG
        config.write_bytes(crlf(config.read_bytes().replace(b"agent_tools: [codex]", b"agent_tools: [../../x]")))
        before = snapshot(self.vault)
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 1)
        self.assertEqual(err, f"install.py: {CONFIG}: agent_tools names an unknown tool '../../x' "
                              "(choose from claude-code, codex, vscode)\n")
        self.assertEqual(snapshot(self.vault), before)
        self.assertEqual(subjects(self.vault), [f"Installed by second-brain-setup {V}"])


class SavedVersionTests(UpdateTestCase):
    def test_update_saves_before_and_after(self):
        self.install_vault(("codex",))
        week = self.vault / WEEK
        week.write_text(week.read_text(encoding="utf-8") + "\nmy own line\n", encoding="utf-8")
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(subjects(self.vault), [
            "Updated to second-brain-setup 0.2.0",
            "Saved before update to 0.2.0",
            f"Installed by second-brain-setup {V}",
        ])
        self.assertEqual(git_run(self.vault, "status", "--porcelain").stdout, "")

    def test_clean_vault_gets_no_saved_commit(self):
        self.install_vault(("codex",))
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(subjects(self.vault), [
            "Updated to second-brain-setup 0.2.0",
            f"Installed by second-brain-setup {V}",
        ])

    def test_already_up_to_date_writes_nothing(self):
        self.install_vault(("codex",))
        before = snapshot(self.vault)
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "already up to date\nmigration: none\n")
        self.assertEqual(snapshot(self.vault), before)
        self.assertEqual(subjects(self.vault), [f"Installed by second-brain-setup {V}"])

    def test_refuses_a_vault_without_its_own_git_repository(self):
        self.install_vault(("codex",))
        install.remove_tree(self.vault / ".git")
        git_run(self.tmp, "init", "-q")  # a parent repository with a staged file that is not the vault's
        (self.tmp / "staged-elsewhere.txt").write_text("not the kit's\n", encoding="utf-8")
        git_run(self.tmp, "add", "staged-elsewhere.txt")
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 1)
        self.assertEqual(err, f"install.py: {self.vault} has no git repository of its own\n")
        self.assertEqual(git_run(self.tmp, "diff", "--cached", "--name-only").stdout, "staged-elsewhere.txt\n")
        self.assertEqual(git_run(self.tmp, "rev-parse", "-q", "--verify", "HEAD").returncode, 1)  # nothing committed

    def test_empty_git_folder_inside_another_repository_is_refused(self):
        self.install_vault(("codex",))
        install.remove_tree(self.vault / ".git")
        (self.vault / ".git").mkdir()  # empty: git skips it and finds the outer repository instead
        git_run(self.tmp, "init", "-q")
        (self.tmp / "staged-elsewhere.txt").write_text("not the kit's\n", encoding="utf-8")
        git_run(self.tmp, "add", "staged-elsewhere.txt")
        self.new_kit_version()
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 1)
        self.assertEqual(err, f"install.py: {self.vault} has no git repository of its own\n")
        self.assertEqual(git_run(self.tmp, "diff", "--cached", "--name-only").stdout, "staged-elsewhere.txt\n")
        self.assertEqual(git_run(self.tmp, "rev-parse", "-q", "--verify", "HEAD").returncode, 1)  # nothing committed

    def test_refuses_a_folder_that_is_not_a_vault(self):
        self.vault.mkdir()
        git_run(self.vault, "init", "-q")  # a real repository of its own, so the git check passes
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 1)
        self.assertEqual(err, f"install.py: {self.vault} is not a second-brain vault\n")


class RecheckTests(UpdateTestCase):
    """The plan is made first; the person can edit before apply writes. Each file is checked again just before it is
    written or removed, so an edit made in between is kept (aside) and never overwritten."""

    def plan(self, tools=None):
        return install.plan_update(self.vault, tools=tools, pins=self.pins)

    def apply(self, changes):
        install.apply_update(self.vault, changes, plugins_from=self.folder, pins=self.pins)

    def test_planned_replace_becomes_keep_aside_when_the_person_edits_first(self):
        self.install_vault()
        copy = self.patch_template()
        (copy / "vault" / AGENTS).write_text("new agents\n", encoding="utf-8")
        changes = self.plan()
        self.assertEqual([(c.action, c.path) for c in changes], [("replace", AGENTS)])
        (self.vault / AGENTS).write_text("my edits\n", encoding="utf-8")
        self.apply(changes)
        self.assertEqual(self.read("AGENTS.md.mine"), "my edits\n")
        self.assertEqual(self.read(AGENTS), "new agents\n")
        self.assertEqual(install.read_kit_files(self.vault)[AGENTS], hashlib.sha256(b"new agents\n").hexdigest())

    def test_planned_remove_is_skipped_when_the_person_edits_first(self):
        self.install_vault(("codex",))
        skills = self.tmp / "kit-skills"
        shutil.copytree(install.SKILLS, skills)
        rel = ".agents/skills/brain/references/system-design.md"
        (skills / "brain" / "references" / "system-design.md").unlink()
        self.patch(install, "SKILLS", skills)
        previous = install.read_kit_files(self.vault)[rel]
        changes = self.plan()
        self.assertEqual([(c.action, c.path) for c in changes], [("remove", rel)])
        (self.vault / rel).write_text("my edits\n", encoding="utf-8")
        self.apply(changes)
        self.assertEqual(self.read(rel), "my edits\n")
        self.assertEqual(install.read_kit_files(self.vault)[rel], previous)

    def test_planned_add_keeps_a_file_the_person_created_first(self):
        self.install_vault(("codex",))
        changes = self.plan(tools=["claude-code"])
        self.assertIn(("add", "CLAUDE.md"), [(c.action, c.path) for c in changes])
        (self.vault / "CLAUDE.md").write_text("my own notes\n", encoding="utf-8")
        self.apply(changes)
        self.assertEqual(self.read("CLAUDE.md.mine"), "my own notes\n")
        kit_text = (install.TEMPLATE / "tools" / "claude-code" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(self.read("CLAUDE.md"), kit_text)

    def test_planned_dashboard_is_not_overwritten_when_it_appears_first(self):
        self.install_vault()
        (self.vault / BACKLOG).unlink()
        changes = self.plan()
        self.assertEqual([(c.action, c.path) for c in changes], [("dashboard", BACKLOG)])
        (self.vault / BACKLOG).write_text("my board\n", encoding="utf-8")
        self.apply(changes)
        self.assertEqual(self.read(BACKLOG), "my board\n")


class KitFilesPathTests(UpdateTestCase):
    def test_a_kit_files_path_outside_the_vault_is_ignored_with_a_warning_and_never_removed(self):
        self.install_vault(("codex",))
        outside = self.tmp / "outside.txt"
        outside.write_text("keep me\n", encoding="utf-8")
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()  # a matching hash: the old code removed it
        kit_files = self.vault / install.KIT_FILES
        recorded = kit_files.read_text(encoding="utf-8")
        for rel in ("../outside.txt", str(outside)):
            with self.subTest(path=rel):
                kit_files.write_text(recorded + f"{digest}  {rel}\n", encoding="utf-8")
                code, out, err = run_cli("update", str(self.vault))
                self.assertEqual(code, 0, err)
                self.assertIn(rel, err)  # the warning line names the path
                self.assertEqual(outside.read_text(encoding="utf-8"), "keep me\n")

    def test_a_recorded_path_the_kit_never_installs_is_ignored_with_a_warning_and_never_removed(self):
        self.install_vault(("codex",))
        note = self.vault / "01 Dashboard" / "01 Today.md"  # inside the vault, but not a system file
        digest = hashlib.sha256(note.read_bytes()).hexdigest()  # the real hash: only the path is wrong
        kit_files = self.vault / install.KIT_FILES
        kit_files.write_text(kit_files.read_text(encoding="utf-8") + f"{digest}  01 Dashboard/01 Today.md\n",
                             encoding="utf-8")
        code, out, err = run_cli("update", str(self.vault))
        self.assertEqual(code, 0, err)
        self.assertIn("01 Dashboard/01 Today.md", err)  # the warning line names the path
        self.assertTrue(note.is_file())


class OutputTests(UpdateTestCase):
    def test_output_is_utf8_even_on_a_narrow_pipe(self):
        self.install_vault(("codex",))
        self.new_kit_version()
        pipe = io.TextIOWrapper(io.BytesIO(), encoding="ascii")  # a Windows pipe with a narrow code page
        with contextlib.redirect_stdout(pipe):
            code = install.main(["update", str(self.vault), "--dry-run"])
        pipe.flush()
        self.assertEqual(code, 0)
        self.assertIn("→".encode("utf-8"), pipe.buffer.getvalue())


class PluginTests(UpdateTestCase):
    def install_with_older_ninja_board(self):
        """A vault with ninja-board 1.0.0 installed; the pins now say 1.1.0 and their files are the new release."""
        pins, folder = fake_plugins(self.tmp)
        pins["ninja-board"]["in_directory"] = False
        install.install(self.vault, ["codex"], plugins_from=folder, pins=pins, today=TODAY)
        (self.vault / ".obsidian" / "plugins" / "ninja-board" / "manifest.json").write_text(
            '{"version": "1.0.0"}', encoding="utf-8")
        manifest = b'{"version": "1.1.0"}\n'
        main = b"new main\n"
        release = folder / "ninja-board"
        (release / "manifest.json").write_bytes(manifest)
        (release / "main.js").write_bytes(main)
        pins["ninja-board"]["version"] = "1.1.0"
        pins["ninja-board"]["files"]["manifest.json"]["sha256"] = hashlib.sha256(manifest).hexdigest()
        pins["ninja-board"]["files"]["main.js"]["sha256"] = hashlib.sha256(main).hexdigest()
        return pins, folder

    def test_pinned_plugin_is_replaced_from_plugins_from(self):
        pins, folder = self.install_with_older_ninja_board()
        plugin_dir = self.vault / ".obsidian" / "plugins" / "ninja-board"
        with mock.patch.object(install, "load_pins", return_value=pins):
            code, out, err = run_cli("update", str(self.vault), "--plugins-from", str(folder))
        self.assertEqual(code, 0, err)
        self.assertIn("plugin  .obsidian/plugins/ninja-board  ninja-board 1.0.0 → 1.1.0\n", out)
        self.assertEqual((plugin_dir / "main.js").read_bytes(), b"new main\n")
        self.assertEqual((plugin_dir / "manifest.json").read_bytes(), b'{"version": "1.1.0"}\n')
        with mock.patch.object(install, "load_pins", return_value=pins):
            self.assertEqual(run_cli("update", str(self.vault))[1], "already up to date\nmigration: none\n")

    def test_dry_run_never_fetches_a_plugin(self):
        pins, _ = self.install_with_older_ninja_board()
        pins["ninja-board"]["files"]["main.js"]["sha256"] = None  # a fetch would refuse this
        with mock.patch.object(install, "load_pins", return_value=pins):
            code, out, err = run_cli("update", str(self.vault), "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("plugin  .obsidian/plugins/ninja-board  ninja-board 1.0.0 → 1.1.0\n", out)


if __name__ == "__main__":
    unittest.main()
