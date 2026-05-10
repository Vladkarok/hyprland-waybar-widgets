#!/usr/bin/env python3
import json
import os
import re
import signal
import subprocess
import sys

try:
    import gi  # type: ignore
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GLib  # type: ignore
except Exception:
    try:
        subprocess.run(["notify-send", "Brightness", "PyGObject (gi) not available. Install python-gobject."])
    except Exception:
        pass
    sys.exit(1)


BRIGHTNESS_CMD = os.environ.get("OMARCHY_BRIGHTNESS_CMD", "omarchy-brightness-display")


def sh(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()


def get_percent(device: str) -> int:
    try:
        return int(sh([BRIGHTNESS_CMD, "get", device]))
    except Exception:
        return 50


def set_percent(device: str, pct: int) -> None:
    try:
        subprocess.run([BRIGHTNESS_CMD, f"{int(pct)}%", device], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class BrightnessSlider(Gtk.Window):
    def __init__(self, device: str):
        super().__init__(title="Brightness")
        self.device = device
        self.set_decorated(False)
        self.set_default_size(260, 64)
        try:
            self.set_keep_above(True)
        except Exception:
            pass
        self.set_resizable(False)
        self.connect("key-press-event", self._on_key)
        self.connect("destroy", lambda *_: Gtk.main_quit())

        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("enter-notify-event", self._on_enter)
        self.connect("leave-notify-event", self._on_leave)
        self._close_timer_id = None

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(10)
        self.add(box)

        self.label = Gtk.Label(label="Brightness")
        self.label.set_halign(Gtk.Align.CENTER)
        box.pack_start(self.label, False, False, 0)

        adj = Gtk.Adjustment(lower=1, upper=100, step_increment=1, page_increment=5)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self.scale.set_digits(0)
        self.scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.scale.set_draw_value(True)
        self.scale.connect("value-changed", self._on_change)
        box.pack_start(self.scale, True, True, 0)

        pct = get_percent(self.device)
        self.scale.set_value(pct)
        self.label.set_text(f"Brightness: {pct}%")

        signal.signal(signal.SIGUSR1, lambda *_: self._close())
        GLib.timeout_add(150, self._place_top_right)

    def _on_change(self, scale: Gtk.Scale):
        value = int(scale.get_value())
        self.label.set_text(f"Brightness: {value}%")
        set_percent(self.device, value)
        self._schedule_close(delay_ms=1500)

    def _on_key(self, _widget, event):
        key = Gdk.keyval_name(event.keyval)
        if key in ("Escape", "Return"):
            self._close()

    def _close(self, *args):
        try:
            self.destroy()
        except Exception:
            pass
        try:
            Gtk.main_quit()
        except Exception:
            pass

    def _on_enter(self, *_args):
        self._cancel_close()

    def _on_leave(self, *_args):
        self._schedule_close(delay_ms=800)

    def _schedule_close(self, delay_ms: int):
        self._cancel_close()

        def _cb():
            self._close()
            return False

        self._close_timer_id = GLib.timeout_add(delay_ms, _cb)

    def _cancel_close(self):
        if self._close_timer_id is not None:
            try:
                GLib.source_remove(self._close_timer_id)
            except Exception:
                pass
            self._close_timer_id = None

    def _place_top_right(self):
        try:
            pid = os.getpid()
            clients = json.loads(sh(["hyprctl", "-j", "clients"]))
            addr = None
            for client in clients:
                if int(client.get("pid", -1)) == pid:
                    addr = client.get("address")
                    break
            if not addr:
                return False

            cursor = sh(["hyprctl", "cursorpos"]).strip()
            parts = re.split(r"[ ,]+", cursor)
            cx, cy = int(float(parts[0])), int(float(parts[1]))
            monitors = json.loads(sh(["hyprctl", "-j", "monitors"]))
            mon = None
            for monitor in monitors:
                mx, my = monitor["x"], monitor["y"]
                mw, mh = monitor["width"], monitor["height"]
                if mx <= cx < mx + mw and my <= cy < my + mh:
                    mon = monitor
                    break
            if not mon and monitors:
                mon = monitors[0]

            margin = 16
            win_w, win_h = 260, 64
            x = mon["x"] + mon["width"] - win_w - margin
            y = mon["y"] + margin

            result = subprocess.run(
                ["hyprctl", "dispatch", "movewindowpixel", "exact", str(x), str(y), f"address:{addr}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                prev_addr = None
                try:
                    active = json.loads(sh(["hyprctl", "-j", "activewindow"]))
                    prev_addr = active.get("address")
                except Exception:
                    pass
                subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{addr}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["hyprctl", "dispatch", "movewindowpixel", "exact", str(x), str(y)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if prev_addr:
                    subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{prev_addr}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return False
        return False


def detect_device() -> str:
    try:
        for line in sh(["brightnessctl", "-l"]).splitlines():
            if line.startswith("backlight/"):
                return line.split("/", 1)[1]
    except Exception:
        pass
    return "nvidia_wmi_ec_backlight"


def main():
    device = sys.argv[1] if len(sys.argv) > 1 else detect_device()
    pidfile = "/tmp/brightness-slider.pid"
    try:
        with open(pidfile, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pidfile = None

    win = BrightnessSlider(device)
    win.show_all()
    Gtk.main()

    if pidfile:
        try:
            if os.path.exists(pidfile):
                os.remove(pidfile)
        except Exception:
            pass


if __name__ == "__main__":
    main()
