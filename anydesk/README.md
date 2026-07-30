# AnyDesk 100% Scale and Dark Theme Notes

Last updated: 2026-07-01

This documents the AnyDesk launcher fix used on this Omarchy/Hyprland system.
It pins AnyDesk to 100% UI scaling and applies the best available dark GTK
theme override.

## Installed Files

The working setup is generated from one Omarchy post-update hook:

- `~/.config/omarchy/hooks/post-update.d/anydesk-100scale`

That hook writes or refreshes these user-level files:

- `~/.local/bin/anydesk-100scale`
- `~/.local/share/applications/anydesk.desktop`
- `~/.config/anydesk-gtk-dark/gtk-3.0/settings.ini`
- `~/.config/anydesk-gtk-dark/gtk-3.0/gtk.css`
- `~/.anydesk/user.conf`

The repo copy of the hook is:

- `anydesk/anydesk-100scale-post-update`

## What Works

The reliable fix is to launch AnyDesk through a wrapper instead of launching
`/usr/bin/anydesk` directly.

The wrapper does three important things:

- Forces the GTK/X11 path with `GDK_BACKEND=x11` and `unset WAYLAND_DISPLAY`.
- Pins all known GTK and Qt scale variables to `1`.
- Points `XDG_CONFIG_HOME` at an app-specific GTK config directory, so the
  dark CSS affects AnyDesk without changing the rest of the desktop.

The hook also writes these AnyDesk config keys every time:

```ini
ad.ui.scale=100
ad.ui.theme=1
```

The desktop file override is important because app launchers, MIME links, and
`anydesk://` links otherwise keep using the vendor desktop file after updates.
The override sets:

```ini
Exec=/home/vladkarok/.local/bin/anydesk-100scale %u
MimeType=x-scheme-handler/anydesk;
X-Omarchy-User-Override=100-percent-scale-dark
```

## Dark Theme Result

The Linux app does not expose the same polished dark mode as Windows. The best
working path is a local GTK 3 CSS override with a warm AnyDesk-like palette.
The design rule is **dark base + warmth from elevated surfaces** (not a lifted
base): the base must stay dark so overlay text stays readable.

- base background: `#191817`
- top/header background: `#141312`
- elevated surface (cards/popovers/selection): `#33302a`
- entry background: `#121110`
- strong text: `#f4f2ee`
- accent red: `#ff3f39`

This improves the main surface, text contrast, separators, inputs, scrollbars,
tooltips, and most GTK-painted buttons. The connection and error states stay
readable against the dark background.

Some square toolbar/action buttons still remain bright. Broader selectors such
as `window .button`, `window .white`, `window button.white`, and similar GTK
class selectors did not change them. That strongly suggests AnyDesk paints
those controls through embedded styling/assets or private widget CSS that the
normal user GTK provider cannot override cleanly.

## The Connecting / Client-Offline Panel Cannot Be Carded

The status overlays ("Connecting…", "Client Offline", "Not supported") merge
into the dark background — they have no distinct card rectangle like the
Windows/default look. This was investigated exhaustively with per-widget
diagnostic CSS (recoloring each selector loudly and screenshotting):

- The panels **are** GTK widgets: their background is a `box` and their text is
  a `label` (both took diagnostic colors), so they are themeable in principle.
- They are **not** `GtkDialog`/`messagedialog` — dialog selectors did not touch
  them.
- They have **no addressable handle**: AnyDesk's internal names (`connect_panel`,
  `triggered_alert_view`, `welcome_panel`, found via `strings /usr/bin/anydesk`)
  are C++ symbols, **not** GTK widget names — `#connect_panel` etc. do nothing.
  No style class (`.white`, `.card`, …) and no shallow structural selector
  (`overlay > box`) isolates them either; they are deeply nested plain boxes,
  indistinguishable from every other `box`.
- Root cause of the merge: our user CSS loads at GTK **USER** priority and its
  `box { background: … }` rule overrides AnyDesk's own **APPLICATION**-priority
  styling that colors these panels in the default theme. USER always beats
  APPLICATION, and with nothing to re-target, they cannot be re-distinguished.

Consequence — a genuine either/or, same class of limit as the white buttons:

- Force-dark all boxes → good dark main UI, but status panels merge (chosen).
- Do not override `box` → panels keep their distinct default card, but the whole
  app reverts toward the light-grey vendor default.

The achievable mitigation (applied): keep the base dark and the status **label**
bright (`ad_text_strong`), so "Connecting…" text stays legible even without a
card behind it.

## Wrong Paths Tried

These were tested and are not enough by themselves:

- Only setting `ad.ui.theme=1`: AnyDesk accepts the key, but Linux UI coverage is
  incomplete.
- Only setting `GTK_THEME=Adwaita-dark`: some widgets change, but the app stays
  visually mixed and too light.
- Using the global desktop GTK theme: affects the rest of the system and still
  does not fully fix AnyDesk.
- Using Qt-only variables: AnyDesk did not behave like a normal Qt app for this
  UI.
- Adding CSS `!important`: GTK 3 rejects this syntax with parse errors.
- Styling `.white`, `.lightgrey`, `.button`, `.image-button`, and related
  selectors: valid CSS, but the remaining bright AnyDesk toolbar controls do
  not respond.

## Why the Hook Exists

AnyDesk updates can replace the vendor desktop file or change launch behavior.
Omarchy updates can also refresh desktop integration. Keeping the fix in
`~/.config/omarchy/hooks/post-update.d/` makes it easy to reapply after updates
without editing Omarchy source files under `~/.local/share/omarchy/`.

The hook is idempotent. It can be run repeatedly.

## Reinstall Steps

After a fresh system install:

1. Install AnyDesk first, so `/usr/bin/anydesk` exists.
2. Clone or copy this repo.
3. From the repo root, install and run the hook:

```bash
install -Dm755 anydesk/anydesk-100scale-post-update ~/.config/omarchy/hooks/post-update.d/anydesk-100scale
~/.config/omarchy/hooks/post-update.d/anydesk-100scale
```

4. Validate the generated files:

```bash
desktop-file-validate ~/.local/share/applications/anydesk.desktop
bash -n ~/.local/bin/anydesk-100scale
bash -n ~/.config/omarchy/hooks/post-update.d/anydesk-100scale
```

5. Launch AnyDesk from the app launcher or with:

```bash
gtk-launch anydesk
```

## Quick Checks

Check that AnyDesk links use the user desktop override:

```bash
xdg-mime query default x-scheme-handler/anydesk
```

Expected:

```text
anydesk.desktop
```

Check the scale and theme keys:

```bash
grep -E '^(ad\.ui\.scale|ad\.ui\.theme)=' ~/.anydesk/user.conf
```

Expected:

```text
ad.ui.scale=100
ad.ui.theme=1
```

## If It Breaks Again

First rerun the hook:

```bash
~/.config/omarchy/hooks/post-update.d/anydesk-100scale
```

Then launch with:

```bash
gtk-launch anydesk
```

If scaling breaks, inspect the wrapper and desktop file first. If colors break,
inspect `~/.config/anydesk-gtk-dark/gtk-3.0/gtk.css` and launch AnyDesk from a
terminal to catch GTK CSS parse warnings.

