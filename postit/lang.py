"""Lightweight UI localization (English default, Italian built-in).

Language is picked from the POSTIT_LANG environment variable first, then
from the system locale (LC_MESSAGES/LANG). All UI strings go through tr().
"""
import os

STRINGS = {
    "en": {
        "new_note": "New note",
        "hide": "Hide",
        "title_placeholder": "Title…",
        "add_todo": "Add task…",
        "add": "Add",
        "remove": "Remove",
        "new_note_menu": "New note",
        "always_on_top": "Always on top",
        "color": "Color",
        "text_note": "Text note",
        "todo_list": "To-do list",
        "note_type": "Note type",
        "delete_note": "Delete note",
        "quit_app": "Quit app",
        "quit": "Quit",
        "mode_todo": "TO-DO",
        "mode_note": "NOTE",
        "missing_gi_cairo": (
            "Missing package 'python3-gi-cairo'.\n"
            "Install it with:  sudo apt install python3-gi-cairo\n"
            "Or run:          ./install.sh"
        ),
    },
    "it": {
        "new_note": "Nuova nota",
        "hide": "Nascondi",
        "title_placeholder": "Titolo…",
        "add_todo": "Aggiungi task…",
        "add": "Aggiungi",
        "remove": "Rimuovi",
        "new_note_menu": "Nuova nota",
        "always_on_top": "Sempre in primo piano",
        "color": "Colore",
        "text_note": "Nota di testo",
        "todo_list": "Lista to-do",
        "note_type": "Tipo di nota",
        "delete_note": "Elimina nota",
        "quit_app": "Esci dall'app",
        "quit": "Esci",
        "mode_todo": "TO-DO",
        "mode_note": "NOTA",
        "missing_gi_cairo": (
            "Manca il pacchetto 'python3-gi-cairo'.\n"
            "Installalo con:  sudo apt install python3-gi-cairo\n"
            "Oppure esegui:   ./install.sh"
        ),
    },
}

_SUPPORTED = ("en", "it")


def detect_language():
    env = os.environ.get("POSTIT_LANG", "").strip().lower()
    if env:
        return env if env in _SUPPORTED else "en"
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        code = val.split("_")[0].split(".")[0].lower()
        if code in _SUPPORTED:
            return code
    return "en"


LANG = detect_language()
_TABLE = STRINGS.get(LANG, STRINGS["en"])


def tr(key):
    return _TABLE.get(key, STRINGS["en"].get(key, key))
