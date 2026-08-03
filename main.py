#!/usr/bin/env python3
import os
import sys

# On Wayland sessions GTK3 runs as a native client where
# gtk_window_set_keep_above is a no-op: "always on top" would not work.
# Using the X11 backend (via XWayland) the window manager handles both the
# desktop level and keep_above (_NET_WM_STATE_ABOVE). Force x11 only when a
# DISPLAY is available. Overridable with the POSTIT_BACKEND variable.
if os.environ.get("POSTIT_BACKEND"):
    os.environ["GDK_BACKEND"] = os.environ["POSTIT_BACKEND"]
elif os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" and os.environ.get("DISPLAY"):
    os.environ["GDK_BACKEND"] = "x11"

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")

from postit.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
