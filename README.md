# Omarchy Fixes

Small fixes I keep around for an Omarchy setup.

This repo currently has two buckets:

- `waybar/`: custom Waybar widgets and config snippets
- `omarchy/`: power profile fixes for Omarchy's menu and resume flow

## Waybar

Included files:

- `waybar/keyboard-layout.sh`: reliable keyboard layout indicator for Hyprland
- `waybar/cpu-status.py`: CPU widget showing total usage % next to the icon, with per-core hover details and short load graphs
- `waybar/examples/memory-builtin.jsonc`: built-in Waybar memory widget example
- `waybar/examples/memory-builtin.css`: matching memory widget colors

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

## Omarchy

Included files:

- `omarchy/bin/omarchy-powerprofiles-apply`
- `omarchy/bin/omarchy-powerprofiles-set`
- `omarchy/bin/omarchy-cmd-screenshot`
- `omarchy/default/systemd/system-sleep/resume-boost`
- `omarchy/patches/omarchy-menu-power-profile.patch`

### Power Profile Fixes

These fix two separate issues in Omarchy's power profile flow:

1. `powerprofilesctl` can report a profile change while CPU governors remain stuck on `performance`, so the actual behavior does not change.
2. Walker can keep the visual focus on the first row, so the power menu can appear to highlight the wrong current profile.

### What The Fixes Do

- `omarchy-powerprofiles-apply` applies the requested profile and repairs the stuck-governor case before retrying.
- `omarchy-powerprofiles-set` routes AC and battery transitions through that helper.
- `resume-boost` uses the same helper when switching to `performance` on resume and when restoring the prior profile.
- `omarchy-menu-power-profile.patch` makes the power menu put the current profile first and call the helper instead of raw `powerprofilesctl set`.

### Install

Copy the helper scripts into your Omarchy checkout:

```bash
install -Dm755 omarchy/bin/omarchy-powerprofiles-apply ~/.local/share/omarchy/bin/omarchy-powerprofiles-apply
install -Dm755 omarchy/bin/omarchy-powerprofiles-set ~/.local/share/omarchy/bin/omarchy-powerprofiles-set
install -Dm755 omarchy/default/systemd/system-sleep/resume-boost ~/.local/share/omarchy/default/systemd/system-sleep/resume-boost
```

Apply the menu patch from the Omarchy repo root:

```bash
cd ~/.local/share/omarchy
git apply /path/to/this/repo/omarchy/patches/omarchy-menu-power-profile.patch
```

Notes:

- The governor recovery path uses `sudo -n` when it is not already running as root.
- The helper only resets governors when a non-`performance` profile should be active and the kernel is still pinned to `performance`.

### Screenshot: Save-As Directory Memory + Auto-Close

Customized fork of Omarchy's `omarchy-cmd-screenshot`. Two quality-of-life
fixes for the satty editor path; the rest of the script is unchanged from
upstream.

**1. Remember the last "Save As" directory.**

The default GTK4 file chooser opens in `recent`, which means every "Save As"
starts somewhere unrelated to where you last saved a screenshot. This fork:

- Reads the last directory from `~/.config/omarchy/screenshot_last_dir`.
- Sets `org.gtk.gtk4.Settings.FileChooser startup-mode 'cwd'` and `cd`s into
  that directory before launching satty, so the file chooser opens there.
- After satty exits, restores `startup-mode 'recent'` and scans
  `~/.local/share/recently-used.xbel` for an image file saved during this
  invocation. If found, its directory is written back to the state file.

**2. Auto-close satty after save / copy / save-as.**

Satty 0.20.1 split the old `--early-exit` behavior into separate flags. This
fork passes both `--early-exit` and `--early-exit-save-as`, and changes
`--actions-on-enter` from `save-to-clipboard` to `save-to-clipboard,exit`
as a belt-and-suspenders for the Enter path.

Install:

```bash
install -Dm755 omarchy/bin/omarchy-cmd-screenshot ~/.local/bin/omarchy-cmd-screenshot
```

The install path is `~/.local/bin/`, not `~/.local/share/omarchy/bin/`. This
is intentional: `~/.local/bin/` shadows the Omarchy command on `PATH`, so the
override survives `omarchy-update` instead of being overwritten on every
update.

**Important — make sure `~/.local/bin` is on Hyprland's PATH.** Omarchy's
`~/.config/uwsm/env` ships with:

```sh
export PATH=$OMARCHY_PATH/bin/:$PATH
```

That prepends the omarchy bin dir but does *not* add `~/.local/bin`, which
also is not on the default systemd user PATH. Without this, `which
omarchy-cmd-screenshot` in your shell will return the override but Hyprland
keybindings (PRINT etc.) will still execute the omarchy-shipped script.

Patch `~/.config/uwsm/env`:

```sh
export PATH=$HOME/.local/bin:$OMARCHY_PATH/bin/:$PATH
```

Relaunch Hyprland (logout / `uwsm stop`) for the change to take effect.

Notes:

- State file: `~/.config/omarchy/screenshot_last_dir`. Safe to delete to
  reset back to `~/Pictures` (or whatever `OMARCHY_SCREENSHOT_DIR` is set to).
- The directory tracking depends on GTK writing to `recently-used.xbel`,
  which it does for the standard GTK4 file chooser.
- This is a candidate for an upstream PR. Earlier related PRs (#2421, #3226)
  are stale; the save-as-directory behavior in particular is fresh ground.

## Tested On

- Omarchy 3.5.1
- Hyprland 0.54.1
- Waybar 0.15.0
- Arch Linux

## License

MIT
