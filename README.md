# Hyprland Keyboard Layout Indicator for Waybar

A reliable keyboard layout indicator for [Waybar](https://github.com/Alexays/Waybar) on [Hyprland](https://hyprland.org/) that works around the known IPC parsing bugs in the built-in `hyprland/language` module.

## The Problem

Waybar ships a built-in `hyprland/language` module, but it has well-documented issues that cause it to fail silently for many users:

1. **IPC parsing bug with device names** -- Hyprland fires `activelayout` IPC events in the format `activelayout>>KEYBOARD_NAME,LAYOUT_NAME`. Keyboard names containing special characters (parentheses, periods, commas) break Waybar's parser. Common offenders include internal keyboards like `ite-tech.-inc.-ite-device(8176)-keyboard`. The module shows the layout as **empty/blank** after switching.

2. **Wrong keyboard device** -- The `keyboard-name` config option targets a specific device, but the XKB layout toggle shortcut (`grp:alt_shift_toggle`, etc.) may fire events from a *different* keyboard device than expected. For example, events may fire from the internal ITE keyboard but not from `at-translated-set-2-keyboard`.

3. **Upstream won't fix** -- [Hyprland issue #6298](https://github.com/hyprwm/Hyprland/issues/6298) proposed fixing the ambiguous comma-separated IPC format, but was closed as "not planned" (Feb 2025).

Related issues:
- [Waybar #4340](https://github.com/Alexays/Waybar/issues/4340) -- Parsing failure with complex device names
- [Waybar #2544](https://github.com/Alexays/Waybar/issues/2544) -- Empty display after layout change
- [Waybar #4229](https://github.com/Alexays/Waybar/issues/4229) -- Module stops updating (regression)
- [Waybar #4301](https://github.com/Alexays/Waybar/issues/4301) -- Indicator freezes after IPC warning
- [Omarchy Discussion #111](https://github.com/basecamp/omarchy/discussions/111) -- Display active keyboard layout in Waybar

## The Solution

This script bypasses the broken IPC event parser entirely. Instead of parsing the `activelayout>>` event string, it:

1. **Listens** to the Hyprland IPC socket for any `activelayout` event (as a trigger only)
2. **Queries** `hyprctl devices -j` to read the actual device state via JSON API
3. **Outputs** Waybar-compatible JSON with text, tooltip, and CSS class

This approach is reliable regardless of device name complexity because `hyprctl devices -j` returns proper JSON that `jq` parses correctly.

## Dependencies

- `hyprctl` (comes with Hyprland)
- `jq` -- JSON processor
- `socat` -- for listening to the Hyprland IPC socket

```bash
# Arch Linux
sudo pacman -S jq socat

# Debian/Ubuntu
sudo apt install jq socat

# Fedora
sudo dnf install jq socat
```

## Installation

### 1. Find your keyboard device name

```bash
hyprctl devices -j | jq -r '.keyboards[] | .name'
```

Pick the keyboard that corresponds to your physical keyboard. Common choices:
- `at-translated-set-2-keyboard` (standard PS/2 keyboard)
- An `ite-tech` or vendor-specific device (laptop internal keyboard)

> **Tip:** To identify which device fires events when you press your layout toggle shortcut, run:
> ```bash
> socat -u UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock - | grep activelayout
> ```
> Then press your layout toggle shortcut and see which keyboard name appears.

### 2. Copy the script

```bash
mkdir -p ~/.config/waybar/scripts
cp keyboard-layout.sh ~/.config/waybar/scripts/
chmod +x ~/.config/waybar/scripts/keyboard-layout.sh
```

### 3. Configure Waybar

Add the module to your Waybar config (`~/.config/waybar/config.jsonc`):

```jsonc
// Add to modules-left, modules-center, or modules-right:
"modules-right": [
    "custom/language",
    // ... your other modules
],

// Module definition:
"custom/language": {
    "exec": "~/.config/waybar/scripts/keyboard-layout.sh <YOUR_KEYBOARD_NAME>",
    "return-type": "json",
    "on-click": "hyprctl switchxkblayout all next"
},
```

Replace `<YOUR_KEYBOARD_NAME>` with the device name from step 1. If omitted, defaults to `at-translated-set-2-keyboard`.

### 4. Style (optional)

Add to your Waybar stylesheet (`~/.config/waybar/style.css`):

```css
#custom-language {
    margin-right: 15px;
}

/* Per-language styling using CSS classes */
#custom-language.en {
    color: #89b4fa;
}

#custom-language.ua {
    color: #f9e2af;
}
```

### 5. Restart Waybar

```bash
pkill waybar && waybar &disown
```

## How It Works

```
  Hyprland IPC Socket                    hyprctl devices -j
  ┌─────────────────┐                   ┌─────────────────┐
  │ activelayout>>   │  ── trigger ──>  │ JSON API query   │
  │ keyboard,layout  │                   │ (reliable parse) │
  └─────────────────┘                   └────────┬────────┘
                                                  │
                                                  v
                                         ┌─────────────────┐
                                         │ Waybar JSON out  │
                                         │ {"text": "UA"}   │
                                         └─────────────────┘
```

1. The script starts by outputting the current layout state
2. It opens a persistent connection to the Hyprland IPC socket via `socat`
3. When any `activelayout` event arrives, it waits 150ms for rapid toggles to settle (debounce)
4. It queries `hyprctl devices -j` and extracts the `active_keymap` for the target keyboard
5. It maps the keymap name to a short code and outputs Waybar JSON

## Supported Languages

The script includes mappings for 30+ languages out of the box. Unmapped languages fall back to the first two characters of the keymap name. To add a custom mapping, add a case in the `get_layout()` function:

```bash
*YourLanguage*) printf '{"text": "XX", "tooltip": "YourLanguage", "class": "xx"}\n' ;;
```

## Tested On

- Hyprland 0.54.1
- Waybar 0.15.0
- Arch Linux (Omarchy)

## License

MIT
