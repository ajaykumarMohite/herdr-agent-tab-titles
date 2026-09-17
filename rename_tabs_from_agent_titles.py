#!/usr/bin/env python3
import json
import os
import subprocess
import sys

MAX_LABEL_LENGTH = 18
AGENT_PRODUCT_NAMES = {
    "claude",
    "claude code",
    "codex",
    "copilot",
    "cursor",
    "droid",
    "gemini",
    "opencode",
    "qwen",
}


def run_herdr(*arguments):
    herdr = os.environ.get("HERDR_BIN_PATH", "herdr")
    completed = subprocess.run(
        [herdr, *arguments], capture_output=True, text=True, timeout=5
    )
    return completed.stdout


def read_result(payload, key):
    try:
        return json.loads(payload)["result"][key]
    except (ValueError, KeyError, TypeError):
        return None


def describes_a_task(title):
    if not title or "@" in title or title.startswith(("/", "~")):
        return False
    return title.lower() not in AGENT_PRODUCT_NAMES


def task_title_of(pane):
    title = (pane.get("terminal_title_stripped") or "").strip()
    return title if describes_a_task(title) else ""


def shortened(title):
    if len(title) <= MAX_LABEL_LENGTH:
        return title
    clipped = title[:MAX_LABEL_LENGTH]
    on_word_boundary = clipped.rsplit(" ", 1)[0]
    if len(on_word_boundary) >= MAX_LABEL_LENGTH // 2:
        return on_word_boundary
    return clipped


def current_label_of(tab_id):
    tab = read_result(run_herdr("tab", "get", tab_id), "tab") or {}
    return (tab.get("label") or "").strip()


def rename_tab_after(pane):
    tab_id = pane.get("tab_id")
    title = task_title_of(pane)
    if not tab_id or not title:
        return

    label = shortened(title)
    if label != current_label_of(tab_id):
        run_herdr("tab", "rename", tab_id, label)


def panes_from_event():
    event = os.environ.get("HERDR_PLUGIN_EVENT_JSON")
    if not event:
        return []
    try:
        pane = json.loads(event)["pane"]
    except (ValueError, KeyError, TypeError):
        return []
    return [pane]


def every_pane():
    return read_result(run_herdr("pane", "list"), "panes") or []


def requested_pane(arguments):
    pane_id = arguments[arguments.index("--pane") + 1]
    pane = read_result(run_herdr("pane", "get", pane_id), "pane")
    return [pane] if pane else []


def panes_to_rename(arguments):
    if "--all" in arguments:
        return every_pane()
    if "--pane" in arguments:
        return requested_pane(arguments)
    return panes_from_event()


def main(arguments):
    for pane in panes_to_rename(arguments):
        rename_tab_after(pane)


if __name__ == "__main__":
    main(sys.argv[1:])
