#!/usr/bin/env python3

"""Waybar calendar toggle/status helper.

Usage:
  calendar-toggle.py status
  calendar-toggle.py toggle
  calendar-toggle.py popup
"""

from __future__ import annotations

import calendar
import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


APP_ID = "omarchy-waybar-calendar"
PID_PATH = Path(f"/tmp/waybar-calendar-{os.environ.get('USER', 'user')}.pid")
WAYBAR_SIGNAL = os.environ.get("WAYBAR_CALENDAR_SIGNAL", "RTMIN+12")


def read_pid() -> int | None:
    try:
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        PID_PATH.unlink(missing_ok=True)
        return None
    except PermissionError:
        return None

    return pid


def notify_waybar() -> None:
    subprocess.run(
        ["pkill", f"-{WAYBAR_SIGNAL}", "waybar"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def status() -> None:
    today = dt.date.today()
    data = {
        "text": "󰃭",
        "tooltip": today.strftime("%A, %d %B %Y"),
        "class": "active" if read_pid() else "inactive",
    }
    print(json.dumps(data, ensure_ascii=False), flush=True)


def toggle() -> None:
    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            PID_PATH.unlink(missing_ok=True)
    else:
        subprocess.Popen(
            [sys.executable, __file__, "popup"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    time.sleep(0.1)
    notify_waybar()


def run_popup() -> None:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")

    def cleanup(*_args: object) -> None:
        PID_PATH.unlink(missing_ok=True)
        notify_waybar()
        Gtk.main_quit()

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    today = dt.date.today()

    window = Gtk.Window(title="Calendar")
    window.set_name("waybar-calendar-popup")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_keep_above(True)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
    window.set_border_width(12)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    window.add(box)

    title = Gtk.Label(label=today.strftime("%A, %d %B %Y"))
    title.set_xalign(0)
    title.get_style_context().add_class("title")
    box.pack_start(title, False, False, 0)

    cal = Gtk.Calendar()
    cal.select_month(today.month - 1, today.year)
    cal.select_day(today.day)
    cal.mark_day(today.day)
    box.pack_start(cal, True, True, 0)

    week = Gtk.Label(label=f"Week {today.isocalendar().week} · {calendar.month_name[today.month]} {today.year}")
    week.set_xalign(0)
    box.pack_start(week, False, False, 0)

    css = Gtk.CssProvider()
    css.load_from_data(
        b"""
        #waybar-calendar-popup {
          background: #1d2021;
          color: #ebdbb2;
          border: 1px solid #504945;
          border-radius: 8px;
        }
        #waybar-calendar-popup label.title {
          font-weight: 700;
        }
        """
    )
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )

    window.connect("destroy", cleanup)
    window.connect("key-press-event", lambda _w, e: cleanup() if e.keyval == Gdk.KEY_Escape else False)

    window.show_all()

    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() if display else None
    geometry = monitor.get_geometry() if monitor else Gdk.Rectangle()
    window_width, _window_height = window.get_size()
    window.move(geometry.x + geometry.width - window_width - 12, geometry.y + 34)

    notify_waybar()
    Gtk.main()


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    if command == "status":
        status()
    elif command == "toggle":
        toggle()
    elif command == "popup":
        run_popup()
    else:
        print(f"usage: {Path(__file__).name} [status|toggle|popup]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
