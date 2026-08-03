# Post-it for Ubuntu (GNOME)

Desktop sticky notes for Ubuntu: quick notes and to-do lists with checkboxes.
Written in **Python + GTK3**, auto-saved to a local JSON file at
`~/.local/share/postit/notes.json`.

The interface is **English by default** and comes with a built-in **Italian
translation** (picked from your system locale, see
[Localization](#localization)).

## AI Attribution

> **This project was developed entirely by an AI assistant — DeepSeek Flash.**
>
> All the code (UI, GTK/Cairo drawing, persistence, localization), the
> setup script and this documentation were written by DeepSeek Flash
> (DeepSeek V4 Flash, model `deepseek/deepseek-v4-flash`), guided by an
> Italian user who reviewed, tested and refined the result.

## Features

- **Multiple independent notes**, each in its own window.
- Every note can be a **text note** or a **to-do list** (checkboxes).
- **Automatic persistence**: every change is saved on its own (notes come
  back where you left them after a restart).
- **Stuck to the desktop**: by default notes sit in the desktop layer — you
  only see them when the desktop is clean (not on top of windows). From each
  note's menu you can enable **"Always on top"**, just like a terminal.
- **Realistic look**: irregular hand-cut edges, drop shadow, tape and a
  slight rotation — like a real sticky note stuck on a wall.
- Customizable paper color (yellow, pink, blue, green, white).

## Installation

```bash
cd ~/IA/Post-it
chmod +x install.sh
./install.sh
```

The script installs missing dependencies, creates the applications-menu entry
and enables autostart at login.

### Dependencies (to install manually)

```bash
sudo apt install python3-gi python3-gi-cairo python3-cairo \
    gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

> **Important**: `python3-gi-cairo` is required (the paper is drawn with
> `cairo.Context`). If you see
> `Couldn't find foreign struct converter for 'cairo.Context'`,
> that package is missing.

## Usage

| Action | How |
|---|---|
| Launch | `python3 ~/IA/Post-it/main.py` (or from the applications menu) |
| New note | Run `main.py` again, press the **+** button on a note, or use the menu → **New note** |
| Hide a note | **×** button (it stays saved) |
| Delete | Menu (⋮) → **Delete note** |
| Change type/color/fix | Menu (⋮) → Note type / Color / Always on top |
| Move a note | Drag the top bar |
| Quit | Menu (⋮) → **Quit app** (or the tray icon, if available) |

> **Tray icon note**: it works if you have the *AppIndicator* GNOME
> extension (enabled by default on Ubuntu).

> **Single-instance note**: the app is a single instance. If it is already
> running, running `main.py` again does not open a second copy — it just
> creates a new note in the running instance. (For multiple test instances:
> `POSTIT_APP_ID=... python3 main.py`.)

## Localization

The UI language is detected from your environment:

- `POSTIT_LANG=en|it` takes precedence if set.
- Otherwise the system locale (`LC_ALL`, `LC_MESSAGES`, `LANG`) is used.

Examples:

```bash
POSTIT_LANG=it python3 main.py    # force Italian
POSTIT_LANG=en python3 main.py    # force English
```

## Desktop behaviour (Wayland vs Xorg)

The app handles compatibility with your environment automatically:

- On **Xorg** it runs directly on the X11 backend: desktop level and
  "always on top" work 100%.
- On **Wayland** (default GNOME session) GTK3 runs as a native Wayland
  client, where *`set_keep_above` is a no-op*: "always on top" would not
  work. The app therefore **automatically forces the X11 backend (via
  XWayland)**, which GNOME's window manager handles correctly.

The "desktop level" is implemented as an **undecorated normal window** (no
`_NET_WM_WINDOW_TYPE_DESKTOP`, no `keep_below`): on GNOME Shell those
mechanisms put the window *below* the desktop (Nautilus, fullscreen), making
it **unresponsive to the mouse**. A normal window always receives clicks and
typing; other windows cover it when you open them (the "stuck to the
desktop" behaviour). "Always on top" uses `keep_above`.

You can force the backend manually with `POSTIT_BACKEND`
(e.g. `POSTIT_BACKEND=wayland python3 main.py`).

## Structure

```
main.py              entry point (backend selection)
postit/app.py        application (multi-note, tray, css)
postit/note_window.py note window (text/todo, menu)
postit/paper.py      paper drawing (cairo)
postit/model.py      data: Note and TodoItem
postit/storage.py    JSON persistence
postit/lang.py       UI localization (EN/IT)
install.sh           setup + autostart
```

## Roadmap (ideas)

- Cloud / database sync
- Drag & drop reordering of tasks
- Due dates / reminders
