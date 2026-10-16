"""Shared test helpers. Importable from the tests as `from helpers import ...`."""

import hashlib
import os
from pathlib import Path

PLUGIN_IDS = ("obsidian-tasks-plugin", "ninja-board")
PLUGIN_FILES = ("main.js", "manifest.json", "styles.css")
DASHBOARD_ID = "ninja-board-dashboards"
DASHBOARD_NAMES = ("01 Today.md", "02 Week.md", "03 Projects.md", "04 Backlog.md", "05 Guide.md")


def isolated_git_env(tmp: Path) -> dict[str, str]:
    """Environment for git calls that ignores the user's global and system git config."""
    empty = tmp / "empty-gitconfig"
    empty.touch()
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = str(empty)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def fake_dashboard(name: str) -> bytes:
    """A small dashboard note: frontmatter with a created line, then a base block."""
    text = (
        "---\n"
        "type: note\n"
        "created: 2020-01-01\n"
        "---\n"
        "\n"
        "```base\n"
        "views:\n"
        "  - type: fake-view\n"
        f"    name: {name}\n"
        "```\n"
    )
    return text.encode("utf-8")


def fake_plugins(tmp: Path) -> tuple[dict, Path]:
    """Small fake plugin files and fake dashboard notes in tmp/plugins-from. Return pins whose sha256 match them, and
    that folder. The dashboard entry has install_to, like the real pin: its notes are not plugin files."""
    folder = tmp / "plugins-from"
    pins = {}
    for plugin_id in PLUGIN_IDS:
        files = {}
        for name in PLUGIN_FILES:
            data = f"fake {plugin_id} {name}\n".encode("utf-8")
            files[name] = _write_fake(folder / plugin_id / name, data, f"https://example.invalid/{plugin_id}/{name}")
        pins[plugin_id] = {"version": "0.0.0", "in_directory": True, "files": files}
    notes = {}
    for name in DASHBOARD_NAMES:
        url = f"https://example.invalid/{DASHBOARD_ID}/{name.replace(' ', '%20')}"
        notes[name] = _write_fake(folder / DASHBOARD_ID / name, fake_dashboard(name), url)
    pins[DASHBOARD_ID] = {"version": "0.0.0", "in_directory": False, "install_to": "01 Dashboard", "files": notes}
    return pins, folder


def _write_fake(path: Path, data: bytes, url: str) -> dict:
    """Write one fake file and return its pin: the url and the sha256 of the bytes written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"url": url, "sha256": hashlib.sha256(data).hexdigest()}
