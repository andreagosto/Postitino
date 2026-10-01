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
        "straight_note": "Straight note (0°)",
        "color": "Color",
        "text_note": "Text note",
        "todo_list": "To-do list",
        "note_type": "Note type",
        "clear_completed": "Clear completed",
        "copy_content": "Copy note (Ctrl+Shift+C)",
        "text_size": "Text size",
        "font_larger": "Larger (Ctrl++)",
        "font_smaller": "Smaller (Ctrl+-)",
        "font_normal": "Reset size (Ctrl+0)",
        "delete_note": "Delete note",
        "confirm_delete_note": "Are you sure you want to delete this note?",
        "show_all_notes": "Show all notes",
        "hide_all_notes": "Hide all notes",
        "notes": "Notes",
        "untitled": "Untitled",
        "drag_to_reorder": "Drag or Alt+Up/Down to reorder",
        "quit_app": "Quit app",
        "quit": "Quit",
        "about": "About Postitino",
        "about_text": (
            "Realistic desktop sticky notes for Ubuntu / GNOME.\n\n"
            "Features:\n"
            "• Text notes and to-do lists with checkboxes\n"
            "• Drag & drop task reordering (and Alt+Up/Down)\n"
            "• Per-note text size zoom (Ctrl++, Ctrl+-, Ctrl+Scroll)\n"
            "• Customizable paper colors and straight note toggle\n"
            "• Desktop pinned mode and Always on top\n"
            "• Automatic local persistence and safety backups\n\n"
            "Developed with AI pair programming (DeepSeek Flash)."
        ),
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
        "straight_note": "Nota dritta (0°)",
        "color": "Colore",
        "text_note": "Nota di testo",
        "todo_list": "Lista to-do",
        "note_type": "Tipo di nota",
        "clear_completed": "Cancella completati",
        "copy_content": "Copia nota (Ctrl+Shift+C)",
        "text_size": "Dimensione testo",
        "font_larger": "Ingrandisci (Ctrl++)",
        "font_smaller": "Rimpicciolisci (Ctrl+-)",
        "font_normal": "Reimposta (Ctrl+0)",
        "delete_note": "Elimina nota",
        "confirm_delete_note": "Sei sicuro di voler eliminare questa nota?",
        "show_all_notes": "Mostra tutte le note",
        "hide_all_notes": "Nascondi tutte le note",
        "notes": "Note",
        "untitled": "Senza titolo",
        "drag_to_reorder": "Trascina o Alt+Su/Giù per riordinare",
        "quit_app": "Esci dall'app",
        "quit": "Esci",
        "about": "Informazioni su Postitino",
        "about_text": (
            "Note adesive realistiche per il desktop Ubuntu / GNOME.\n\n"
            "Caratteristiche:\n"
            "• Note di testo e liste to-do con caselle di spunta\n"
            "• Riordino dei task via drag & drop (e Alt+Su/Giù)\n"
            "• Zoom del testo per singola nota (Ctrl++, Ctrl+-, Ctrl+Rotellina)\n"
            "• Colori della carta personalizzati e opzione nota dritta\n"
            "• Modalità ancorata al desktop o sempre in primo piano\n"
            "• Persistenza automatica locale con backup di sicurezza\n\n"
            "Sviluppato con pair programming IA (DeepSeek Flash)."
        ),
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
