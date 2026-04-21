#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path


BLOCKS = "▁▂▃▄▅▆▇█"
HISTORY_LENGTH = 10
STATE_PATH = Path(f"/tmp/waybar-cpu-state-{os.environ.get('USER', 'user')}.json")


def read_text(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def read_boot_id():
    return read_text("/proc/sys/kernel/random/boot_id") or "unknown"


def read_cpu_stats():
    stats = {}
    with open("/proc/stat", "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("cpu"):
                break
            parts = line.split()
            name = parts[0]
            values = [int(value) for value in parts[1:]]
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            stats[name] = {"idle": idle, "total": sum(values)}
    return stats


def load_percent(current, previous):
    total_delta = current["total"] - previous["total"]
    idle_delta = current["idle"] - previous["idle"]
    if total_delta <= 0:
        return 0.0
    busy_delta = max(total_delta - idle_delta, 0)
    return busy_delta * 100.0 / total_delta


def read_topology():
    logical_to_sensor = {}
    cpu_count = os.cpu_count() or 0
    for cpu in range(cpu_count):
        core_id = read_text(f"/sys/devices/system/cpu/cpu{cpu}/topology/core_id")
        if core_id is None:
            logical_to_sensor[cpu] = None
            continue
        logical_to_sensor[cpu] = f"Core {core_id}"
    return logical_to_sensor


def read_temperatures():
    hwmon_root = Path("/sys/class/hwmon")
    labels = {}
    package_temp = None

    for hwmon in hwmon_root.glob("hwmon*"):
        if read_text(hwmon / "name") != "coretemp":
            continue
        for input_file in sorted(hwmon.glob("temp*_input")):
            base = input_file.name[:-6]
            label = read_text(hwmon / f"{base}_label")
            raw_value = read_text(input_file)
            if raw_value is None:
                continue
            temp_c = round(int(raw_value) / 1000)
            if label == "Package id 0":
                package_temp = temp_c
            elif label:
                labels[label] = temp_c
        break

    if package_temp is None:
        for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
            if read_text(zone / "type") == "x86_pkg_temp":
                raw_value = read_text(zone / "temp")
                if raw_value is not None:
                    package_temp = round(int(raw_value) / 1000)
                break

    return package_temp, labels


def temp_class(temp_c):
    if temp_c is None:
        return "cool"
    if temp_c >= 90:
        return "critical"
    if temp_c >= 80:
        return "hot"
    if temp_c >= 65:
        return "warm"
    return "cool"


def sparkline(values):
    if not values:
        return ""
    chars = []
    for value in values[-HISTORY_LENGTH:]:
        index = min(len(BLOCKS) - 1, max(0, round(value * (len(BLOCKS) - 1) / 100)))
        chars.append(BLOCKS[index])
    return "".join(chars)


def trim_history(values):
    return values[-HISTORY_LENGTH:]


def load_state(boot_id):
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "boot_id": boot_id,
            "prev_stats": {},
            "history": {"total": [], "cores": {}},
            "peak_temps": {"package": None, "labels": {}},
        }

    if state.get("boot_id") != boot_id:
        return {
            "boot_id": boot_id,
            "prev_stats": {},
            "history": {"total": [], "cores": {}},
            "peak_temps": {"package": None, "labels": {}},
        }

    return state


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state), encoding="utf-8")
    tmp_path.replace(STATE_PATH)


def format_temp(value):
    if value is None:
        return "--C"
    return f"{value:>3}C"


def main():
    boot_id = read_boot_id()
    state = load_state(boot_id)
    previous_stats = state.get("prev_stats")
    if previous_stats:
        current_stats = read_cpu_stats()
    else:
        previous_stats = read_cpu_stats()
        time.sleep(0.2)
        current_stats = read_cpu_stats()

    topology = read_topology()
    package_temp, labeled_temps = read_temperatures()

    total_usage = round(load_percent(current_stats["cpu"], previous_stats.get("cpu", current_stats["cpu"])))
    cpu_count = len([key for key in current_stats if key.startswith("cpu") and key != "cpu"])

    history = state.setdefault("history", {"total": [], "cores": {}})
    history["total"] = trim_history(history.get("total", []) + [total_usage])

    peaks = state.setdefault("peak_temps", {"package": None, "labels": {}})
    if package_temp is not None:
        previous_peak = peaks.get("package")
        peaks["package"] = package_temp if previous_peak is None else max(previous_peak, package_temp)

    lines = []
    lines.append(
        f"Total : {total_usage:>3}%  {format_temp(package_temp)}  peak {format_temp(peaks.get('package'))}  {sparkline(history['total'])}"
    )

    core_history = history.setdefault("cores", {})
    label_peaks = peaks.setdefault("labels", {})
    label_width = len(f"Core{max(cpu_count - 1, 0)}")

    for cpu in range(cpu_count):
        stat_name = f"cpu{cpu}"
        usage = round(load_percent(current_stats[stat_name], previous_stats.get(stat_name, current_stats[stat_name])))
        samples = trim_history(core_history.get(str(cpu), []) + [usage])
        core_history[str(cpu)] = samples

        sensor_label = topology.get(cpu)
        temp = labeled_temps.get(sensor_label, package_temp)
        if sensor_label and temp is not None:
            prior_peak = label_peaks.get(sensor_label)
            label_peaks[sensor_label] = temp if prior_peak is None else max(prior_peak, temp)
        peak = label_peaks.get(sensor_label, peaks.get("package"))

        lines.append(
            f"{f'Core{cpu}':<{label_width}}: {usage:>3}%  {format_temp(temp)}  peak {format_temp(peak)}  {sparkline(samples)}"
        )

    payload = {
        "text": "󰍛",
        "tooltip": "<tt>" + "\n".join(lines) + "</tt>",
        "class": temp_class(package_temp),
        "percentage": int(package_temp if package_temp is not None else total_usage),
    }
    print(json.dumps(payload, ensure_ascii=False))

    state["boot_id"] = boot_id
    state["prev_stats"] = current_stats
    save_state(state)


if __name__ == "__main__":
    main()
