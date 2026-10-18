# Set up a second brain

This file is for the agent. The person asked you to install a second brain for them. Work through these steps in order. Use plain words. Say what a step will do before you do it.

Rules for the whole setup:

- Ask before every install, and before anything that needs admin rights.
- Change nothing outside the vault folder. The exceptions are installing git, uv or Obsidian on a yes, and the temporary kit folder in step 4.

## 1. Find out which agent you are

You are Claude Code, Codex, or VS Code with GitHub Copilot. If you are not sure which one you are, ask the person.

If you are another tool, tell the person plainly that your tool is not supported or tested. Offer to install anyway. The vault and its `AGENTS.md` work with any agent that reads `AGENTS.md`, but nothing is promised for your tool. If the person says yes, see the tool choice in step 3.

## 2. Check git, uv and Obsidian

Check each one. If one is missing or too old, tell the person what it is and why it is needed. Install only after a yes.

- **git:** run `git --version`. It must be 2.28 or newer.
- **uv:** run `uv --version`. It must be 0.9.0 or newer. Compare the parts as numbers, so 0.10.0 is newer than 0.9.0. The installer needs a final Python 3.14, which uv 0.9.0 and newer offer.
- **Obsidian:** it must be 1.10.2 or newer. This is the app version, from Settings → About in Obsidian. If you cannot read it, ask the person to open Obsidian, go to Settings → About, and tell you the version.

If a tool is too old:

- **uv:** on macOS, run `brew upgrade uv` if Homebrew installed uv. Otherwise run `uv self update`. On Windows, run `winget upgrade --id astral-sh.uv -e`.
- **Obsidian:** ask the person to update it from Settings → About, or to download the newest version from https://obsidian.md/download.

To install what is missing, after a yes:

- **macOS, git:** run `xcode-select --install`. A window opens. The person clicks Install and waits for it to finish.
- **macOS, uv:** run `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **macOS, Obsidian:** download it from https://obsidian.md/download, then drag it to Applications. The agent cannot do that part; the person does it. If Homebrew is already installed, `brew install git uv` does the same for git and uv, and after a yes the agent may run `brew install --cask obsidian` for Obsidian.
- **Windows:** run `winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`, then `winget install --id astral-sh.uv -e --source winget --accept-source-agreements --accept-package-agreements`, then `winget install --id Obsidian.Obsidian -e --source winget --accept-source-agreements --accept-package-agreements`. Those flags accept the terms of winget and of each package. Tell the person that, and ask first. If `winget` is not found, tell the person and stop until they can use it.

After an install, check again. A terminal that was already open may not see a new tool. Open a new terminal and check again. If the check still fails, ask the person to restart you and start this setup again.

If the person says no to an install, or an install is blocked (for example on a work laptop), say what is still missing. For a blocked install, say exactly what to ask IT for: git, uv 0.9.0 or newer, and Obsidian 1.10.2 or newer. Then stop until the person has them.

## 3. Ask two questions

Ask both before you install.

**Where the vault goes.** The default is `~/Documents/second-brain`. Check first whether that folder is in a synced folder:

- On macOS, if the folder `~/Library/Mobile Documents/com~apple~CloudDocs/Documents` exists, iCloud syncs Documents. Propose `~/second-brain` instead.
- On Windows, find the Documents path. Run `powershell -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')"`. If the path contains `OneDrive`, propose `%USERPROFILE%\second-brain` instead.

Say why. Sync and git can damage each other, and a saved version could be lost or broken. The install needs a folder that does not exist yet, or one that is empty. On Windows, use the full path in the install command. The installer does not expand `%USERPROFILE%`.

**Which tools.** The choices are:

- Claude Code (`claude-code`)
- Codex (`codex`)
- VS Code with GitHub Copilot (`vscode`)

Your own tool is already picked. The person can pick others too.

If your tool is not one of these, use `none` instead of tool ids. That installs no tool files. For such an agent, `AGENTS.md` is the entry point. Tell the person plainly that your tool is not supported or tested. Also tell them that the vault has no tool files and lists no agent tools.

## 4. Get the kit

Get the newest release of the kit. Never use the `main` branch.

1. Run `git ls-remote --tags https://github.com/AlexSendula/second-brain-setup`. This only reads the tag list. Skip the lines that end in `^{}`. Take the highest version tag, such as `0.1.0`. Compare the parts as numbers.
2. Before anything is downloaded, ask the person **Install now?** Name what the install fetches:
   - the kit, release `<tag>`, from https://github.com/AlexSendula/second-brain-setup
   - Ninja Board's five dashboard notes, from the Ninja Board 1.0.2 release, https://github.com/AlexSendula/ninja-board
   - Python 3.14, which uv downloads into its own folder the first time it needs it

   Go on only on a yes. If the answer is no, say what is still missing, and stop.
3. Clone that tag into a temporary folder that does not exist yet, such as one in the system's temporary folder: `git clone --depth 1 --branch <tag> https://github.com/AlexSendula/second-brain-setup <temp folder>`

## 5. Install the vault

The answers in step 3 and the yes in step 4 cover this install. Run the installer from the temporary folder:

`uv run <temp folder>/install.py install <folder> --tools <ids>`

- `<folder>` is the vault folder from step 3.
- `<ids>` is the tool ids from step 3, separated by commas with no spaces, such as `claude-code,codex`. For an unsupported tool, use `--tools none`.
- The first run can take a minute while uv fetches Python 3.14.
- A line that starts with `install.py: warning:` is not an error. Show it to the person and go on.
- If the command fails, it prints one line that starts with `install.py:` and exits with code 1. Show that line to the person, and stop.
- If the folder still has files in it after a failed install, tell the person. The install only starts in an empty folder, so those files are the install's. With the person's yes, delete that folder and run step 5 again.

## 6. Set up the vault with its own skill

Read `<folder>/.agents/skills/brain-setup/SKILL.md`. Follow its "New vault" section in this conversation. Run its commands from the vault folder. When that section is done, it sends you back to this file at step 7.

## 7. Placeholder: "What's on your mind"

**Placeholder, not built yet.** This step comes with the routines. Skip it, and go on to step 8.

## 8. Open Obsidian

Open Obsidian:

- macOS: run `open -a Obsidian`.
- Windows: run `start "" obsidian://` in cmd. From another shell, run `cmd /c start "" obsidian://`.

Then tell the person the one click that stays with them: click **Open folder as vault**, then choose the vault folder. No other dialog appears.

Tell the person that Today says "Unknown view type: ninja-board-today". That is expected. It goes away after Ninja Board is installed and Obsidian is restarted, in step 9.

## 9. Install the two plugins

The vault is set up for two Obsidian plugins, Tasks and Ninja Board, but their code is not in it yet. Tell the person that both come from Obsidian's community plugins, that Obsidian keeps them up to date, and that Tasks needs no settings because the kit already set them.

Ask the person: do they want to install Tasks and Ninja Board in Obsidian themselves, or should you do it? Their choice is the yes for the installs in this step. Follow the way they choose.

**The person does it:**

1. Tell the person to open Settings → Community plugins in Obsidian and click **Turn on community plugins**.
2. Open Tasks' page in Obsidian:
   - macOS: run `open "obsidian://show-plugin?id=obsidian-tasks-plugin"`.
   - Windows: run `start "" "obsidian://show-plugin?id=obsidian-tasks-plugin"` in cmd. From another shell, run `cmd /c start "" "obsidian://show-plugin?id=obsidian-tasks-plugin"`.
3. Tell the person to click **Install**, then **Enable**.
4. Do the same for Ninja Board. Its page is `obsidian://show-plugin?id=ninja-board`.

**The agent does it**, through Obsidian's command line interface:

1. Tell the person to turn on Settings → General → Advanced → **Command line interface**. If Obsidian offers to register it in the terminal, the person may skip that. If the setting is not there, Obsidian is older than 1.12.4. Use the person's way instead.
2. Find the command, called `<obsidian>` below. Use `obsidian` if it is on the PATH (macOS: `command -v obsidian`; Windows: `where.exe obsidian`). If not, on macOS use `/Applications/Obsidian.app/Contents/MacOS/Obsidian`. On Windows, Obsidian is normally at `%LOCALAPPDATA%\Programs\Obsidian\Obsidian.exe` in cmd, and `$env:LOCALAPPDATA\Programs\Obsidian\Obsidian.exe` in PowerShell. Write out the real folder, and wrap the full path in double quotes wherever `<obsidian>` is used, because a user name can contain spaces. In PowerShell, put `& ` before the quoted path. This has not been tested on Windows.
3. Run these from the vault folder. In that folder, the command targets that vault:
   - `<obsidian> plugins:restrict off`
   - `<obsidian> plugin:install id=obsidian-tasks-plugin enable`
   - `<obsidian> plugin:install id=ninja-board enable`
4. Then always run `<obsidian> plugins:enabled filter=community versions`, and check that `obsidian-tasks-plugin` and `ninja-board` are both listed, each with a version number. An id without a version is switched on but not installed yet. An install can print nothing even when it worked.
5. Ignore lines such as `Loading updated app package …` and `Your Obsidian installer is out of date …`. They are not errors. If a command says the command line interface is not enabled, ask the person to turn it on. If the two plugins are still not both listed, switch to the person's way.

**Both ways:** tell the person to quit Obsidian once and open it again. Obsidian applies the start page only when the app starts, and a Today tab that was open before the install keeps the "Unknown view type" message until then. On macOS, the person presses Cmd+Q. On Windows, they close the window. From then on, Obsidian opens on Today, with its board.

To check that Tasks is set up, the person can open the Guide board. Its Setup tile shows four OK lines.

## 10. Hand over

Tell the person how to start their agent inside the vault. From now on, always start the agent in the vault folder.

- Claude Code: `cd <folder>`, then `claude`.
- Codex: `cd <folder>`, then `codex`.
- VS Code: File → Open Folder, then choose the vault folder. Then open Copilot Chat.

The first time the person starts Claude Code or Codex in the vault folder, it asks whether to trust the folder. Tell them to answer yes.

Then say that the setup is done, and give the vault folder's path.
