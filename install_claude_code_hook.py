#!/usr/bin/env python3
import json
import os
import pathlib
import stat
import sys

HOOKED_EVENTS = ("UserPromptSubmit", "Stop")

SHIM_TEMPLATE = """#!/bin/sh
set -eu

[ "${{HERDR_ENV:-}}" = "1" ] || exit 0
[ -n "${{HERDR_PANE_ID:-}}" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

cat >/dev/null 2>&1 || true

exec python3 "{renamer}" --pane "$HERDR_PANE_ID"
"""

plugin_root = pathlib.Path(
    os.environ.get("HERDR_PLUGIN_ROOT", pathlib.Path(__file__).resolve().parent)
)


def requested_config_dirs(arguments):
    if "--config-dir" in arguments:
        return [pathlib.Path(arguments[arguments.index("--config-dir") + 1])]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        return [pathlib.Path(os.environ["CLAUDE_CONFIG_DIR"])]
    return []


def discovered_config_dirs():
    home = pathlib.Path.home()
    candidates = [home / ".claude", *sorted(home.glob(".claude-*"))]
    return [
        directory
        for directory in candidates
        if (directory / "settings.json").is_file()
    ]


def write_shim(config_dir):
    hooks_dir = config_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    shim_path = hooks_dir / "herdr-agent-tab-title.sh"
    renamer = plugin_root / "rename_tabs_from_agent_titles.py"
    shim_path.write_text(SHIM_TEMPLATE.format(renamer=renamer))
    shim_path.chmod(shim_path.stat().st_mode | stat.S_IXUSR)
    return shim_path


def register(settings, shim_path):
    command = "sh '%s'" % shim_path
    entry = {
        "matcher": "*",
        "hooks": [{"type": "command", "command": command, "timeout": 5}],
    }

    hooks = settings.setdefault("hooks", {})
    for event in HOOKED_EVENTS:
        registered = hooks.setdefault(event, [])
        if not any(command in json.dumps(item) for item in registered):
            registered.append(entry)


def load_settings(settings_path):
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text())
    except ValueError:
        raise SystemExit("%s is not valid JSON; fix it and rerun" % settings_path)


def install_into(config_dir):
    settings_path = config_dir.expanduser() / "settings.json"
    settings = load_settings(settings_path)
    register(settings, write_shim(config_dir.expanduser()))
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    print("hooked %s in %s" % (", ".join(HOOKED_EVENTS), settings_path))


def main(arguments):
    config_dirs = requested_config_dirs(arguments) or discovered_config_dirs()
    if not config_dirs:
        raise SystemExit("no Claude Code configuration directory found")

    for config_dir in config_dirs:
        install_into(config_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
