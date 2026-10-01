# Changelog

All notable changes to **Postitino** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-10-01

### Fixed
- **Font Resizing Engine**: Switched to GTK `TextTag` (`size-points`) and `Pango.AttrList` for reliable and dynamic text scaling across text notes, task rows, and entry fields.
- **Position Retention on Hide/Show**: Fixed window coordinates loss when hiding notes via the close button (`×`) or tray menu; notes now accurately remember and restore their exact screen positions when toggled.
- **Native About Dialog**: Replaced basic message dialog with a fully-featured native `Gtk.AboutDialog`, fixing an empty popup issue caused by unsupported markup tags.
- **Multi-Keyboard & Mouse Wheel Zoom**: Added `Ctrl` + mouse scroll wheel zooming over notes and ensured `Ctrl++` works across varying keyboard layouts regardless of Shift modifier state.

---

## [1.0.0] - 2026-10-01

### Added
- **Multi-Note Support**: Multiple independent sticky notes on the desktop, each customizable as a text note or a to-do list.
- **Interactive To-Do Lists**: Checkboxes with strikethrough styling, task reordering via Drag & Drop grip handles (`⋮⋮`) and keyboard shortcuts (`Alt+Up` / `Alt+Down`).
- **One-Click Clear Completed**: Dedicated button and menu option to quickly clean up finished tasks.
- **System Tray Integration**: Native Ayatana / AppIndicator tray icon with "New note", "Show all notes", "Hide all notes", and direct note visibility toggling (`✓`).
- **Dynamic Text Zoom**: Per-note font resizing (`Ctrl++`, `Ctrl+-`, `Ctrl+0`, `Ctrl+Scroll`).
- **Straight Note Option**: Toggle note rotation to 0° with one click from the menu.
- **Quick Copy to Clipboard (`Ctrl+Shift+C`)**: Export note text or markdown-formatted checklists (`- [ ]`, `- [x]`).
- **Automatic Persistence & Backup**: Local auto-saving with debounce to `~/.local/share/postit/notes.json` with fallback backup (`notes.json.bak`).
- **Desktop Stuck & Always on Top**: Runs in the desktop layer without interfering with windows, with per-note "Always on top" mode.
- **Delete Confirmation Dialog**: Protection against accidental note deletion (`Ctrl+Shift+D`).
- **Realistic Paper Aesthetic**: Hand-cut irregular edges, realistic drop shadows, adhesive tape, and paper colors (yellow, pink, blue, green, white) drawn via Cairo.
- **XWayland Backend Enforcement**: Automatic backend selection to ensure "Always on top" and mouse clicks work properly under GNOME Wayland sessions.
- **Bilingual UI**: English default with built-in Italian localization based on system locale or `POSTIT_LANG`.
