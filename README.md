# Agent Tab Titles

A [Herdr](https://herdr.dev) plugin that renames each tab to the task its coding agent is working on.

Herdr tabs are numbered `1 2 3 4`, and naming them by hand is friction nobody keeps up with. Coding agents already publish what they are doing as the terminal title, so this plugin copies that onto the tab.

```
before          after
1  2  3  4      PR 412 review  Transport reuse  RFC 8058  Flaky auth test
```

## Install

```sh
herdr plugin install ajaykumarMohite/herdr-agent-tab-titles
herdr plugin action invoke ajaykumarmohite.agent-tab-titles.install-claude-code-hook
```

The second command registers a small shim on Claude Code's `UserPromptSubmit` and `Stop` events, so every tab relabels itself as work moves. Set `CLAUDE_CONFIG_DIR` first if you keep more than one Claude Code configuration, and run it once per directory.

Restart running Claude Code sessions afterwards — hooks load at session start.

## Use it without Claude Code

Every agent Herdr detects reports a terminal title, so the rename works for any of them:

```sh
herdr plugin action invoke ajaykumarmohite.agent-tab-titles.rename-all
```

Bind it to a key in `~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "prefix+alt+t"
type = "shell"
command = "herdr plugin action invoke ajaykumarmohite.agent-tab-titles.rename-all"
```

## What it does

`rename_tabs_from_agent_titles.py` reads a pane's `terminal_title_stripped` through the Herdr CLI and renames that pane's tab to it, shortened to 18 characters on a word boundary. It skips the rename when the label already matches.

Titles that are not tasks are ignored, so a tab keeps its last real label instead of flickering:

- shell titles — anything containing `@`, or starting with `/` or `~`
- bare product names — `claude`, `codex`, `copilot`, `cursor`, `droid`, `gemini`, `opencode`, `qwen`

## Suggested sidebar

Not required, but the titles read better with one line per agent:

```toml
[ui]
prompt_new_tab_name = false

[ui.sidebar.spaces]
rows = [["state_icon", "workspace", "git_status"]]

[ui.sidebar.agents]
rows = [["state_icon", "terminal_title_stripped"]]
```

`prompt_new_tab_name = false` drops the "name this tab" dialog on every new tab — the point of the plugin is that you never name one again. Apply with `herdr server reload-config`.

## Events and the hook

The plugin declares `[[events]]` for `pane.agent_status_changed` and `pane.agent_detected`. Herdr dispatches both to an installed plugin — `herdr plugin log list --plugin ajaykumarmohite.agent-tab-titles` shows them arriving. A plugin **linked** from a local directory did not receive them in testing, so verify against an installed copy before concluding they are dead.

The Claude Code hook stays because it fires on the exact turn boundaries and does not depend on agent-status transitions being reported for that pane. Treat the events as the belt and the hook as the braces; if you use another agent, the events alone carry the rename.

## Requirements

Herdr 0.9.0 or newer, `python3` on `PATH`, Linux or macOS.

## Uninstall

```sh
herdr plugin uninstall ajaykumarmohite.agent-tab-titles
```

Then remove the two `herdr-agent-tab-title.sh` entries from `~/.claude/settings.json` and delete `~/.claude/hooks/herdr-agent-tab-title.sh`. Tab names stay as they are; `herdr tab rename <tab-id> <name>` resets one.
