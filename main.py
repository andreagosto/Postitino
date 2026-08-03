#!/usr/bin/env python3
import os
import sys

# Su sessione Wayland, GTK3 gira come client nativo dove gtk_window_set_keep_above
# e' un no-op: "sempre in primo piano" non funziona. Usando il backend X11
# (via XWayland) il window manager gestisce sia il livello desktop sia
# keep_above (_NET_WM_STATE_ABOVE). Forziamo x11 solo quando c'e' un DISPLAY.
# Sovrascrivibile con la variabile POSTIT_BACKEND.
if os.environ.get("POSTIT_BACKEND"):
    os.environ["GDK_BACKEND"] = os.environ["POSTIT_BACKEND"]
elif os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" and os.environ.get("DISPLAY"):
    os.environ["GDK_BACKEND"] = "x11"

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")

from postit.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
