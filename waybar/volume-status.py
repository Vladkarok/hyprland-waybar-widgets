#!/usr/bin/env python3

import json
import re
import subprocess
import sys


LOW = "▏"
MEDIUM = "▎"
HIGH = "▌"
GAP = " "


def run(command):
    return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()


def default_sink_name():
    for line in run(["pactl", "info"]).splitlines():
        if line.startswith("Default Sink:"):
            return line.split(":", 1)[1].strip()
    return None


def read_sinks():
    return json.loads(run(["pactl", "-f", "json", "list", "sinks"]))


def active_icon(sink):
    active_port = str(sink.get("active_port", "")).lower()
    if "headset" in active_port:
        return "󰋎"
    if "headphone" in active_port:
        return ""

    for port in sink.get("ports", []):
        if port.get("name") != sink.get("active_port"):
            continue
        port_type = str(port.get("type", "")).lower()
        description = str(port.get("description", "")).lower()
        if "headset" in port_type or "headset" in description:
            return "󰋎"
        if "headphone" in port_type or "headphone" in description:
            return ""

    return ""


def volume_percent(sink):
    channels = sink.get("volume", {}).values()
    values = []
    for channel in channels:
        match = re.search(r"\d+", str(channel.get("value_percent", "")))
        if match:
            values.append(int(match.group(0)))
    if not values:
        return 0
    return round(sum(values) / len(values))


def level_mark(volume):
    if volume <= 0:
        return "×"
    if volume <= 33:
        return LOW
    if volume <= 66:
        return MEDIUM
    return HIGH


def main():
    try:
        default_name = default_sink_name()
        sinks = read_sinks()
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError) as error:
        print(json.dumps({"text": "×", "tooltip": f"Audio unavailable: {error}", "class": "error"}))
        return 1

    sink = next((item for item in sinks if item.get("name") == default_name), None)
    if sink is None and sinks:
        sink = sinks[0]
    if sink is None:
        print(json.dumps({"text": "×", "tooltip": "No audio sink", "class": "error"}))
        return 1

    volume = volume_percent(sink)
    muted = bool(sink.get("mute"))
    icon = active_icon(sink)
    mark = "×" if muted else level_mark(volume)

    state_class = "muted" if muted else "zero" if volume <= 0 else "normal"
    tooltip = f"{'Muted' if muted else 'Playing'} at {volume}%"
    print(
        json.dumps(
            {
                "text": f"{mark}{GAP}{icon}",
                "tooltip": tooltip,
                "class": state_class,
                "percentage": volume,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
