import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

from .model import Note
from .note_window import NoteWindow
from .storage import Storage, default_storage_path

APP_ID = os.environ.get("POSTIT_APP_ID", "it.andrea.postit")

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
#postit-paper textview text { font-size: 13px; }
#postit-paper button { background: transparent; border: none; box-shadow: none; padding: 2px; }
#postit-paper button:hover { background-color: rgba(0, 0, 0, 0.10); }
#postit-paper entry { background-color: rgba(255, 255, 255, 0.45);
                      border: none; border-radius: 4px; box-shadow: none; padding: 3px 6px; }
#postit-paper #postit-mode { color: rgba(0, 0, 0, 0.55); font-size: 10px; font-weight: bold; }
#postit-paper #postit-title {
    background-color: transparent;
    color: rgba(0, 0, 0, 0.85);
    font-size: 15px;
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
        self._setup_css()
        self._setup_tray()

    def do_activate(self):
        if not self._started:
            self._started = True
            self.restore()
        else:
            self.new_note()

    def do_shutdown(self):
        self.storage.flush()
        Gtk.Application.do_shutdown(self)

    # ------------------------------------------------------------- windows

    def restore(self):
        if not self.storage.notes:
            n = Note()
            self.storage.notes[n.id] = n
            self.storage.schedule_save()
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
        win.show_all()
        return win

    def _on_window_destroyed(self, win, note):
        self.windows.pop(note.id, None)

    def delete_note(self, win):
        note = win.note
        self.storage.notes.pop(note.id, None)
        self.save()
        win.destroy()

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
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3
        except (ImportError, ValueError):
            return
        menu = Gtk.Menu()
        m_new = Gtk.MenuItem("Nuova nota")
        m_new.connect("activate", lambda *a: self.new_note())
        menu.append(m_new)
        menu.append(Gtk.SeparatorMenuItem())
        m_quit = Gtk.MenuItem("Esci")
        m_quit.connect("activate", lambda *a: self.quit())
        menu.append(m_quit)
        menu.show_all()

        ind = AppIndicator3.Indicator.new(
            "it.andrea.postit",
            "accessories-text-editor",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        ind.set_menu(menu)
        self._tray = ind


def main():
    app = PostItApp()
    return app.run(None)
