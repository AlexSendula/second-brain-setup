"""Tests for install.py: validation, the vault skeleton, Obsidian settings, the checksum list, saved versions."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import install
from helpers import DASHBOARD_ID, DASHBOARD_NAMES, fake_pins, isolated_git_env

TODAY = date(2026, 10, 16)
CLAUDE_FILE = "@../AGENTS.md\n@../.memory/MEMORY.md\n"  # imports in .claude/CLAUDE.md are relative to that file


def run_main(*args: str) -> tuple[int, str]:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = install.main(list(args))
    return code, err.getvalue()


def do_install(target: Path, tools: list[str]) -> None:
    install.install(target, tools, pinned_from=None, pins={}, today=TODAY)


def isolate_git(case: unittest.TestCase, tmp: Path) -> Path:
    """Hide the user's git config for the rest of the test. Return the empty global config git reads instead."""
    patch = mock.patch.dict(os.environ, isolated_git_env(tmp), clear=True)
    patch.start()
    case.addCleanup(patch.stop)
    return tmp / "empty-gitconfig"


def git_run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True, check=False)


class ToolValidationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def test_parse_tools_keeps_valid_order(self):
        self.assertEqual(install.parse_tools("claude-code,codex"), ["claude-code", "codex"])

    def test_none_means_no_tools(self):
        self.assertEqual(install.parse_tools("none"), [])

    def test_none_cannot_be_combined_with_a_tool(self):
        code, err = run_main("install", str(self.tmp / "v"), "--tools", "none,codex")
        self.assertEqual(code, 1)
        self.assertEqual(err, "install.py: --tools none cannot be combined with other tool ids\n")
        self.assertFalse((self.tmp / "v").exists())

    def test_unknown_tool_is_refused(self):
        code, err = run_main("install", str(self.tmp / "v"), "--tools", "cursor")
        self.assertEqual(code, 1)
        self.assertEqual(err, "install.py: unknown tool 'cursor' (choose from claude-code, codex, vscode)\n")
        self.assertFalse((self.tmp / "v").exists())

    def test_empty_tools_is_refused(self):
        code, err = run_main("install", str(self.tmp / "v"), "--tools", "")
        self.assertEqual(code, 1)
        self.assertEqual(err, "install.py: --tools needs at least one tool id\n")
        self.assertFalse((self.tmp / "v").exists())

    def test_duplicate_tools_is_refused(self):
        code, err = run_main("install", str(self.tmp / "v"), "--tools", "claude-code,claude-code")
        self.assertEqual(code, 1)
        self.assertEqual(err, "install.py: --tools lists a tool twice\n")
        self.assertFalse((self.tmp / "v").exists())


class UsageErrorTests(unittest.TestCase):
    def test_missing_argument_is_one_line_and_returns_1(self):
        code, err = run_main("install")
        self.assertEqual(code, 1)
        lines = err.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("install.py: "))


class InstallTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)

    def test_install_creates_the_folders(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        for name in install.FOLDERS:
            self.assertTrue((target / name).is_dir(), name)
        self.assertTrue((target / "02 Inbox" / ".gitkeep").exists())

    def test_memory_file_is_created_empty(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        memory = target / ".memory" / "MEMORY.md"
        self.assertTrue(memory.is_file())
        self.assertEqual(memory.read_bytes(), b"")

    def test_only_chosen_tools_files(self):
        vscode = self.tmp / "vs"
        do_install(vscode, ["vscode"])
        self.assertTrue((vscode / ".vscode" / "settings.json").is_file())
        self.assertFalse((vscode / "CLAUDE.md").exists())
        self.assertFalse((vscode / ".claude").exists())

        claude = self.tmp / "cc"
        do_install(claude, ["claude-code"])
        self.assertTrue((claude / ".claude" / "CLAUDE.md").is_file())
        self.assertFalse((claude / ".vscode").exists())

    def test_claude_code_file_is_dot_claude_claude_md_with_two_imports(self):
        target = self.tmp / "v"
        do_install(target, ["claude-code"])
        self.assertEqual((target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"), CLAUDE_FILE)
        self.assertFalse((target / "CLAUDE.md").exists())

    def test_refuses_non_empty_folder(self):
        target = self.tmp / "v"
        target.mkdir()
        (target / "note.md").write_text("mine", encoding="utf-8")
        with self.assertRaises(install.InstallError):
            do_install(target, ["codex"])
        self.assertEqual(sorted(p.name for p in target.iterdir()), ["note.md"])
        self.assertEqual((target / "note.md").read_text(encoding="utf-8"), "mine")

    def test_ignorable_files_count_as_empty(self):
        for name in (".DS_Store", "Thumbs.db", "desktop.ini"):
            with self.subTest(name=name):
                target = Path(tempfile.mkdtemp(dir=self.tmp))
                (target / name).write_bytes(b"")
                do_install(target, ["codex"])
                self.assertTrue((target / "01 Dashboard").is_dir())

    def test_space_and_accent_in_path(self):
        target = self.tmp / "Mïn brain"
        do_install(target, ["codex"])
        self.assertTrue((target / "01 Dashboard").is_dir())

    def test_skills_installed(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        skills = target / ".agents" / "skills"
        self.assertTrue((skills / "brain" / "SKILL.md").is_file())
        self.assertTrue((skills / "brain-setup" / "SKILL.md").is_file())
        system = skills / "brain" / "references" / "system-design.md"
        self.assertTrue(system.read_text(encoding="utf-8").startswith("# Second Brain: system design"))
        for source in sorted(install.SKILLS.rglob("*")):
            if source.is_file():
                rel = source.relative_to(install.SKILLS)
                with self.subTest(file=rel.as_posix()):
                    self.assertEqual((skills / rel).read_bytes(), source.read_bytes())

    def test_system_design_has_no_jekyll_tags(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        system = target / ".agents" / "skills" / "brain" / "references" / "system-design.md"
        text = system.read_text(encoding="utf-8")
        self.assertNotIn("{{", text)
        self.assertNotIn("{%", text)

    def test_claude_skills_link(self):
        target = self.tmp / "v"
        do_install(target, ["claude-code"])
        link = target / ".claude" / "skills"
        self.assertTrue((link / "brain" / "SKILL.md").is_file())
        self.assertEqual(os.path.realpath(link), os.path.realpath(target / ".agents" / "skills"))
        bare = self.tmp / "bare"
        do_install(bare, ["codex"])
        self.assertFalse((bare / ".claude").exists())

    @unittest.skipIf(os.name == "nt", "off Windows the link is a symlink")
    def test_claude_skills_link_is_the_only_git_entry(self):
        target = self.tmp / "v"
        do_install(target, ["claude-code"])
        self.assertEqual(git_run(target, "ls-files", ".claude/skills").stdout, ".claude/skills\n")

    def test_claude_skills_contents_are_not_saved(self):
        """On Windows the link is a junction, which git reads as a folder. A real folder stands in for it here."""
        target = self.tmp / "v"
        do_install(target, ["claude-code"])
        link = target / ".claude" / "skills"
        if link.is_symlink():
            link.unlink()
        else:
            os.rmdir(link)  # a junction
        shutil.copytree(target / ".agents" / "skills", link)
        git_run(target, "add", "-A")
        listed = git_run(target, "ls-files", ".claude/skills").stdout.splitlines()
        self.assertLessEqual(len(listed), 1, listed)

    def test_none_installs_no_tool_files(self):
        target = self.tmp / "v"
        with mock.patch.object(install, "load_pins", return_value={}):  # keep the test offline
            code, err = run_main("install", str(target), "--tools", "none")
        self.assertEqual(code, 0, err)
        for name in ("CLAUDE.md", ".claude", ".vscode"):
            self.assertFalse((target / name).exists(), name)
        config = (target / install.CONFIG).read_text(encoding="utf-8")
        self.assertEqual(install.config_value(config, "agent_tools"), "[]")


class FailedInstallTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)

    def break_git_after_the_writes(self):
        """Make the first git call fail. It runs after the vault's files are written."""
        patch = mock.patch.object(install, "git", side_effect=install.InstallError("git failed (injected)"))
        patch.start()
        self.addCleanup(patch.stop)

    def test_failure_after_the_first_write_removes_the_new_folder(self):
        target = self.tmp / "v"
        self.break_git_after_the_writes()
        with self.assertRaises(install.InstallError):
            do_install(target, ["claude-code"])
        self.assertFalse(target.exists())

    def test_failure_keeps_a_folder_that_was_there_with_only_os_files(self):
        target = self.tmp / "v"
        target.mkdir()
        (target / ".DS_Store").write_bytes(b"")
        self.break_git_after_the_writes()
        with self.assertRaises(install.InstallError):
            do_install(target, ["claude-code"])
        self.assertEqual([entry.name for entry in target.iterdir()], [".DS_Store"])

    def test_missing_git_is_named_before_any_write(self):
        target = self.tmp / "v"
        with mock.patch.dict(os.environ, {"PATH": str(self.tmp / "no-programs")}):
            with self.assertRaises(install.InstallError) as caught:
                do_install(target, ["codex"])
        self.assertIn("git is not installed", str(caught.exception))
        self.assertFalse(target.exists())


class RemoveTreeTests(unittest.TestCase):
    def test_removes_read_only_files_at_every_depth(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name) / "git"
        (folder / "objects").mkdir(parents=True)
        for path in (folder / "HEAD", folder / "objects" / "pack.idx"):
            path.write_bytes(b"read-only\n")
            path.chmod(0o444)  # git makes its object files read-only on Windows
        install.remove_tree(folder)
        self.assertFalse(folder.exists())


class LinkDirTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.target = self.tmp / "vault" / ".agents" / "skills"
        self.link = self.tmp / "vault" / ".claude" / "skills"

    @unittest.skipIf(os.name == "nt", "off Windows the link is a symlink")
    def test_symlink_is_relative(self):
        self.target.mkdir(parents=True)
        self.link.parent.mkdir(parents=True)
        install.link_dir(self.link, self.target)
        self.assertEqual(os.readlink(self.link), "../.agents/skills")

    def test_windows_makes_a_junction(self):
        winapi = mock.MagicMock()  # _winapi exists only on Windows
        with mock.patch.object(os, "name", "nt"), mock.patch.dict(sys.modules, {"_winapi": winapi}):
            install.link_dir(self.link, self.target)
        winapi.CreateJunction.assert_called_once_with(str(self.target), str(self.link))
        self.assertFalse(self.link.exists())

    def test_junction_target_is_absolute(self):
        relative = Path(".agents") / "skills"
        expected = str(Path.cwd() / relative)  # built before the patch: Path() picks a class by os.name
        winapi = mock.MagicMock()
        with mock.patch.object(os, "name", "nt"), mock.patch.dict(sys.modules, {"_winapi": winapi}):
            install.link_dir(self.link, relative)
        self.assertEqual(winapi.CreateJunction.call_args.args[0], expected)

    def test_failed_junction_is_an_install_error(self):
        winapi = mock.MagicMock()
        winapi.CreateJunction.side_effect = OSError("access denied")
        with mock.patch.object(os, "name", "nt"), mock.patch.dict(sys.modules, {"_winapi": winapi}):
            with self.assertRaises(install.InstallError):
                install.link_dir(self.link, self.target)


class ObsidianSetupTests(unittest.TestCase):
    """The kit installs no plugin code. It sets up what Obsidian's own plugins need and hides the agent's files."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)

    def test_no_plugin_code_is_installed(self):
        pins, folder = fake_pins(self.tmp)
        target = self.tmp / "v"
        install.install(target, ["claude-code"], pinned_from=folder, pins=pins, today=TODAY)
        plugins = target / ".obsidian" / "plugins"
        found = sorted(path.relative_to(plugins).as_posix() for path in plugins.rglob("*") if path.is_file())
        self.assertEqual(found, ["obsidian-tasks-plugin/data.json"])
        for name in ("main.js", "manifest.json", "styles.css"):
            self.assertEqual(list(target.rglob(name)), [], name)

    def test_tasks_settings_are_the_templates(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        rel = Path(".obsidian") / "plugins" / "obsidian-tasks-plugin" / "data.json"
        self.assertEqual((target / rel).read_bytes(), (install.TEMPLATE / "vault" / rel).read_bytes())

    def test_tasks_settings(self):
        path = install.TEMPLATE / "vault" / ".obsidian" / "plugins" / "obsidian-tasks-plugin" / "data.json"
        settings = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(settings["taskFormat"], "dataview")
        statuses = {status["symbol"]: status for status in settings["statusSettings"]["customStatuses"]}
        self.assertEqual(statuses["w"]["type"], "ON_HOLD")
        self.assertEqual(statuses["w"]["nextStatusSymbol"], "x")

    def test_agent_files_are_hidden_in_obsidian(self):
        target = self.tmp / "v"
        do_install(target, ["codex"])
        obsidian = target / ".obsidian"
        snippet = obsidian / "snippets" / "hide-agent-files.css"
        self.assertEqual(snippet.read_bytes(), (install.TEMPLATE / "vault" / install.HIDE_SNIPPET).read_bytes())
        self.assertIn('[data-path="AGENTS.md"]', snippet.read_text(encoding="utf-8"))
        appearance = json.loads((obsidian / "appearance.json").read_text(encoding="utf-8"))
        self.assertEqual(appearance, {"enabledCssSnippets": ["hide-agent-files"]})
        app = json.loads((obsidian / "app.json").read_text(encoding="utf-8"))
        self.assertEqual(app["userIgnoreFilters"], ["AGENTS.md"])

    def test_obsidian_settings_are_installed(self):
        target = self.tmp / "v"
        do_install(target, ["claude-code"])
        obsidian = target / ".obsidian"
        app = json.loads((obsidian / "app.json").read_text(encoding="utf-8"))
        self.assertEqual(app, {"openBehavior": "file:01 Dashboard/01 Today.md", "userIgnoreFilters": ["AGENTS.md"]})
        community = json.loads((obsidian / "community-plugins.json").read_text(encoding="utf-8"))
        self.assertEqual(community, ["obsidian-tasks-plugin", "ninja-board"])  # listed, and installed by Obsidian
        core = json.loads((obsidian / "core-plugins.json").read_text(encoding="utf-8"))
        self.assertEqual(
            core,
            {
                "file-explorer": True,
                "global-search": True,
                "switcher": True,
                "graph": True,
                "backlink": True,
                "canvas": True,
                "outgoing-link": True,
                "tag-pane": True,
                "properties": True,
                "page-preview": True,
                "daily-notes": True,
                "templates": True,
                "note-composer": True,
                "command-palette": True,
                "slash-command": False,
                "editor-status": True,
                "bookmarks": True,
                "markdown-importer": False,
                "zk-prefixer": False,
                "random-note": False,
                "outline": True,
                "word-count": True,
                "slides": False,
                "audio-recorder": False,
                "workspaces": False,
                "file-recovery": True,
                "publish": False,
                "sync": True,
                "webviewer": False,
                "footnotes": False,
                "bases": True,
            },
        )


class FetchPinnedTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def test_missing_local_file_is_named(self):
        pins, folder = fake_pins(self.tmp)
        (folder / DASHBOARD_ID / "05 Guide.md").unlink()
        with self.assertRaises(install.InstallError) as caught:
            install.fetch_pinned(pins, folder, self.tmp / "dest")
        self.assertIn("05 Guide.md", str(caught.exception))

    def test_unpinned_download_is_refused(self):
        pins = {
            DASHBOARD_ID: {
                "version": "1.0.0",
                "install_to": "01 Dashboard",
                "files": {"01 Today.md": {"url": "https://example.invalid/today.md", "sha256": None}},
            }
        }
        with self.assertRaises(install.InstallError) as caught:
            install.fetch_pinned(pins, None, self.tmp / "dest")
        self.assertIn("not pinned yet", str(caught.exception))
        self.assertIn("--pinned-from", str(caught.exception))

    def test_local_unpinned_file_warns(self):
        pins, folder = fake_pins(self.tmp)
        pins[DASHBOARD_ID]["files"]["01 Today.md"]["sha256"] = None
        warnings = install.fetch_pinned(pins, folder, self.tmp / "dest")
        self.assertEqual(warnings, [f"{DASHBOARD_ID}/01 Today.md is not pinned yet"])

    @unittest.skipUnless(os.environ.get("KIT_ONLINE") == "1", "downloads from GitHub; set KIT_ONLINE=1")
    def test_online_dashboard_download(self):
        pins = install.load_pins()
        self.assertEqual(install.fetch_pinned(pins, None, self.tmp / "dest"), [])
        for name, pin in pins[DASHBOARD_ID]["files"].items():
            with self.subTest(note=name):
                data = (self.tmp / "dest" / DASHBOARD_ID / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), pin["sha256"])


class DashboardTests(unittest.TestCase):
    """The five dashboard notes come from the pinned Ninja Board release. The kit carries no copy of them."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)

    def test_install_puts_the_five_dashboards_in_the_folder_dated_today(self):
        pins, folder = fake_pins(self.tmp)
        target = self.tmp / "v"
        install.install(target, ["codex"], pinned_from=folder, pins=pins, today=TODAY)
        self.assertEqual(sorted(p.name for p in (target / "01 Dashboard").iterdir()), sorted(DASHBOARD_NAMES))
        for name in DASHBOARD_NAMES:
            with self.subTest(note=name):
                fixture = (folder / DASHBOARD_ID / name).read_bytes()
                expected = fixture.replace(b"created: 2020-01-01\n", b"created: 2026-10-16\n")
                self.assertEqual((target / "01 Dashboard" / name).read_bytes(), expected)
        self.assertFalse((target / ".obsidian" / "plugins" / DASHBOARD_ID).exists())

    def test_dashboard_checksum_mismatch_writes_nothing(self):
        pins, folder = fake_pins(self.tmp)
        (folder / DASHBOARD_ID / "02 Week.md").write_bytes(b"corrupted\n")
        target = self.tmp / "v"
        with self.assertRaises(install.InstallError) as caught:
            install.install(target, ["codex"], pinned_from=folder, pins=pins, today=TODAY)
        self.assertIn("02 Week.md", str(caught.exception))
        self.assertFalse(target.exists())

    def test_a_pins_entry_without_install_to_is_refused_and_writes_nothing(self):
        pins, folder = fake_pins(self.tmp)
        pins["obsidian-tasks-plugin"] = {  # an entry from an old pins.json: plugin files, not notes
            "version": "8.5.0",
            "in_directory": True,
            "files": {"main.js": {"url": "https://example.invalid/main.js", "sha256": None}},
        }
        target = self.tmp / "v"
        with self.assertRaises(install.InstallError) as caught:
            install.install(target, ["codex"], pinned_from=folder, pins=pins, today=TODAY)
        self.assertIn("obsidian-tasks-plugin", str(caught.exception))
        self.assertIn("install_to", str(caught.exception))
        self.assertFalse(target.exists())

    def test_kit_template_carries_no_copy_of_the_dashboards(self):
        self.assertEqual(list((install.TEMPLATE / "vault" / "01 Dashboard").glob("*.md")), [])

    def test_pinned_dashboards_come_from_the_ninja_board_release(self):
        pins = install.load_pins()
        self.assertEqual(list(pins), [DASHBOARD_ID])  # the kit pins notes only: Obsidian installs the plugins
        entry = pins[DASHBOARD_ID]
        self.assertEqual(entry["version"], "1.0.2")
        self.assertEqual(sorted(entry), ["files", "install_to", "version"])
        self.assertEqual(entry["install_to"], "01 Dashboard")
        self.assertEqual(sorted(entry["files"]), sorted(DASHBOARD_NAMES))
        for name, pin in entry["files"].items():
            with self.subTest(note=name):
                url = "https://raw.githubusercontent.com/AlexSendula/ninja-board/1.0.2/sample-vault/01%20Dashboard/"
                self.assertEqual(pin["url"], url + name.replace(" ", "%20"))
                self.assertRegex(pin["sha256"], r"^[0-9a-f]{64}$")


class DownloadTests(unittest.TestCase):
    def test_only_https_is_downloaded(self):
        for url in ("file:///etc/hosts", "ftp://example.invalid/kit.zip", "http://example.invalid/main.js"):
            with self.subTest(url=url), mock.patch.object(install.urllib.request, "urlopen") as urlopen:
                with self.assertRaises(install.InstallError) as caught:
                    install.download(url)
                self.assertIn(url, str(caught.exception))
                urlopen.assert_not_called()

    def test_https_is_downloaded(self):
        with mock.patch.object(install.urllib.request, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"data"
            self.assertEqual(install.download("https://example.invalid/main.js"), b"data")


class KitFilesTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        isolate_git(self, self.tmp)
        self.vault = self.tmp / "v"
        do_install(self.vault, list(install.TOOLS))

    def test_kit_files_list(self):
        listed = install.read_kit_files(self.vault)
        for rel, digest in listed.items():
            with self.subTest(file=rel):
                self.assertEqual(hashlib.sha256((self.vault / rel).read_bytes()).hexdigest(), digest)
        self.assertIn("AGENTS.md", listed)
        self.assertIn(".agents/skills/brain/SKILL.md", listed)
        self.assertIn(".claude/CLAUDE.md", listed)
        self.assertIn(install.HIDE_SNIPPET, listed)
        self.assertNotIn("CLAUDE.md", listed)  # the 0.1.x place; the kit no longer writes it
        self.assertNotIn("99 System/config.md", listed)
        self.assertNotIn("01 Dashboard/01 Today.md", listed)

    def test_kit_files_record_the_claude_file_and_the_snippet_with_their_checksums(self):
        listed = install.read_kit_files(self.vault)
        claude = hashlib.sha256(CLAUDE_FILE.encode("utf-8")).hexdigest()
        snippet = hashlib.sha256((install.TEMPLATE / "vault" / install.HIDE_SNIPPET).read_bytes()).hexdigest()
        self.assertEqual(listed[".claude/CLAUDE.md"], claude)
        self.assertEqual(listed[install.HIDE_SNIPPET], snippet)
        tools = list(install.TOOLS)  # what update expects is what install recorded
        self.assertEqual(install.kit_file_shas(tools, install.placeholder_values(TODAY, tools)), listed)

    def test_kit_files_format(self):
        raw = (self.vault / install.KIT_FILES).read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        paths = []
        for line in raw.decode("utf-8").splitlines():
            self.assertRegex(line, r"^[0-9a-f]{64}  \S")
            paths.append(line.split("  ", 1)[1])
        self.assertEqual(paths, sorted(paths))

    def test_kit_files_are_the_kit_files(self):
        vscode = self.tmp / "vs"
        do_install(vscode, ["vscode"])
        for vault, tools in ((self.vault, list(install.TOOLS)), (vscode, ["vscode"])):
            with self.subTest(tools=tools):
                self.assertEqual(sorted(install.read_kit_files(vault)), sorted(install.kit_system_files(tools)))
        self.assertNotIn("CLAUDE.md", install.read_kit_files(vscode))

    def test_kept_aside_file_is_not_adopted(self):
        mine = self.vault / ".agents" / "skills" / "brain" / "SKILL.md.mine"
        mine.write_text("my edits\n", encoding="utf-8")
        tools = list(install.TOOLS)
        install.write_kit_files(self.vault, install.kit_file_shas(tools, install.placeholder_values(TODAY, tools)))
        self.assertTrue(mine.is_file())
        self.assertNotIn(".agents/skills/brain/SKILL.md.mine", install.read_kit_files(self.vault))


class SavedVersionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.gitconfig = isolate_git(self, self.tmp)
        self.vault = self.tmp / "v"

    def test_first_saved_version(self):
        do_install(self.vault, ["claude-code"])
        self.assertEqual(git_run(self.vault, "log", "--format=%s").stdout, f"Installed by second-brain-setup {install.kit_version()}\n")
        self.assertEqual(git_run(self.vault, "status", "--porcelain").stdout, "")
        self.assertTrue((self.vault / ".memory" / "MEMORY.md").is_file())
        self.assertEqual(git_run(self.vault, "ls-files", ".memory").stdout, "")

    def test_local_identity_without_global(self):
        do_install(self.vault, ["codex"])
        self.assertEqual(git_run(self.vault, "config", "user.name").stdout, "second-brain\n")
        self.assertEqual(git_run(self.vault, "config", "user.email").stdout, "second-brain@localhost\n")
        self.assertEqual(self.gitconfig.read_bytes(), b"")

    def test_global_email_without_name_fills_only_the_name(self):
        self.gitconfig.write_text("[user]\n\temail = global@example.invalid\n", encoding="utf-8")
        do_install(self.vault, ["codex"])
        self.assertEqual(git_run(self.vault, "config", "--local", "--get", "user.name").stdout, "second-brain\n")
        self.assertEqual(git_run(self.vault, "config", "--local", "--get", "user.email").returncode, 1)
        self.assertEqual(git_run(self.vault, "config", "user.email").stdout, "global@example.invalid\n")

    def test_existing_identity_is_kept(self):
        self.gitconfig.write_text(
            "[user]\n\tname = Global Person\n\temail = global@example.invalid\n", encoding="utf-8"
        )
        do_install(self.vault, ["codex"])
        self.assertEqual(git_run(self.vault, "config", "user.name").stdout, "Global Person\n")
        for key in ("user.name", "user.email"):
            with self.subTest(key=key):
                self.assertEqual(git_run(self.vault, "config", "--local", "--get", key).returncode, 1)


class PlaceholderTests(unittest.TestCase):
    def test_unfilled_placeholder_is_refused(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = Path(tmp.name) / "src"
        src.mkdir()
        (src / "note.md").write_text("created: {{when}}\n", encoding="utf-8")
        with self.assertRaises(install.InstallError) as caught:
            install.copy_template(src, Path(tmp.name) / "dest", {"today": "2026-10-16"})
        self.assertIn("note.md", str(caught.exception))
        self.assertIn("{{when}}", str(caught.exception))


class WriteErrorTests(unittest.TestCase):
    def test_write_failure_is_one_line_and_returns_1(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        isolate_git(self, Path(tmp.name))
        blocker = Path(tmp.name) / "file"
        blocker.write_text("not a folder", encoding="utf-8")
        with mock.patch.object(install, "load_pins", return_value={}):  # keep the test offline
            code, err = run_main("install", str(blocker / "v"), "--tools", "codex")
        self.assertEqual(code, 1)
        lines = err.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("install.py: "))


if __name__ == "__main__":
    unittest.main()
