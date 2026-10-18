"""Shared test helpers. Importable from the tests as `from helpers import ...`."""

import hashlib
import os
from pathlib import Path

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


def fake_pins(tmp: Path) -> tuple[dict, Path]:
    """Fake dashboard notes in tmp/pinned-from. Return pins whose sha256 match them, and that folder.
    The entry has install_to, like the real pin: every pins entry is a set of notes."""
    folder = tmp / "pinned-from"
    notes = {}
    for name in DASHBOARD_NAMES:
        url = f"https://example.invalid/{DASHBOARD_ID}/{name.replace(' ', '%20')}"
        notes[name] = _write_fake(folder / DASHBOARD_ID / name, fake_dashboard(name), url)
    return {DASHBOARD_ID: {"version": "0.0.0", "install_to": "01 Dashboard", "files": notes}}, folder


def _write_fake(path: Path, data: bytes, url: str) -> dict:
    """Write one fake file and return its pin: the url and the sha256 of the bytes written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"url": url, "sha256": hashlib.sha256(data).hexdigest()}
