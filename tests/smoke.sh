#!/bin/sh
set -eu

plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
herdr="${HERDR_BIN_PATH:-herdr}"

if ! command -v "$herdr" >/dev/null 2>&1; then
    echo "skip: herdr is not on PATH"
    exit 0
fi

pane_id="${HERDR_PANE_ID:-}"
if [ -z "$pane_id" ]; then
    echo "skip: run this inside a Herdr pane"
    exit 0
fi

pane_info="$("$herdr" pane get "$pane_id" 2>/dev/null || true)"
tab_id="$(printf '%s' "$pane_info" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin)["result"]["pane"]["tab_id"])
except Exception:
    pass')"

if [ -z "$tab_id" ]; then
    echo "skip: pane $pane_id is not in the running session"
    exit 0
fi
original_label="$("$herdr" tab get "$tab_id" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["tab"]["label"])')"

"$herdr" tab rename "$tab_id" smoke-placeholder >/dev/null
python3 "$plugin_root/rename_tabs_from_agent_titles.py" --pane "$pane_id"
renamed_label="$("$herdr" tab get "$tab_id" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["tab"]["label"])')"

if [ "$renamed_label" = "smoke-placeholder" ]; then
    "$herdr" tab rename "$tab_id" "$original_label" >/dev/null
    echo "fail: the tab kept the placeholder label"
    exit 1
fi

echo "pass: tab renamed to '$renamed_label'"
