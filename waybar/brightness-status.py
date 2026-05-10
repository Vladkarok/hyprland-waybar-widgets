#!/usr/bin/env python3
import json
import os
import subprocess
import sys


BRIGHTNESS_CMD = os.environ.get("OMARCHY_BRIGHTNESS_CMD", "omarchy-brightness-display")
ICONS = ["󰃞", "󰃟", "󰃠"]


def brightness_percent(device: str) -> int:
    try:
        out = subprocess.check_output([BRIGHTNESS_CMD, "get", device], text=True, stderr=subprocess.DEVNULL)
        return max(0, min(100, int(out.strip())))
    except Exception:
        return 50


def icon_for(percent: int) -> str:
    if percent < 34:
        return ICONS[0]
    if percent < 67:
        return ICONS[1]
    return ICONS[2]


def main() -> int:
    device = sys.argv[1] if len(sys.argv) > 1 else "nvidia_wmi_ec_backlight"
    percent = brightness_percent(device)
    print(json.dumps({
        "text": icon_for(percent),
        "tooltip": f"Brightness: {percent}%",
        "class": "low" if percent < 34 else "medium" if percent < 67 else "high",
        "percentage": percent,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
