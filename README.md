# Omarchy Fixes

Small fixes I keep around for an Omarchy setup.

This repo currently has four buckets:

- `waybar/`: custom Waybar widgets and config snippets
- `omarchy/`: power profile, brightness, and screenshot fixes for Omarchy
- `hypr/`: Hyprland config files with no upstream Omarchy equivalent
- `docs/`: notes about this setup

See [docs/customizations.md](docs/customizations.md) for a full inventory of what is
customized against stock Omarchy and why — written to support wiping back to defaults
on the Omarchy 4.0 upgrade and re-adding tweaks deliberately.

## Waybar

Included files:

- `waybar/keyboard-layout.sh`: reliable keyboard layout indicator for Hyprland
- `waybar/calendar-toggle.py`: Waybar calendar icon with a small GTK popup
- `waybar/screen-keyboard.sh`: manual Waybar/Hyprland toggle for `wvkbd`
- `waybar/cpu-status.py`: CPU widget showing total usage % next to the icon, with per-core hover details and short load graphs
- `waybar/volume-status.py`: volume widget showing rough level glyphs with exact 0% and muted handling
- `waybar/brightness-status.py`: brightness widget status from the shared brightness curve helper
- `waybar/brightness-toggle.py`: toggles the custom brightness slider
- `waybar/brightness-slider.py`: GTK brightness slider backed by the shared brightness curve helper
- `waybar/examples/calendar-toggle.jsonc`: Waybar custom module for a popup calendar icon
- `waybar/examples/calendar-toggle.css`: matching calendar module spacing and active color
- `waybar/examples/screen-keyboard.jsonc`: Waybar custom module for manually toggling `wvkbd`
- `waybar/examples/screen-keyboard.css`: matching screen keyboard module spacing and active color
- `waybar/examples/memory-builtin.jsonc`: built-in Waybar memory widget example
- `waybar/examples/memory-builtin.css`: matching memory widget colors
- `waybar/examples/pulseaudio-volume-level.jsonc`: custom Waybar volume widget example showing rough volume level with compact glyphs
- `waybar/examples/pulseaudio-volume-level.css`: optional stable width for the volume widget
- `waybar/examples/backlight-linear.jsonc`: Waybar backlight module wired to the shared brightness curve helper

### Keyboard Layout Widget

This works around the known IPC parsing problems in Waybar's built-in `hyprland/language` module by treating the socket event as a trigger and reading the real layout state from `hyprctl devices -j`.

Dependencies:

- `hyprctl`
- `jq`
- `socat`

Install:

```bash
mkdir -p ~/.config/waybar/scripts
install -m755 waybar/keyboard-layout.sh ~/.config/waybar/scripts/keyboard-layout.sh
```

Find your keyboard device name:

```bash
hyprctl devices -j | jq -r '.keyboards[] | .name'
```

Waybar snippet:

```jsonc
"modules-right": [
  "custom/language"
],

"custom/language": {
  "exec": "~/.config/waybar/scripts/keyboard-layout.sh <YOUR_KEYBOARD_NAME>",
  "return-type": "json",
  "on-click": "hyprctl switchxkblayout all next"
}
```

Optional CSS:

```css
#custom-language.en {
  color: #89b4fa;
}

#custom-language.ua {
  color: #f9e2af;
}
```

### Calendar Toggle

This adds a Waybar calendar icon that opens a small GTK calendar popup. It is
self-contained and does not need `gsimplecal`, `yad`, or another external
calendar app.

Files:

- `waybar/calendar-toggle.py`
- `waybar/examples/calendar-toggle.jsonc`
- `waybar/examples/calendar-toggle.css`

Dependencies:

- `python3`
- `python-gobject`
- GTK 3
- `pgrep`
- `pkill`

Install:

```bash
mkdir -p ~/.config/waybar/scripts
install -m755 waybar/calendar-toggle.py ~/.config/waybar/scripts/calendar-toggle.py
```

Add `custom/calendar` to `modules-center`, for example next to the clock:

```jsonc
"modules-center": [
  "clock",
  "custom/calendar",
  "custom/weather"
]
```

Waybar snippet:

```jsonc
"custom/calendar": {
  "exec": "python3 ~/.config/waybar/scripts/calendar-toggle.py status",
  "return-type": "json",
  "format": "{}",
  "tooltip": true,
  "on-click": "python3 ~/.config/waybar/scripts/calendar-toggle.py toggle",
  "signal": 12,
  "interval": 60
}
```

Optional CSS:

```css
#custom-calendar {
  min-width: 12px;
  margin-left: 7.5px;
  margin-right: 7.5px;
}

#custom-calendar.active {
  color: #a55555;
}
```

### Screen Keyboard Toggle

This adds a manual Waybar icon for toggling `wvkbd`. The widget reports active
while the keyboard process is running, so it uses start/stop instead of
signal-based hide/show.

Files:

- `waybar/screen-keyboard.sh`
- `waybar/examples/screen-keyboard.jsonc`
- `waybar/examples/screen-keyboard.css`

Dependencies:

- `wvkbd`
- `pgrep`
- `pkill`

Install:

```bash
mkdir -p ~/.config/waybar/scripts
install -m755 waybar/screen-keyboard.sh ~/.config/waybar/scripts/screen-keyboard.sh
```

Add `custom/screen-keyboard` to `modules-right`, for example next to the
language indicator:

```jsonc
"modules-right": [
  "custom/language",
  "custom/screen-keyboard"
]
```

Waybar snippet:

```jsonc
"custom/screen-keyboard": {
  "exec": "~/.config/waybar/scripts/screen-keyboard.sh status",
  "return-type": "json",
  "format": "{}",
  "tooltip": true,
  "on-click": "~/.config/waybar/scripts/screen-keyboard.sh toggle",
  "signal": 11,
  "interval": 10
}
```

Optional CSS:

```css
#custom-screen-keyboard {
  min-width: 12px;
  margin-right: 12px;
}

#custom-screen-keyboard.active {
  color: #a55555;
}
```

Optional Hyprland binding:

```ini
bindd = SUPER ALT, K, Toggle screen keyboard, exec, ~/.config/waybar/scripts/screen-keyboard.sh toggle
```

### CPU Hover Widget

This replaces the stock `cpu` module with a custom widget that shows total CPU usage % to the left of the icon and exposes much more detail on hover.

Tooltip data:

- total CPU load
- per-core load
- per-core temperature when exposed by the kernel
- session peak temperature
- 10-sample CPU load sparklines for total and per-core history

Install:

```bash
mkdir -p ~/.config/waybar/scripts
install -m755 waybar/cpu-status.py ~/.config/waybar/scripts/cpu-status.py
```

Waybar snippet:

```jsonc
"modules-right": [
  "custom/cpu"
],

"custom/cpu": {
  "exec": "python3 ~/.config/waybar/scripts/cpu-status.py",
  "return-type": "json",
  "interval": 1,
  "tooltip": true
}
```

Optional CSS:

```css
#custom-cpu.warm {
  color: #d79921;
}

#custom-cpu.hot {
  color: #fe8019;
}

#custom-cpu.critical {
  color: #fb4934;
}
```

Notes:

- On many Intel CPUs, temperatures are exposed per physical core, not per logical thread.
- The `peak` value is tracked by the script for the current boot session.
- The sparkline is CPU load history, not temperature history.

### Built-in Memory Widget

If you do not need a custom RAM graph yet, the built-in `memory` module is enough — the example shows usage % next to the icon with a useful hover tooltip.

Files:

- `waybar/examples/memory-builtin.jsonc`
- `waybar/examples/memory-builtin.css`

Recommended behavior:

- show usage percentage to the left of the icon in the bar
- show percentage and used / total GiB on hover
- keep warning and critical colors through `states`

### Volume Level Indicator

Omarchy's stock `pulseaudio` module can show only one icon per output type and cannot distinguish exact `0%` from other values in the first icon bucket. The custom example keeps the widget icon-only but uses a tiny left-side level glyph for low / medium / high volume, with a distinct `×` marker for muted or exact `0%`.

Files:

- `waybar/examples/pulseaudio-volume-level.jsonc`
- `waybar/examples/pulseaudio-volume-level.css`
- `waybar/volume-status.py`

Recommended behavior:

- show rough low / medium / high output volume without another percentage
- show exact `0%` and muted as a distinct `×` state
- keep speaker, headphone, and headset states visually distinct

Dependencies:

- `pactl`
- `pamixer`

Install:

```bash
mkdir -p ~/.config/waybar/scripts
install -m755 waybar/volume-status.py ~/.config/waybar/scripts/volume-status.py
```

Replace `pulseaudio` with `custom/volume` in `modules-right`:

```jsonc
"modules-right": [
  "custom/volume"
]
```

Waybar snippet:

```jsonc
"custom/volume": {
  "exec": "python3 ~/.config/waybar/scripts/volume-status.py",
  "return-type": "json",
  "interval": 1,
  "on-click": "omarchy-launch-audio",
  "on-click-right": "pamixer -t",
  "on-scroll-up": "pamixer -i 5",
  "on-scroll-down": "pamixer -d 5",
  "tooltip": true
}
```

Optional CSS:

```css
#custom-volume {
  min-width: 28px;
}
```

Reload Waybar:

```bash
pkill -SIGUSR2 waybar
```

### Linear Brightness Controls

Omarchy's stock brightness controls operate directly on hardware backlight
percentages. On some panels, including `nvidia_wmi_ec_backlight`, that feels
non-linear: the top end changes slowly and the low end changes abruptly.

This repo keeps one shared gamma-corrected helper for display brightness:

- `omarchy/bin/omarchy-brightness-display`
- `waybar/brightness-status.py`
- `waybar/brightness-slider.py`
- `waybar/brightness-toggle.py`
- `waybar/examples/backlight-linear.jsonc`

The helper exposes adjusted user-facing percentages and maps them to raw
hardware backlight values with `OMARCHY_BRIGHTNESS_GAMMA` (default `2.2`). It
clamps normal brightness to `OMARCHY_BRIGHTNESS_MIN` (default `5`) as a real
hardware backlight floor, so normal brightness keys do not set the panel below
5%; display-off still uses the separate `off` action.

Install:

```bash
install -Dm755 omarchy/bin/omarchy-brightness-display ~/.local/bin/omarchy-brightness-display
install -Dm755 waybar/brightness-status.py ~/.config/waybar/scripts/brightness-status.py
install -Dm755 waybar/brightness-toggle.py ~/.config/waybar/scripts/brightness-toggle.py
install -Dm755 waybar/brightness-slider.py ~/.config/waybar/scripts/brightness-slider.py
```

Waybar snippet:

```jsonc
"custom/brightness": {
  "exec": "python3 ~/.config/waybar/scripts/brightness-status.py nvidia_wmi_ec_backlight",
  "return-type": "json",
  "on-click": "python3 ~/.config/waybar/scripts/brightness-toggle.py nvidia_wmi_ec_backlight",
  "on-scroll-up": "omarchy-brightness-display +5% nvidia_wmi_ec_backlight",
  "on-scroll-down": "omarchy-brightness-display 5%- nvidia_wmi_ec_backlight",
  "tooltip": true,
  "interval": 2
}
```

Fn brightness keys already call `omarchy-brightness-display` from Omarchy's
stock Hyprland media bindings. With `~/.local/bin` before Omarchy's bin
directory in `~/.config/uwsm/env`, this override applies to Fn keys, Waybar
scroll, and the slider. Change `OMARCHY_BRIGHTNESS_GAMMA` in one place to tune
the curve everywhere.

## Omarchy

Included files:

- `omarchy/bin/omarchy-powerprofiles-apply`
- `omarchy/bin/omarchy-powerprofiles-set`
- `omarchy/bin/omarchy-brightness-display`
- `omarchy/patches/omarchy-menu-power-profile.patch`
- `satty/config.toml`: enables Satty auto-close after save/copy (0.21.x+)

### Power Profile Fixes

These fix two separate issues in Omarchy's power profile flow:

1. `powerprofilesctl` can report a profile change while CPU governors remain stuck on `performance`, so the actual behavior does not change.
2. Walker can keep the visual focus on the first row, so the power menu can appear to highlight the wrong current profile.

### What The Fixes Do

- `omarchy-powerprofiles-apply` applies the requested profile and repairs the stuck-governor case before retrying.
- `omarchy-powerprofiles-set` routes AC and battery transitions through that helper.
- `omarchy-menu-power-profile.patch` makes the power menu put the current profile first and call the helper instead of raw `powerprofilesctl set`.

### Install

Copy the helper scripts into your Omarchy checkout:

```bash
install -Dm755 omarchy/bin/omarchy-powerprofiles-apply ~/.local/share/omarchy/bin/omarchy-powerprofiles-apply
install -Dm755 omarchy/bin/omarchy-powerprofiles-set ~/.local/share/omarchy/bin/omarchy-powerprofiles-set
```

Apply the menu patch from the Omarchy repo root:

```bash
cd ~/.local/share/omarchy
git apply /path/to/this/repo/omarchy/patches/omarchy-menu-power-profile.patch
```

Notes:

- The governor recovery path uses `sudo -n` when it is not already running as root.
- The helper only resets governors when a non-`performance` profile should be active and the kernel is still pinned to `performance`.

### Screenshot: Satty Save-As Defaults + Auto-Close

**Resolved upstream — no local fork needed as of Satty 0.21.0.**

The Save As filename prefill and remembered-directory behavior were merged into
Satty itself ([gabm/satty#499](https://github.com/gabm/satty/pull/499),
released in 0.21.0) and reached Arch `extra` in 0.21.1-1. If you are on Satty
≥ 0.21.0, drop the old custom scripts and use stock Omarchy plus one config
line.

**1. Save As defaults (native).**

Stock Omarchy already passes `--output-filename` to Satty, which is all the
merged feature needs. Satty now:

- Prefills the Save As filename from `--output-filename`.
- Remembers the last accepted Save As directory, stored in the XDG state dir
  (`~/.local/state/satty/save_as_last_dir`), and reopens there next time.

**2. Auto-close after save / copy / save-as.**

0.21.0 merged the old `--early-exit` / `--early-exit-save-as` flags into a
single `--early-exit [copy|save|save-as|all]` (bare = `all`). Stock Omarchy
does not pass it on the CLI, so set it once in `satty/config.toml`:

```toml
[general]
early-exit = true
```

Install (config only — the screenshot script is stock Omarchy):

```bash
install -Dm644 satty/config.toml ~/.config/satty/config.toml
```

Migration from the old local build:

```bash
rm -f ~/.local/bin/satty ~/.local/bin/omarchy-capture-screenshot
rm -f ~/.config/satty/save_as_last_dir   # 0.21.x uses ~/.local/state/satty/
```

The removed `--early-exit-save-as` flag means the old wrapper errors against
0.21.x, so this migration is required, not optional.

Notes:

- Historical: this started as a shell wrapper (`omarchy-cmd-screenshot`, using
  a `gsettings` filechooser hack) and then a patched Satty build. Both are
  retired now that the behavior is upstream.
- Earlier stale PRs on this topic: #2421, #3226.

## Hyprland

Config files that have **no upstream Omarchy equivalent**. Omarchy's
`omarchy-refresh-hyprland` can restore any of its own defaults, but it knows
nothing about these two, so this is their only backup.

Both are sourced from `~/.config/hypr/hyprland.conf`, after the Omarchy defaults
so they take precedence:

```
source = ~/.config/hypr/envs.conf
source = ~/.config/hypr/windows.conf
```

### `hypr/windows.conf`

Global window defaults plus per-app rules.

The two global rules at the top open new windows floating and disable all
transparency:

```
windowrule = float on, match:class .*
windowrule = opacity 1 1, match:class .*
```

The opacity rule is needed because Omarchy does not set
`decoration:active_opacity` (it is already `1.0`) — it tags every window with
`default-opacity` in `default/hypr/windows.conf` and then applies
`opacity 0.985 0.96` to that tag. The blanket rule overrides that and the
per-app browser rules.

**Rule order matters.** Hyprland applies matching rules in sequence, so the
blanket `float on` must stay above the per-app `tile on` rules. That is what
keeps the autostart chat apps tiled while everything else floats.

The per-app rules pin chat apps to workspaces 1 and 2, put Last War and
xclicker on workspaces 5 and 15, and disable blur/shadow on `steam_proton` for
performance. The app classes were found by trial and error and are not
guessable — Whatsie, for example, reports `com.ktechpit.whatsie`.

### `hypr/envs.conf`

`SDL_VIDEODRIVER=wayland` and a custom `OMARCHY_SCREENSHOT_DIR`.

Note Omarchy 4.0 ships a commented `OMARCHY_SCREENSHOT_DIR` slot in
`uwsm/default` — prefer that over a separate file when migrating.

### Install

```bash
cp hypr/windows.conf hypr/envs.conf ~/.config/hypr/
hyprctl reload
```

Then confirm both are sourced in `~/.config/hypr/hyprland.conf`.

Omarchy 4.0 replaces this `.conf` format with Lua and cannot source `.conf`
files from a `.lua` entry point, so these need translating rather than copying.
See [docs/customizations.md](docs/customizations.md).

## Tested On

- Omarchy 3.5.1
- Hyprland 0.54.1
- Waybar 0.15.0
- Arch Linux

## License

MIT
