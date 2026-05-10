#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main():
    device = sys.argv[1] if len(sys.argv) > 1 else "nvidia_wmi_ec_backlight"
    pidfile = "/tmp/brightness-slider.pid"
    pid = None
    try:
        with open(pidfile, "r") as f:
            pid = int(f.read().strip())
    except Exception:
        pid = None

    if pid and is_alive(pid):
        try:
            os.kill(pid, signal.SIGUSR1)
        except Exception:
            pass
        for _ in range(10):
            time.sleep(0.05)
            if not is_alive(pid):
                break
        if is_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            time.sleep(0.1)
        if is_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
        try:
            if os.path.exists(pidfile):
                os.remove(pidfile)
        except Exception:
            pass
    else:
        script = os.path.expanduser("~/.config/waybar/scripts/brightness-slider.py")
        subprocess.Popen(["python3", script, device], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
