import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gtk

from .lang import tr
from .model import Note
from .note_window import NoteWindow
from .storage import Storage, default_storage_path

APP_ID = os.environ.get("POSTIT_APP_ID", "it.andrea.postitino")
ICON_NAME = "it.andrea.postitino"
ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postitino.svg"
)

CSS = b"""
#postit-paper { background: transparent; }
#postit-paper textview,
#postit-paper textview text,
#postit-paper view,
#postit-paper scrolledwindow,
#postit-paper list,
#postit-paper list row,
#postit-paper box,
#postit-paper checkbutton,
#postit-paper eventbox {
    background-color: transparent;
    background-image: none;
}
#postit-paper button { background: transparent; border: none; box-shadow: none; padding: 2px; }
#postit-paper button:hover { background-color: rgba(0, 0, 0, 0.10); }
#postit-paper #postit-drag-handle { opacity: 0.40; }
#postit-paper #postit-drag-handle:hover { opacity: 0.95; }
#postit-paper entry { background-color: rgba(255, 255, 255, 0.45);
                      border: none; border-radius: 4px; box-shadow: none; padding: 3px 6px; }
#postit-paper #postit-mode { color: rgba(0, 0, 0, 0.55); font-size: 10px; font-weight: bold; }
#postit-paper #postit-title {
    background-color: transparent;
    color: rgba(0, 0, 0, 0.85);
    font-weight: bold;
    caret-color: rgba(0, 0, 0, 0.7);
    padding: 0 4px;
    border: none;
}
#postit-paper #postit-title:focus {
    background-color: rgba(255, 255, 255, 0.35);
    border-radius: 4px;
}
window.popup menu {
    background-color: #f6f6f6;
    background-image: none;
    color: #2e3436;
}
window.popup menu > menuitem {
    background-color: transparent;
    color: #2e3436;
    padding: 5px 10px;
}
window.popup menu > menuitem:hover {
    background-color: #3584e4;
    color: #ffffff;
}
"""


class PostItApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.storage = Storage(default_storage_path())
        self.windows = {}
        self._started = False
        self._cascade = 0
        self._tray = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.hold()
        self._setup_icon()
        self._setup_css()
        self._setup_tray()

    def _setup_icon(self):
        try:
            if os.path.exists(ICON_PATH):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(ICON_PATH)
                Gtk.Window.set_default_icon(pixbuf)
        except Exception:
            pass

    def do_activate(self):
        if not self._started:
            self._started = True
            self.restore()
        else:
            self.new_note()

    def do_shutdown(self):
        for win in self.windows.values():
            if win.get_visible():
                pos = win.get_position()
                if pos and (pos[0] != 0 or pos[1] != 0):
                    win.note.x, win.note.y = pos[0], pos[1]
        self.storage.flush()
        Gtk.Application.do_shutdown(self)

    # ------------------------------------------------------------- windows

    def restore(self):
        if not self.storage.notes:
            n = Note()
            self.storage.notes[n.id] = n
            self.storage.schedule_save()
        if all(not getattr(n, "visible", True) for n in self.storage.notes.values()):
            first = next(iter(self.storage.notes.values()))
            first.visible = True
        for n in self.storage.notes.values():
            self.open_window(n)

    def new_note(self):
        n = Note()
        self.storage.notes[n.id] = n
        self.storage.schedule_save()
        return self.open_window(n)

    def open_window(self, note):
        if note.x is None or note.y is None:
            screen = Gdk.Screen.get_default()
            geo = screen.get_monitor_geometry(screen.get_primary_monitor())
            step = (self._cascade % 12) * 30
            self._cascade += 1
            note.x = geo.x + 130 + step
            note.y = geo.y + 130 + step
        win = NoteWindow(self, note)
        win.connect("destroy", self._on_window_destroyed, note)
        self.windows[note.id] = win
        if getattr(note, "visible", True):
            win.show_all()
        else:
            win.realize()
        self.update_tray()
        return win

    def _on_window_destroyed(self, win, note):
        self.windows.pop(note.id, None)
        self.update_tray()

    def delete_note(self, win):
        note = win.note
        self.storage.notes.pop(note.id, None)
        self.save()
        self.windows.pop(note.id, None)
        win.destroy()
        self.update_tray()

    def save(self):
        self.storage.schedule_save()

    def quit_app(self):
        self.quit()

    # ------------------------------------------------------------ styling

    def _setup_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # ---------------------------------------------------------------- tray

    def _setup_tray(self):
        AppIndicator = None
        for name in ("AyatanaAppIndicator3", "AppIndicator3"):
            try:
                gi.require_version(name, "0.1")
                mod = __import__("gi.repository", fromlist=[name])
                AppIndicator = getattr(mod, name)
                break
            except (ImportError, ValueError):
                continue
        if not AppIndicator:
            return

        self._AppIndicator = AppIndicator
        self._tray = AppIndicator.Indicator.new(
            APP_ID,
            ICON_NAME,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self._tray.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.update_tray()

    def update_tray(self):
        if not self._tray:
            return
        menu = Gtk.Menu()

        m_new = Gtk.MenuItem(label=tr("new_note_menu"))
        m_new.connect("activate", lambda *a: self.new_note())
        menu.append(m_new)

        m_show_all = Gtk.MenuItem(label=tr("show_all_notes"))
        m_show_all.connect("activate", lambda *a: self.show_all_notes())
        menu.append(m_show_all)

        m_hide_all = Gtk.MenuItem(label=tr("hide_all_notes"))
        m_hide_all.connect("activate", lambda *a: self.hide_all_notes())
        menu.append(m_hide_all)

        menu.append(Gtk.SeparatorMenuItem())

        notes_menu = Gtk.Menu()
        has_notes = False
        for note_id, note in self.storage.notes.items():
            has_notes = True
            title = note.title.strip()
            if not title:
                if note.type == "todo":
                    first_text = note.items[0].text.strip() if note.items else ""
                    title = f"[{tr('mode_todo')}] " + (first_text[:18] + "…" if first_text else tr("untitled"))
                else:
                    first_line = note.content.strip().split("\n")[0] if note.content.strip() else ""
                    title = first_line[:20] + "…" if first_line else tr("untitled")
            prefix = "✓ " if getattr(note, "visible", True) else "   "
            item = Gtk.MenuItem(label=f"{prefix}{title}")
            item.connect("activate", self._on_tray_toggle_note, note_id)
            notes_menu.append(item)

        m_notes = Gtk.MenuItem(label=tr("notes"))
        m_notes.set_submenu(notes_menu)
        if not has_notes:
            m_notes.set_sensitive(False)
        menu.append(m_notes)

        menu.append(Gtk.SeparatorMenuItem())

        m_quit = Gtk.MenuItem(label=tr("quit"))
        m_quit.connect("activate", lambda *a: self.quit())
        menu.append(m_quit)

        menu.show_all()
        self._tray.set_menu(menu)

    def show_all_notes(self):
        for note in self.storage.notes.values():
            win = self.windows.get(note.id)
            if win:
                win.show_note()
            else:
                note.visible = True
                self.open_window(note)
        self.save()
        self.update_tray()

    def hide_all_notes(self):
        for win in list(self.windows.values()):
            if win.get_visible():
                win.hide_note()
        self.save()
        self.update_tray()

    def _on_tray_toggle_note(self, item, note_id):
        win = self.windows.get(note_id)
        note = self.storage.notes.get(note_id)
        if not note:
            return
        if not win:
            note.visible = True
            self.open_window(note)
        elif win.get_visible():
            win.hide_note()
        else:
            win.show_note()


def main():
    app = PostItApp()
    return app.run(None)
