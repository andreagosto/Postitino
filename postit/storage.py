import json
import os

from gi.repository import GLib

from .model import Note


def default_storage_path():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    d = os.path.join(base, "postit")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "notes.json")


class Storage:
    def __init__(self, path):
        self.path = path
        self.notes = {}
        self._timer = None
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        for d in data.get("notes", []):
            try:
                n = Note.from_dict(d)
            except Exception:
                continue
            self.notes[n.id] = n

    def save(self):
        data = {"notes": [n.to_dict() for n in self.notes.values()]}
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    def schedule_save(self):
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(400, self._flush)

    def _flush(self):
        self._timer = None
        self.save()
        return False

    def flush(self):
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = None
        self.save()
