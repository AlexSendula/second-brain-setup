# Second Brain Setup

Second Brain Setup gives you a second brain on your computer: an Obsidian vault of plain notes for your tasks, projects, people and plans, kept with your AI agent. You say one sentence to your agent, and it does the setup.

This is an early version (0.1.0). It has been tested by hand on macOS with Claude Code. Windows is covered by automated tests, but has not been tried by hand yet.

## Install

Ask your agent:

```text
Install this second brain for me: https://github.com/AlexSendula/second-brain-setup
```

Your agent follows [SETUP.md](SETUP.md). It checks what you have, asks where the vault should go and which agent tools you use. At the end it opens Obsidian, and you choose the vault folder and trust its plugins.

From then on, start your agent in the vault folder.

## What you need

- git 2.28 or newer
- uv 0.9.0 or newer
- Obsidian 1.10.2 or newer
- One agent tool: Claude Code, Codex, or VS Code with GitHub Copilot
- macOS or Windows. Linux is not tested.

Your agent can install git and uv for you after a yes, and Obsidian too on Windows or on macOS with Homebrew. Otherwise you install Obsidian yourself. Codex on Windows has not been tried by hand yet.

## What gets installed

Before it downloads anything, your agent names each item and waits for your yes.

- **The vault:** a new folder, `~/Documents/second-brain` by default, with the folders from `01 Dashboard` to `99 System`. If iCloud or OneDrive syncs your Documents folder, the agent suggests `~/second-brain` instead, since sync and git don't mix well.
- **What your agent follows:** `AGENTS.md`, the rules and settings in `99 System/`, and two agent skills, `brain-setup` and `brain`. Claude Code and VS Code get their own files, such as `CLAUDE.md` for Claude Code. Codex gets none.
- **Two Obsidian plugins:** [Tasks](https://github.com/obsidian-tasks-group/obsidian-tasks) 8.5.0, already set up, and [Ninja Board](https://github.com/AlexSendula/ninja-board) 1.0.0 with its five boards. After Obsidian's first restart, it opens on Today.
- **Python 3.14**, which uv downloads into its own folder the first time.
- **A git repository** in the vault, with a first saved version.

Then your agent asks your name, your timezone, and whether to turn on capacity (counting your hours) and a daily briefing.

## What's not there yet

- The agent's routines: the daily catch-up, processing the inbox, conversations and the weekly review.
- The `brain` command those routines use for dates, lookups and checks.

Both come in later versions. Until then, your agent can show and explain the vault, and you can use the boards in Obsidian.

## Updates

Your agent never updates on its own. To update, say this to your agent in the vault:

```text
update my brain
```

It finds the newest release, tells you where it comes from, shows what would change, and applies it only after your yes.

- An update never changes your notes or your rules.
- A system file you edited, such as `AGENTS.md`, is kept beside the new one as `<file>.mine`.
- The update saves a version before and after. To undo it, run this in the vault:

```bash
git revert --no-edit HEAD
```

To add another agent tool later, ask your agent to add it.

## For developers

- [SETUP.md](SETUP.md) is what the agent reads. [install.py](install.py) does the work: `install` creates a vault, and `update` updates one.
- [template/](template/) holds the vault's files, [skills/](skills/) the agent skills, and [pins.json](pins.json) the plugin versions and their checksums.

Run the tests (you need uv):

```bash
uv run --python 3.14 --with pyyaml python -m unittest discover -s tests -v
```

Set `KIT_ONLINE=1` to include the test that downloads the plugins from GitHub. CI runs the tests on macOS and Windows.

## Part of Second Brain

- [Second Brain](https://alexsendula.github.io/second-brain/): the framework, with its design and research
- [Ninja Board](https://github.com/AlexSendula/ninja-board): the Obsidian plugin that shows the vault as boards
- [Second Brain Setup](https://github.com/AlexSendula/second-brain-setup): sets up a vault from one sentence to your agent

## Licence

MIT, Copyright (c) 2026 AlexSendula. See [LICENSE](LICENSE).
