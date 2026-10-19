---
name: brain-setup
description: Sets up and updates the vault. Use it when the person sets up a new vault, says "update my brain", asks to add an agent tool, or asks to turn an add-on on or off.
---

Use this skill for setup and for changes to the vault's system. Run commands from the vault's top folder. Use plain words with the person, and say what a step will do before you do it.

## Every run: the synced folder check

1. Find the vault's full path. Run `pwd`.
2. Warn the person if the path is in one of these places:
   - iCloud Drive: under `~/Library/Mobile Documents/`, or under `~/Documents` or `~/Desktop` while iCloud's Desktop & Documents sync is on. If you are not sure that sync is on, ask the person to check their iCloud settings.
   - OneDrive: the path contains `OneDrive`.
3. Say why: sync and git can damage each other, and a saved version could be lost or broken.
4. Suggest a folder that sync does not cover, such as `~/second-brain`. The person decides.

## New vault

Use this when the person starts a new vault, or when `SETUP.md` hands over to this skill.

1. Ask for the person's name.
2. Make their note. Copy the Template in `99 System/types/person.md` to `05 People/<name>.md`, with today's date as `created`. Then add the line `- [[<name>]]` to `05 People/People.md`.
3. Find the timezone, then confirm it with the person:
   - macOS: run `readlink /etc/localtime`. The zone is the part after `zoneinfo/`, such as `Europe/London`.
   - Windows: run `tzutil /g`. It prints a Windows name, such as `GMT Standard Time`. Ask for the person's city, and write the zone name, such as `Europe/London`.
4. Ask two questions:
   - Capacity, which counts your hours each week and the time you log: on or off? If on, ask how many hours a day are available (`available`, default `16h`) and on which days (`available_days`, default `mon-sun`).
   - Daily briefing: on or off?
5. Name the defaults, and say that any of them can be changed on request: contexts `home, out, computer, phone`; the weekly review on Sunday; week plans on.
6. Edit `99 System/config.md`. Change only these keys, using only these answers: `timezone` (in quotes), `daily_briefing`, and `addons` (`[capacity]` when Capacity is on, `[]` when it is off). When Capacity is on, also set `available` and `available_days`. Leave every other line as it is.
7. Save a version: run `git add -A`, then `git commit -m "Set up <name>'s second brain"`.
8. If the person started this from `SETUP.md`'s install conversation, go back to `SETUP.md` and continue from step 7. If not, do not look for `SETUP.md`. Finish with a short summary of what you set and saved: the timezone, the daily briefing, the add-ons, and the saved version.

## Check git and uv

Updates and new tools need git and uv. Check both before you start.

1. Run `git --version`. Git must be installed. Any version works.
2. Run `uv --version`. The output looks like `uv 0.9.0`. uv must be 0.9.0 or newer. Compare the parts as numbers, so 0.10.0 is newer than 0.9.0.
3. If one is missing or too old, stop. Tell the person exactly what to install or upgrade, and do nothing else. Do not run the install or upgrade yourself:
   - git missing: on macOS, `xcode-select --install`. On Windows, `winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`.
   - uv missing: on macOS, `curl -LsSf https://astral.sh/uv/install.sh | sh`. On Windows, `winget install --id astral-sh.uv -e --source winget --accept-source-agreements --accept-package-agreements`.
   - uv too old: if Homebrew installed uv, `brew upgrade uv`. Otherwise, `uv self update`.
   - The winget flags accept the terms of winget and of each package. Tell the person that, and ask first.
4. Start again only when both checks pass.

## Update ("update my brain")

Update only when the person asks. Never check for updates or update on your own.

First, check git and uv, as in "Check git and uv" above.

1. Read `update_source` in `99 System/config.md`.
2. Find the newest release. Run `git ls-remote --tags "<update_source>"`. This only reads the release names; it downloads no code. Skip lines that end in `^{}`. Keep only the tags that look like a version, digits.digits.digits, such as `0.2.0`. Take the highest of those, comparing the parts as numbers, so 0.10.0 is newer than 0.9.0. If no tag looks like a version, stop and tell the person. Do not go on.
3. Tell the person where the update comes from and which release it would fetch, such as: "The update comes from `<update_source>`, release `<tag>`. Go on?" Wait for a yes. On a no, stop. Do not clone or run anything before a yes.
4. On a yes, fetch that release into a folder outside the vault that does not exist yet, such as one in the system's temporary folder: `git clone --depth 1 --branch <tag> "<update_source>" "<kit folder>"`.
5. Preview the update from the vault's top folder: `uv run "<kit folder>/install.py" update . --dry-run`. The preview changes nothing.
6. Explain the list in plain words. Each line starts with one of these actions:
   - `add`: a new file is added.
   - `replace`: a system file you have not edited is replaced with the new version.
   - `remove`: a system file the new version no longer has is removed, if you have not edited it.
   - `keep-aside`: you edited this system file, so your copy is kept as `<file>.mine` beside the new one.
   - `dashboard`: a new dashboard note is added. An existing dashboard is never rewritten.
   - `mark`: an existing dashboard note that has no `cssclasses` property gets `cssclasses: ninja-board` added. That marks it as a board page, so Ninja Board opens it read-only and shows only the board, without its Properties and title. Nothing else in the note changes, and a dashboard that already has `cssclasses` is left alone.
   - `tool`: an agent tool's files are added.
   - `version`: the system version in config changes.
   - `migration: none`: no note needs converting to a new format.
   Say that the update never changes the person's rules, their own skills or their notes, except for the one property `mark` adds to a dashboard. It changes the version numbers and the list of agent tools in config. System files such as `AGENTS.md`, `.claude/settings.json` and `.vscode/settings.json` can be replaced, or kept aside as `<file>.mine` when the person edited them.
   Also explain these, when they apply:
   - An update from 0.1.x moves Claude Code's file to `.claude/CLAUDE.md`. For an unedited `CLAUDE.md`, the list shows `add .claude/CLAUDE.md` and `remove CLAUDE.md`. If the person edited it, the list shows only the add, and the root `CLAUDE.md` stays; they can move their edits into the new file.
   - The update adds the `hide-agent-files` snippet. The person turns it on in Settings → Appearance → CSS snippets, and then `AGENTS.md` no longer shows in Obsidian's file list.
   - An update never installs or updates plugins. Obsidian does: Settings → Community plugins → Check for updates.
7. Ask whether to apply the update. Wait for a yes. The update saves a version before it changes anything, and another after. To undo it, run `git revert --no-edit HEAD` in the vault. That saves a new version which undoes the update. Never use `git reset --hard`.
8. On a yes, run the update for real: `uv run "<kit folder>/install.py" update .` If the run ends with a line that starts with `install.py:`, the update failed. Show that line to the person. Running the same update again is safe. The line `already up to date` means there is nothing to do.
9. Run the check: `uv run .agents/skills/brain/scripts/brain.py check`. Until the tool exists, skip this step and say so.
10. Summarize in plain words: what was added, replaced, marked and kept aside, where any `.mine` copies are, and the new version.

## Add a tool

Use this when the person starts using another agent tool. The tool ids are `claude-code` (Claude Code), `codex` (Codex) and `vscode` (VS Code with GitHub Copilot).

First, check git and uv, as in "Check git and uv" above.

1. Ask which tool they want to add.
2. Find the newest release and tell the person the update source and release, as in an update, steps 1 to 3. Wait for a yes before cloning or running anything.
3. On a yes, fetch the release as in an update, step 4.
4. Preview: `uv run "<kit folder>/install.py" update . --tools <id> --dry-run`. The newest release comes with it, so the list can show other changes too. Explain all of them, as in an update, and ask whether to apply it.
5. On a yes, run the same command without `--dry-run`. The update saves versions before and after, as in an update.
6. Summarize: the tool's files are added, and `agent_tools` in config lists the tool. Codex has no extra files.

## Add-ons on or off

Capacity is the only add-on so far.

1. Ask which add-on, and whether it goes on or off.
2. On a yes, change `addons` in `99 System/config.md`. To turn an add-on on, add its id to the list (`capacity`). To turn it off, remove the id. Change nothing else.
3. If Capacity is on and `available` or `available_days` is missing, ask for them. The defaults are `16h` and `mon-sun`.
4. When Capacity is off, leave `available` and `available_days` in config. They stay valid.
5. Save a version: run `git add -A`, then `git commit -m "Turn <add-on> on"` or `"Turn <add-on> off"`.

## Format migration

None yet. If the person asks, say so. Every update ends with `migration: none`. If an update ever shows any other last line, stop and tell the person. This skill cannot migrate notes yet.
