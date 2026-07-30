#!/bin/bash

# Manual on-screen keyboard toggle/status helper for Waybar on Hyprland.
#
# Dependencies: wvkbd, pgrep, pkill
#
# Optional environment:
#   SCREEN_KEYBOARD_BIN       Keyboard binary to run. Default: wvkbd-mobintl
#   SCREEN_KEYBOARD_ARGS      Arguments passed when starting it. Default: -L 260
#   SCREEN_KEYBOARD_WAYBAR_SIGNAL  Waybar custom-module signal. Default: RTMIN+11

set -euo pipefail

keyboard_bin="${SCREEN_KEYBOARD_BIN:-wvkbd-mobintl}"
keyboard_args="${SCREEN_KEYBOARD_ARGS:--L 260}"
waybar_signal="${SCREEN_KEYBOARD_WAYBAR_SIGNAL:-RTMIN+11}"

is_running() {
    pgrep -x "$keyboard_bin" >/dev/null
}

status() {
    if is_running; then
        printf '{"text":"󰌌","tooltip":"Hide screen keyboard","class":"active"}\n'
    else
        printf '{"text":"󰌌","tooltip":"Show screen keyboard","class":"inactive"}\n'
    fi
}

notify_waybar() {
    pkill -"$waybar_signal" waybar 2>/dev/null || true
}

start_keyboard() {
    if command -v uwsm >/dev/null 2>&1; then
        # shellcheck disable=SC2086
        uwsm app -- "$keyboard_bin" $keyboard_args >/dev/null 2>&1 &
    else
        # shellcheck disable=SC2086
        "$keyboard_bin" $keyboard_args >/dev/null 2>&1 &
    fi
}

case "${1:-status}" in
    toggle)
        if is_running; then
            pkill -x "$keyboard_bin"
        else
            start_keyboard
        fi
        sleep 0.1
        notify_waybar
        ;;
    status)
        status
        ;;
    *)
        printf 'usage: %s [status|toggle]\n' "$0" >&2
        exit 2
        ;;
esac
