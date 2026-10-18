# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Install and update a second-brain Obsidian vault. Standard library only."""

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NoReturn

KIT_ROOT = Path(__file__).resolve().parent
TEMPLATE = KIT_ROOT / "template"
SKILLS = KIT_ROOT / "skills"
TOOLS = ("claude-code", "codex", "vscode")
FOLDERS = (
    "01 Dashboard",
    "02 Inbox",
    "03 Projects",
    "04 Areas",
    "05 People",
    "06 Conversations",
    "07 Resources",
    "08 Weeks",
    "09 Logs",
    "10 Archive",
    "99 System",
)
IGNORABLE_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})
UPDATE_SOURCE = "https://github.com/AlexSendula/second-brain-setup"
PLACEHOLDER = re.compile(r"\{\{\w+\}\}")
KIT_FILES = ".agents/kit-files.txt"
CONFIG = "99 System/config.md"
CLAUDE_SKILLS = ".claude/skills"  # the link Claude Code reads; it points at .agents/skills
HIDE_SNIPPET = ".obsidian/snippets/hide-agent-files.css"  # hides AGENTS.md from Obsidian's file list
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)  # CRLF too: Windows editors save that way


class InstallError(Exception):
    """A failure the user should see as one line. main() prints it and returns 1."""


class _Parser(argparse.ArgumentParser):
    """Usage errors raise InstallError instead of printing usage and exiting with 2."""

    def error(self, message: str) -> NoReturn:
        raise InstallError(message)


def kit_version() -> str:
    return (KIT_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def parse_tools(value: str) -> list[str]:
    if not value:
        raise InstallError("--tools needs at least one tool id")
    tools = value.split(",")
    if tools == ["none"]:
        return []  # no tool files: for an agent tool the kit does not support
    if "none" in tools:
        raise InstallError("--tools none cannot be combined with other tool ids")
    for tool in tools:
        if tool not in TOOLS:
            raise InstallError(f"unknown tool '{tool}' (choose from {', '.join(TOOLS)})")
    if len(set(tools)) != len(tools):
        raise InstallError("--tools lists a tool twice")
    return tools


def is_empty_dir(path: Path) -> bool:
    """True when the folder is missing or holds only files the OS adds by itself."""
    if not path.exists():
        return True
    if not path.is_dir():
        return False
    return all(entry.name in IGNORABLE_FILES for entry in path.iterdir())


def placeholder_values(today: date, tools: list[str]) -> dict[str, str]:
    """The values for {{name}} placeholders. Install and update both fill templates with these."""
    return {
        "today": today.isoformat(),
        "system_version": kit_version(),
        "update_source": UPDATE_SOURCE,
        "agent_tools": "[" + ", ".join(tools) + "]",
    }


def render_text(text: str, name: str, values: dict[str, str]) -> str:
    """Fill {{name}} placeholders. A placeholder left over is an InstallError."""
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    left = PLACEHOLDER.search(text)
    if left:
        raise InstallError(f"{name} has an unfilled placeholder {left.group(0)}")
    return text


def copy_template(src: Path, dest: Path, values: dict[str, str]) -> list[Path]:
    """Copy a tree. Fill {{name}} placeholders in .md and .json files. Return the paths written, relative to dest."""
    written = []
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in (".md", ".json"):
            text = render_text(path.read_text(encoding="utf-8"), rel.as_posix(), values)
            out.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(path, out)
        written.append(rel)
    return written


def copy_skills(dest: Path) -> None:
    """Copy every kit skill into dest byte for byte. Skills are not placeholder-filled."""
    for path in sorted(SKILLS.rglob("*")):
        if path.is_file():
            out = dest / path.relative_to(SKILLS)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, out)


def link_dir(link: Path, target: Path) -> None:
    """Make link lead to the folder target: a relative symlink, or a junction on Windows."""
    if os.name == "nt":
        import _winapi  # Windows only; a junction needs an absolute target
        try:
            _winapi.CreateJunction(str(target.absolute()), str(link))
        except OSError as error:
            raise InstallError(f"could not make the junction {link}: {error}") from error
    else:
        link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=True)


def kit_system_files(tools: list[str]) -> dict[str, Path]:
    """The files an install writes that updates may replace: vault-relative POSIX path -> kit source file."""
    return {
        "AGENTS.md": TEMPLATE / "vault" / "AGENTS.md",
        HIDE_SNIPPET: TEMPLATE / "vault" / HIDE_SNIPPET,
        **_skill_files(),
        **_tool_files(tools),
    }


def _skill_files() -> dict[str, Path]:
    files = {}
    for folder in sorted(SKILLS.glob("brain*")):
        if folder.is_dir():
            for source in sorted(folder.rglob("*")):
                if source.is_file():
                    files[f".agents/skills/{source.relative_to(SKILLS).as_posix()}"] = source
    return files


def _tool_files(tools: list[str]) -> dict[str, Path]:
    files = {}
    for tool in tools:
        tool_dir = TEMPLATE / "tools" / tool
        if tool_dir.is_dir():  # codex has no files
            for source in sorted(tool_dir.rglob("*")):
                if source.is_file():
                    files[source.relative_to(tool_dir).as_posix()] = source
    return files


def kit_file_shas(tools: list[str], values: dict[str, str]) -> dict[str, str]:
    """Vault-relative path -> sha256 of the content the kit writes there, as install and update render it."""
    return {rel: _sha256(_installed_bytes(rel, source, values)) for rel, source in kit_system_files(tools).items()}


def write_kit_files(vault: Path, shas: dict[str, str]) -> None:
    """Write KIT_FILES: one line per kit path, sorted, with the sha256 of what the kit wrote there.

    The hashes are the kit's, never the vault's, so an edit the person keeps is never recorded as installed.
    The paths come from kit_system_files, never from a glob of the vault, so a file the person keeps
    aside (such as SKILL.md.mine) is never adopted as a kit file.
    """
    lines = [f"{shas[rel]}  {rel}\n" for rel in sorted(shas)]
    (vault / KIT_FILES).write_text("".join(lines), encoding="utf-8", newline="\n")


# CLAUDE.md is the 0.1.x place for Claude Code's file. The kit no longer writes it, but a 0.1.x vault records it,
# and an update removes it from there when the person did not edit it.
SYSTEM_FILES = frozenset({
    "AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md", ".claude/settings.json", HIDE_SNIPPET, ".vscode/settings.json",
})


def _inside_vault(vault: Path, rel: str) -> bool:
    """True for a relative path with no .. part that resolves inside the vault."""
    if Path(rel).is_absolute() or ".." in re.split(r"[\\/]", rel):
        return False
    return (vault / rel).resolve().is_relative_to(vault.resolve())


def _is_system_path(rel: str) -> bool:
    """True for a file the kit installs and may replace or remove: a system file, or a file in a brain skill folder."""
    parts = rel.split("/")
    in_brain_skill = len(parts) >= 4 and parts[:2] == [".agents", "skills"] and parts[2].startswith("brain")
    return rel in SYSTEM_FILES or in_brain_skill


def read_kit_files(vault: Path, *, warn: bool = True) -> dict[str, str]:
    """Path -> sha256, as write_kit_files wrote them. Only system-file paths inside the vault are kept; any other
    recorded path is never replaced or removed, and a warning names it."""
    listed = {}
    for line in (vault / KIT_FILES).read_text(encoding="utf-8").splitlines():
        digest, _, rel = line.partition("  ")
        if _inside_vault(vault, rel) and _is_system_path(rel):
            listed[rel] = digest
        elif warn:
            print(f"install.py: warning: {KIT_FILES} lists {rel}, which is not a kit system file inside the vault; "
                  "ignored", file=sys.stderr)
    return listed


def _run_git(vault: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:  # the environment is os.environ, so tests can isolate the git config
        return subprocess.run(
            ["git", *args], cwd=vault, capture_output=True, encoding="utf-8", errors="replace", check=False
        )
    except OSError as error:  # git is not installed
        raise InstallError(f"could not run git: {error}") from error


def git(vault: Path, *args: str) -> str:
    """Run git in the vault and return its stdout. A failed command raises InstallError with git's stderr."""
    result = _run_git(vault, *args)
    if result.returncode != 0:
        raise InstallError(f"git failed in {vault}: {result.stderr.strip()}")
    return result.stdout


def load_pins(path: Path = KIT_ROOT / "pins.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def download(url: str) -> bytes:
    if not url.startswith("https://"):  # urlopen also reads file:// and ftp://
        raise InstallError(f"could not download {url}: only https:// links are downloaded")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read()
    except OSError as error:  # URLError and timeouts are OSError too
        raise InstallError(f"could not download {url}: {error}") from error


def fetch_pinned(pins: dict, pinned_from: Path | None, dest: Path) -> list[str]:
    """Write each pinned file to dest/<id>/<file>, checked against its sha256. Return warning lines.

    pinned_from is a local folder laid out as <id>/<file>, for developers and tests. Without it, each file is
    downloaded from its pinned url.
    """
    warnings = []
    for pin_id, pin in pins.items():
        for name, file_pin in pin["files"].items():
            label = f"{pin_id}/{name}"
            if pinned_from is None:
                if file_pin["sha256"] is None:
                    raise InstallError(f"{label} is not pinned yet; use --pinned-from")
                data = download(file_pin["url"])
            else:
                source = pinned_from / pin_id / name
                if not source.is_file():
                    raise InstallError(f"{label} is missing from {pinned_from}")
                data = source.read_bytes()
            if file_pin["sha256"] is None:
                warnings.append(f"{label} is not pinned yet")
            elif hashlib.sha256(data).hexdigest() != file_pin["sha256"]:
                raise InstallError(f"{label} does not match its pinned sha256")
            out = dest / pin_id / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
    return warnings


def _probe_git() -> None:
    """Run git before the first write, so a missing git leaves no half-built vault."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise InstallError("git is not installed or does not run. Install git, then run install again.") from error


def remove_tree(path: Path) -> None:
    """Remove a folder with everything in it. Windows makes git's object files read-only, so a file that refuses to
    go has its read-only bit cleared, and the removal of that file is tried once more."""

    def clear_read_only_and_retry(func, failed: str, _error: BaseException) -> None:
        os.chmod(failed, stat.S_IWRITE)
        func(failed)

    shutil.rmtree(path, onexc=clear_read_only_and_retry)


def _remove(path: Path) -> None:
    """Remove a file, a folder with everything in it, or a link. A Windows junction is removed as a link only."""
    if os.path.isjunction(path):
        os.rmdir(path)  # a junction is a folder to Windows: rmdir removes only the link
    elif path.is_dir() and not path.is_symlink():
        remove_tree(path)
    else:
        path.unlink()


def _undo_install(target: Path, created: bool) -> None:
    """Remove what a failed install wrote. A folder that was there before stays, holding only its OS files."""
    if not target.is_dir():
        return
    for entry in target.iterdir():
        if created or entry.name not in IGNORABLE_FILES:
            _remove(entry)
    if created:
        target.rmdir()


def install(target: Path, tools: list[str], *, pinned_from: Path | None, pins: dict, today: date) -> None:
    if not is_empty_dir(target):
        raise InstallError(f"{target} is not an empty folder; choose a new or empty one")
    sources = _note_sources(pins)
    _probe_git()
    values = placeholder_values(today, tools)
    # Fetch and check every pinned note before the first write, so a failure leaves the target untouched.
    with tempfile.TemporaryDirectory() as staging:
        staged = Path(staging)
        for warning in fetch_pinned(pins, pinned_from, staged):
            print(f"install.py: warning: {warning}", file=sys.stderr)
        created = not target.exists()
        try:
            copy_template(TEMPLATE / "vault", target, values)
            for tool in tools:
                tool_dir = TEMPLATE / "tools" / tool
                if tool_dir.is_dir():  # codex has no files
                    copy_template(tool_dir, target, values)
            for rel, (pin_id, name) in sources.items():  # each pinned note goes into its folder, dated today
                note = target / rel
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_bytes(_dated_note((staged / pin_id / name).read_bytes(), rel, values["today"]))
            copy_skills(target / ".agents" / "skills")
            if "claude-code" in tools:  # Claude Code reads only .claude/skills
                link_dir(target / ".claude" / "skills", target / ".agents" / "skills")
            # Made in code, not in the template: the vault .gitignore hides .memory/ from git.
            (target / ".memory").mkdir(parents=True, exist_ok=True)
            (target / ".memory" / "MEMORY.md").touch()
            for name in FOLDERS:
                folder = target / name
                folder.mkdir(parents=True, exist_ok=True)
                if not any(folder.iterdir()):
                    (folder / ".gitkeep").touch()
            write_kit_files(target, kit_file_shas(tools, values))
            git(target, "init", "-q", "-b", "main")
            for key, value in (("user.name", "second-brain"), ("user.email", "second-brain@localhost")):
                # Filled for this vault only, and only where the person has no value of their own.
                if not _run_git(target, "config", key).stdout.strip():
                    git(target, "config", key, value)
            git(target, "add", "-A")
            # commit.gpgsign=false: a signing setup must not hang the install.
            message = f"Installed by second-brain-setup {kit_version()}"
            git(target, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        except BaseException:
            with contextlib.suppress(OSError):  # the error below is the one to show; SETUP.md covers any leftovers
                _undo_install(target, created)
            raise


@dataclass
class Change:
    """One step of an update. note is printed after the path and may be empty."""

    action: str  # add, replace, remove, keep-aside, dashboard, tool or version
    path: str
    note: str = ""
    seen: str = ""  # the sha of the vault file when the plan was made; "" when it was missing


def read_config(vault: Path) -> str:
    return (vault / CONFIG).read_bytes().decode("utf-8")


def config_value(text: str, key: str) -> str:
    """The raw value of a `key: value` line in config's frontmatter."""
    match = FRONTMATTER.match(text)
    lines = match.group(1).splitlines() if match else []
    for line in lines:
        name, _, value = line.partition(":")
        if name == key:
            return value.strip()
    raise InstallError(f"{CONFIG} has no {key} line in its frontmatter")


def config_tools(text: str) -> list[str]:
    value = config_value(text, "agent_tools")
    if not (value.startswith("[") and value.endswith("]")):
        raise InstallError(f"{CONFIG}: agent_tools must be a list, like [claude-code, codex]")
    tools = [tool.strip() for tool in value[1:-1].split(",") if tool.strip()]
    for tool in tools:  # the id names a template folder, so only a known id may pass
        if tool not in TOOLS:
            raise InstallError(f"{CONFIG}: agent_tools names an unknown tool '{tool}' (choose from {', '.join(TOOLS)})")
    return tools


def set_frontmatter_line(text: str, key: str, value: str, name: str = CONFIG) -> str:
    """Replace the frontmatter line `key: ...`. Every other byte of the file stays as it is. name is for the errors."""
    match = FRONTMATTER.match(text)
    if match is None:
        raise InstallError(f"{name} has no frontmatter")
    block, count = re.subn(rf"(?m)^{key}:[^\r\n]*", lambda _: f"{key}: {value}", match.group(1))
    if count != 1:
        raise InstallError(f"{name} needs exactly one {key} line in its frontmatter")
    return text[: match.start(1)] + block + text[match.end(1) :]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _installed_bytes(rel: str, source: Path, values: dict[str, str]) -> bytes:
    """What install writes for a kit file: skills are copied as they are, other .md and .json files are filled."""
    if source.is_relative_to(SKILLS) or source.suffix not in (".md", ".json"):
        return source.read_bytes()
    return render_text(source.read_text(encoding="utf-8"), rel, values).encode("utf-8")


def _aside_path(path: Path) -> Path:
    """The first free name beside path: path.mine, then path.mine2, path.mine3, and so on."""
    candidate = path.with_name(path.name + ".mine")
    count = 2
    while os.path.lexists(candidate):
        candidate = path.with_name(f"{path.name}.mine{count}")
        count += 1
    return candidate


def _note_sources(pins: dict) -> dict[str, tuple[str, str]]:
    """Vault-relative path -> (pins id, file name) for each pinned note. Every pins entry is a set of notes, so an
    entry without install_to, such as one from an old pins.json, is an InstallError."""
    sources = {}
    for pin_id, pin in pins.items():
        if "install_to" not in pin:
            raise InstallError(f"pins entry '{pin_id}' has no install_to; every entry must be a set of notes")
        for name in pin["files"]:
            sources[f"{pin['install_to']}/{name}"] = (pin_id, name)
    return sources


def _dated_note(data: bytes, rel: str, day: str) -> bytes:
    """A pinned note as the kit writes it: its created line set to day. Nothing else in the note changes."""
    return set_frontmatter_line(data.decode("utf-8"), "created", day, rel).encode("utf-8")


def _has_own_repo(vault: Path) -> bool:
    """True when git's top folder for the vault is the vault itself. An empty .git folder, or none, is not one."""
    if not vault.is_dir():
        return False
    result = _run_git(vault, "rev-parse", "--show-toplevel")
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == vault.resolve()


def _add_note(vault: Path, rel: str, listed: dict[str, str]) -> str:
    """What a 0.1.x person needs to know about a file that is new to their vault. The 0.1.x skill, which runs
    the update, only knows to read this list aloud, so the hints live here."""
    if rel == HIDE_SNIPPET:
        return "turn it on in Settings → Appearance → CSS snippets"
    old = vault / "CLAUDE.md"
    if rel == ".claude/CLAUDE.md" and old.is_file() and listed.get("CLAUDE.md") != _sha256(old.read_bytes()):
        return "your edited CLAUDE.md stays; move your edits here"
    return ""


def plan_update(vault: Path, *, tools: list[str] | None, pins: dict) -> list[Change]:
    """Decide what an update does. Writes nothing and fetches nothing."""
    # Without its own repository, git would save the enclosing repository's whole working tree and index.
    if not _has_own_repo(vault):
        raise InstallError(f"{vault} has no git repository of its own")
    if not (vault / CONFIG).is_file() or not (vault / KIT_FILES).is_file():
        raise InstallError(f"{vault} is not a second-brain vault")
    config = read_config(vault)
    tools_now = config_tools(config)
    version_now = config_value(config, "system_version").strip('"')
    added = [tool for tool in tools or [] if tool not in tools_now]
    new_tools = tools_now + added
    values = placeholder_values(date.today(), new_tools)
    expected = kit_file_shas(new_tools, values)  # N: the sha of what the new kit writes, per path
    listed = read_kit_files(vault)  # R: the sha the kit wrote last time, per path

    changes = []
    if version_now != kit_version():
        changes.append(Change("version", CONFIG, f"{version_now} → {kit_version()}"))
    changes += [Change("tool", tool, "added to agent_tools") for tool in added]
    for rel in sorted(expected):
        target = vault / rel
        if not target.exists():
            changes.append(Change("add", rel, _add_note(vault, rel, listed)))
            continue
        vault_sha = _sha256(target.read_bytes())  # V
        if vault_sha == expected[rel] or listed.get(rel) == expected[rel]:
            continue  # already the kit's content, or the kit did not change it: the person's edit stays
        if listed.get(rel) == vault_sha:  # unedited (V == R) and the kit changed it (N != R)
            changes.append(Change("replace", rel, seen=vault_sha))
        else:  # edited (V != R) and the kit changed it (N != R)
            changes.append(Change("keep-aside", rel, f"kept as {_aside_path(target).name}", seen=vault_sha))
    for rel in sorted(listed):  # only files the kit installed; an edited one is left alone
        target = vault / rel
        if rel not in expected and target.is_file() and _sha256(target.read_bytes()) == listed[rel]:
            note = "moved to .claude/CLAUDE.md" if rel == "CLAUDE.md" else ""
            changes.append(Change("remove", rel, note, seen=listed[rel]))
    if "claude-code" in new_tools and not os.path.lexists(vault / CLAUDE_SKILLS):
        changes.append(Change("add", CLAUDE_SKILLS, "link to .agents/skills"))
    for rel in sorted(_note_sources(pins)):  # the pinned notes the vault lacks; an existing note is never rewritten
        if not (vault / rel).exists():
            changes.append(Change("dashboard", rel))
    return changes


def _remove_if_unchanged(target: Path, seen: str) -> None:
    """Remove a file the kit no longer ships, unless the person changed it since the plan. Then it stays."""
    if target.is_file() and _sha256(target.read_bytes()) == seen:
        target.unlink()


def _write_checked(target: Path, new: bytes, change: Change) -> None:
    """Write a planned file, unless the person's file changed since the plan. Their file goes aside instead."""
    current = target.read_bytes() if target.is_file() else None
    if current == new:
        return  # already the kit's content
    if change.action == "dashboard" and current is not None:
        return  # an existing dashboard is never rewritten
    if change.action == "replace" and current is not None and _sha256(current) == change.seen:
        target.write_bytes(new)  # unchanged since the plan
        return
    if current is not None:  # edited since the plan, or planned as a keep-aside
        target.rename(_aside_path(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as file:  # exclusive: a file that appears now is never overwritten
        file.write(new)


def _recorded(vault: Path, expected: dict[str, str], listed: dict[str, str]) -> dict[str, str]:
    """kit-files after an update: the sha of what the kit wrote, or the previous sha for a file left alone."""
    records = {}
    for rel, new_sha in expected.items():
        target = vault / rel
        if target.is_file() and _sha256(target.read_bytes()) == new_sha:
            records[rel] = new_sha
        elif rel in listed:  # left alone: the kit's last record stands, never the person's edit
            records[rel] = listed[rel]
    for rel, previous in listed.items():
        if rel not in expected and (vault / rel).is_file():  # no longer in the kit, and left alone
            records[rel] = previous
    return records


def apply_update(vault: Path, changes: list[Change], *, pinned_from: Path | None, pins: dict) -> None:
    """Write what plan_update chose. Planned notes are fetched before the first write. Each file is checked
    again just before it is written or removed, so an edit made since the plan is kept aside or left alone,
    never overwritten. An update never reads or writes .obsidian/plugins: Obsidian owns the plugins."""
    tools_added = [change.path for change in changes if change.action == "tool"]
    tools = config_tools(read_config(vault)) + tools_added
    values = placeholder_values(date.today(), tools)
    wanted = kit_system_files(tools)
    listed = read_kit_files(vault, warn=False)  # plan_update has already warned about any path it ignored
    contents = {}
    for change in changes:
        if change.action in ("add", "replace", "keep-aside") and change.path != CLAUDE_SKILLS:
            contents[change.path] = _installed_bytes(change.path, wanted[change.path], values)

    with tempfile.TemporaryDirectory() as staging:
        staged = Path(staging)
        sources = _note_sources(pins)
        dashboards = {}  # every note is built before the first write, so a bad pin writes no note at all
        if any(change.action == "dashboard" for change in changes):  # all pinned files are fetched and checked
            for warning in fetch_pinned(pins, pinned_from, staged):
                print(f"install.py: warning: {warning}", file=sys.stderr)
        for change in changes:
            if change.action == "dashboard":
                pin_id, name = sources[change.path]
                data = (staged / pin_id / name).read_bytes()
                dashboards[change.path] = _dated_note(data, change.path, values["today"])
        for change in changes:
            target = vault / change.path
            if change.action == "remove":
                _remove_if_unchanged(target, change.seen)
            elif change.path == CLAUDE_SKILLS:
                if not os.path.lexists(target):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    link_dir(target, vault / ".agents" / "skills")
            elif change.action == "dashboard":  # an existing note is kept; a missing one is created exclusively
                _write_checked(target, dashboards[change.path], change)
            elif change.path in contents:
                _write_checked(target, contents[change.path], change)

    version_changed = any(change.action == "version" for change in changes)
    if version_changed or tools_added:
        config = read_config(vault)  # read again: the person may have changed other lines since the plan
        if version_changed:
            config = set_frontmatter_line(config, "system_version", f'"{kit_version()}"')
        if tools_added:
            config = set_frontmatter_line(config, "agent_tools", f"[{', '.join(tools)}]")
        (vault / CONFIG).write_bytes(config.encode("utf-8"))
    write_kit_files(vault, _recorded(vault, kit_file_shas(tools, values), listed))


def _save(vault: Path, message: str) -> None:
    """Commit everything in the vault if anything changed. A saved version is how an update is undone."""
    git(vault, "add", "-A")
    if git(vault, "status", "--porcelain").strip():
        git(vault, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)


def update(vault: Path, dry_run: bool, tools: list[str] | None, pinned_from: Path | None) -> None:
    pins = load_pins()
    changes = plan_update(vault, tools=tools, pins=pins)
    if not changes:
        print("already up to date")
        print("migration: none")
        return
    for change in changes:
        print("  ".join(part for part in (change.action, change.path, change.note) if part))
    print("migration: none")
    if dry_run:
        return
    version = kit_version()
    _save(vault, f"Saved before update to {version}")
    apply_update(vault, changes, pinned_from=pinned_from, pins=pins)
    _save(vault, f"Updated to second-brain-setup {version}")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="install.py", description="Install or update a second-brain Obsidian vault.")
    commands = parser.add_subparsers(dest="command", required=True)
    pinned_help = "developer flag: a local folder laid out as <id>/<file>, read instead of downloading"

    create = commands.add_parser("install", help="create a new vault")
    create.add_argument("folder", type=Path)
    create.add_argument("--tools", help=f"comma-separated tool ids: {', '.join(TOOLS)}")
    create.add_argument("--pinned-from", type=Path, help=pinned_help)

    refresh = commands.add_parser("update", help="update an existing vault")
    refresh.add_argument("vault", type=Path)
    refresh.add_argument("--dry-run", action="store_true")
    refresh.add_argument("--tools", help=f"comma-separated tool ids: {', '.join(TOOLS)}")
    refresh.add_argument("--pinned-from", type=Path, help=pinned_help)
    return parser


def _utf8_output() -> None:
    """The notes use arrows and accents; a Windows pipe with a narrow code page must not crash on them."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):  # io.StringIO has none, and tests redirect to it
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _utf8_output()
    try:
        args = build_parser().parse_args(argv)
        pinned_from = args.pinned_from.expanduser() if args.pinned_from is not None else None
        if args.command == "install":
            if args.tools is None:
                raise InstallError("install needs --tools (e.g. --tools claude-code)")
            install(
                args.folder.expanduser(),
                parse_tools(args.tools),
                pinned_from=pinned_from,
                pins=load_pins(),
                today=date.today(),
            )
        else:
            tools = parse_tools(args.tools) if args.tools is not None else None
            update(args.vault.expanduser(), args.dry_run, tools, pinned_from)
    except (InstallError, OSError) as error:
        print(f"install.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
