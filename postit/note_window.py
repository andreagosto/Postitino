import math
import os
import random

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango

from .lang import tr
from .model import TodoItem
from .paper import COLORS, PostItPaper


class NoteWindow(Gtk.Window):
    RESIZE_THICKNESS = 10
    CORNER_SIZE = 14
    EDGE_CURSORS = {
        Gdk.WindowEdge.NORTH_WEST: Gdk.CursorType.TOP_LEFT_CORNER,
        Gdk.WindowEdge.NORTH: Gdk.CursorType.TOP_SIDE,
        Gdk.WindowEdge.NORTH_EAST: Gdk.CursorType.TOP_RIGHT_CORNER,
        Gdk.WindowEdge.EAST: Gdk.CursorType.RIGHT_SIDE,
        Gdk.WindowEdge.SOUTH_EAST: Gdk.CursorType.BOTTOM_RIGHT_CORNER,
        Gdk.WindowEdge.SOUTH: Gdk.CursorType.BOTTOM_SIDE,
        Gdk.WindowEdge.SOUTH_WEST: Gdk.CursorType.BOTTOM_LEFT_CORNER,
        Gdk.WindowEdge.WEST: Gdk.CursorType.LEFT_SIDE,
    }
    EDGE_ORDER = [
        Gdk.WindowEdge.NORTH, Gdk.WindowEdge.SOUTH,
        Gdk.WindowEdge.WEST, Gdk.WindowEdge.EAST,
        Gdk.WindowEdge.NORTH_WEST, Gdk.WindowEdge.NORTH_EAST,
        Gdk.WindowEdge.SOUTH_WEST, Gdk.WindowEdge.SOUTH_EAST,
    ]

    def __init__(self, app, note):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.app = app
        self.note = note
        self._save_timer = None

        self.set_title("Postitino")
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_resizable(True)
        self.set_size_request(150, 170)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self._desired_page = None
        self._color_lock = False
        self._type_lock = False
        self._rotation_lock = False
        self._drag_active = False
        self._drag_timeout = None

        self._build_ui()
        self._apply_font_size()
        self._apply_behavior()
        self._load_note()

        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)
        self.connect("delete-event", self.on_close)
        self.connect("configure-event", self.on_configure)
        self.connect("map-event", self.on_map)
        self.connect("realize", self.on_realize)
        self.connect("button-release-event", self.on_window_release)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        seed = int(self.note.id.replace("-", "")[:16], 16)
        self.paper = PostItPaper(seed, self.note.color, self.note.rotation)
        self.paper.set_hexpand(True)
        self.paper.set_vexpand(True)

        self.overlay = Gtk.Overlay()
        self.overlay.add(self.paper)
        self.add(self.overlay)

        for edge in self.EDGE_ORDER:
            self.overlay.add_overlay(self._make_resize_handle(edge))

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        header.set_margin_top(44)
        header.set_margin_start(26)
        header.set_margin_end(14)

        self.mode_label = Gtk.Label(label="")
        self.mode_label.set_name("postit-mode")
        self.mode_label.set_halign(Gtk.Align.START)

        btn_new = self._icon_button("list-add-symbolic", tr("new_note"))
        btn_new.connect("clicked", lambda *a: self.app.new_note())

        self.menu_btn = Gtk.MenuButton()
        self.menu_btn.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.MENU))
        self.menu = self._build_menu()
        self.menu_btn.set_popup(self.menu)
        self.menu_btn.set_relief(Gtk.ReliefStyle.NONE)

        btn_close = self._icon_button("window-close-symbolic", tr("hide"))
        btn_close.connect("clicked", lambda *a: self.hide_note())

        header.pack_start(btn_new, False, False, 0)
        header.pack_start(self.mode_label, False, False, 0)
        header.pack_start(Gtk.Label(), True, True, 0)
        header.pack_end(btn_close, False, False, 0)
        header.pack_end(self.menu_btn, False, False, 0)

        movebox = Gtk.EventBox()
        movebox.connect("button-press-event", self.on_header_press)
        movebox.connect("button-release-event", self.on_window_release)
        movebox.add(header)
        self.paper.pack_start(movebox, False, False, 0)

        titlebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        titlebox.set_margin_start(26)
        titlebox.set_margin_end(18)
        titlebox.set_margin_top(2)
        titlebox.set_margin_bottom(2)
        self.title_entry = Gtk.Entry()
        self.title_entry.set_name("postit-title")
        self.title_entry.set_placeholder_text(tr("title_placeholder"))
        self.title_entry.set_hexpand(True)
        self.title_entry.set_has_frame(False)
        self.title_entry.connect("changed", self._on_title_changed)
        titlebox.pack_start(self.title_entry, True, True, 0)
        self.paper.pack_start(titlebox, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.text_page = self._build_text()
        self.todo_page = self._build_todo()
        self.stack.add_named(self.text_page, "text")
        self.stack.add_named(self.todo_page, "todo")
        self.paper.pack_start(self.stack, True, True, 0)

    def _icon_button(self, icon, tooltip):
        b = Gtk.Button()
        b.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU))
        b.set_relief(Gtk.ReliefStyle.NONE)
        b.set_tooltip_text(tooltip)
        return b

    def _build_text(self):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_hexpand(True)
        sw.set_vexpand(True)
        sw.set_margin_start(26)
        sw.set_margin_end(18)
        sw.set_margin_top(4)
        sw.set_margin_bottom(18)
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(4)
        self.text_view.set_right_margin(2)
        self.text_view.set_top_margin(2)
        self.text_view.set_can_focus(True)
        self.text_view.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.text_view.connect("scroll-event", self.on_scroll)
        buf = self.text_view.get_buffer()
        buf.connect("changed", self._on_text_changed)
        buf.connect_after("insert-text", self._on_buffer_insert)
        sw.add(self.text_view)
        return sw

    def _build_todo(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_hexpand(True)
        box.set_vexpand(True)
        box.set_margin_start(26)
        box.set_margin_end(18)
        box.set_margin_top(4)
        box.set_margin_bottom(18)

        self.todo_scroll = Gtk.ScrolledWindow()
        self.todo_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.todo_scroll.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.todo_scroll.connect("scroll-event", self.on_scroll)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(False)
        self.todo_scroll.add(self.listbox)
        box.pack_start(self.todo_scroll, True, True, 0)

        addrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add_entry = Gtk.Entry()
        self.add_entry.set_placeholder_text(tr("add_todo"))
        self.add_entry.connect("activate", self._on_add_todo)
        self.add_entry.connect("key-press-event", self._on_add_entry_key)
        btn = self._icon_button("list-add-symbolic", tr("add"))
        btn.connect("clicked", self._on_add_todo)
        btn_clear = self._icon_button("edit-clear-all-symbolic", tr("clear_completed"))
        btn_clear.connect("clicked", self._on_clear_completed)
        addrow.pack_start(self.add_entry, True, True, 0)
        addrow.pack_start(btn, False, False, 0)
        addrow.pack_start(btn_clear, False, False, 0)
        box.pack_start(addrow, False, False, 0)
        return box

    # ------------------------------------------------------------- loading

    def _load_note(self):
        self.title_entry.set_text(self.note.title)
        if self.note.type == "todo":
            for it in self.note.items:
                self._add_todo_row(it)
            self._set_page(self.todo_page)
            self.mode_label.set_text(tr("mode_todo"))
        else:
            buf = self.text_view.get_buffer()
            buf.set_text(self.note.content)
            self._apply_buffer_font(buf, getattr(self.note, "font_size", 13))
            self._set_page(self.text_page)
            self.mode_label.set_text(tr("mode_note"))

        self._apply_font_size()

        if self.note.x is not None and self.note.y is not None:
            self.move(self.note.x, self.note.y)
        self.resize(self.note.w, self.note.h)

    def _apply_behavior(self):
        # NORMAL window with no special levels: on GNOME/Mutter both the
        # DESKTOP type and keep_below put the window BELOW the desktop
        # (Nautilus, fullscreen), making it unclickable. With NORMAL the note
        # always receives the mouse; other windows cover it when opened (that
        # is the "stuck to the desktop" behaviour). "Always on top" = keep_above.
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.set_keep_below(False)
        self.set_keep_above(self.note.always_on_top)

    def _refresh_level(self):
        """Re-apply keep_above at runtime (hide->show->present: the WM
        forgets _NET_WM_STATE during hide)."""
        was_visible = self.get_visible()
        pos = self.get_position()
        if pos and (pos[0] != 0 or pos[1] != 0):
            self.note.x, self.note.y = pos[0], pos[1]
        self.hide()
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.set_keep_below(False)
        if was_visible:
            if self.note.x is not None and self.note.y is not None:
                self.move(self.note.x, self.note.y)
            self.show()
            if self.note.x is not None and self.note.y is not None:
                self.move(self.note.x, self.note.y)
            self.present()
        self.set_keep_above(self.note.always_on_top)

    # ------------------------------------------------------------- signals

    def on_header_press(self, widget, event):
        # guard: ignore if a drag (move/resize) is already active, so a
        # double click cannot leave a pending input grab
        if self._drag_active:
            return True
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self._drag_active = True
            self._arm_drag_timeout()
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)
        return True

    def _arm_drag_timeout(self):
        # safety net: if the release never arrives (lost grab on
        # XWayland/multi-monitor) the flag resets itself and the app
        # never stays stuck
        if self._drag_timeout:
            GLib.source_remove(self._drag_timeout)
        self._drag_timeout = GLib.timeout_add(6000, self._reset_drag)

    def _reset_drag(self):
        self._drag_active = False
        self._drag_timeout = None
        return False

    # ----------------------------------------------------- edge resize

    def _make_resize_handle(self, edge):
        is_corner = edge in (Gdk.WindowEdge.NORTH_WEST, Gdk.WindowEdge.NORTH_EAST,
                             Gdk.WindowEdge.SOUTH_WEST, Gdk.WindowEdge.SOUTH_EAST)
        t = self.RESIZE_THICKNESS
        c = self.CORNER_SIZE
        eb = Gtk.EventBox()
        eb.set_name("postit-resize")

        if edge in (Gdk.WindowEdge.NORTH, Gdk.WindowEdge.SOUTH):
            eb.set_size_request(1, t)
            eb.set_hexpand(True)
        elif edge in (Gdk.WindowEdge.WEST, Gdk.WindowEdge.EAST):
            eb.set_size_request(t, 1)
            eb.set_vexpand(True)
        else:
            eb.set_size_request(c, c)

        if edge in (Gdk.WindowEdge.WEST, Gdk.WindowEdge.NORTH_WEST, Gdk.WindowEdge.SOUTH_WEST):
            eb.set_halign(Gtk.Align.START)
        elif edge in (Gdk.WindowEdge.EAST, Gdk.WindowEdge.NORTH_EAST, Gdk.WindowEdge.SOUTH_EAST):
            eb.set_halign(Gtk.Align.END)
        else:
            eb.set_halign(Gtk.Align.FILL)

        if edge in (Gdk.WindowEdge.NORTH, Gdk.WindowEdge.NORTH_WEST, Gdk.WindowEdge.NORTH_EAST):
            eb.set_valign(Gtk.Align.START)
        elif edge in (Gdk.WindowEdge.SOUTH, Gdk.WindowEdge.SOUTH_WEST, Gdk.WindowEdge.SOUTH_EAST):
            eb.set_valign(Gtk.Align.END)
        else:
            eb.set_valign(Gtk.Align.FILL)

        eb.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.ENTER_NOTIFY_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        eb.connect("enter-notify-event", self.on_resize_enter, edge)
        eb.connect("leave-notify-event", self.on_resize_leave)
        eb.connect("button-press-event", self.on_resize_press, edge)
        return eb

    def on_resize_enter(self, widget, event, edge):
        if widget.get_window() is not None:
            widget.get_window().set_cursor(
                Gdk.Cursor.new_for_display(self.get_display(), self.EDGE_CURSORS[edge]))
        return False

    def on_resize_leave(self, widget, event):
        if widget.get_window() is not None:
            widget.get_window().set_cursor(None)
        return False

    def on_resize_press(self, widget, event, edge):
        if self._drag_active:
            return True
        if event.button != 1:
            return False
        self._drag_active = True
        self._arm_drag_timeout()
        self.begin_resize_drag(edge, event.button, event.x_root, event.y_root, event.time)
        return True

    def on_map(self, widget, event):
        if self._desired_page is not None:
            self.stack.set_visible_child(self._desired_page)
        return False

    def on_realize(self, widget):
        # keep_above must be applied once the window is realized/mapped so
        # the WM honours it (especially on X11/XWayland)
        self._apply_behavior()

    def on_window_release(self, widget, event):
        self._drag_active = False
        if self._drag_timeout:
            GLib.source_remove(self._drag_timeout)
            self._drag_timeout = None
        if self.get_visible():
            pos = self.get_position()
            if pos and (pos[0] != 0 or pos[1] != 0):
                self.note.x, self.note.y = pos[0], pos[1]
                self.schedule_save()
        return False

    def _set_page(self, page):
        self._desired_page = page
        self.stack.set_visible_child(page)

    def on_close(self, widget, event):
        self.hide_note()
        self.app.storage.flush()
        return True

    def hide_note(self):
        pos = self.get_position()
        if pos and (pos[0] != 0 or pos[1] != 0):
            self.note.x, self.note.y = pos[0], pos[1]
        self.hide()
        self.note.visible = False
        self.schedule_save()
        self.app.update_tray()

    def show_note(self):
        if self.note.x is not None and self.note.y is not None:
            self.move(self.note.x, self.note.y)
        self.show_all()
        if self.note.x is not None and self.note.y is not None:
            self.move(self.note.x, self.note.y)
        self.present()
        self.set_keep_above(self.note.always_on_top)
        self.note.visible = True
        self.schedule_save()
        self.app.update_tray()
        GLib.idle_add(self._reassert_position)

    def _reassert_position(self):
        if self.get_visible() and self.note.x is not None and self.note.y is not None:
            self.move(self.note.x, self.note.y)
        return False

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self._zoom_font(1)
                return True
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self._zoom_font(-1)
                return True
            elif event.direction == Gdk.ScrollDirection.SMOOTH:
                has_delta, dx, dy = event.get_scroll_deltas()
                if has_delta:
                    if dy < -0.05:
                        self._zoom_font(1)
                        return True
                    elif dy > 0.05:
                        self._zoom_font(-1)
                        return True
        return False

    def on_key_press(self, widget, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        val = event.keyval

        if ctrl:
            if val in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                self._zoom_font(1)
                return True
            elif val in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
                self._zoom_font(-1)
                return True
            elif val in (Gdk.KEY_0, Gdk.KEY_KP_0):
                self._reset_font()
                return True

            if not shift:
                if val in (Gdk.KEY_n, Gdk.KEY_N):
                    self.app.new_note()
                    return True
                elif val in (Gdk.KEY_w, Gdk.KEY_W):
                    self.hide_note()
                    return True
            else:
                if val in (Gdk.KEY_D, Gdk.KEY_d):
                    self._on_delete_requested()
                    return True
                elif val in (Gdk.KEY_C, Gdk.KEY_c):
                    self._on_copy_content()
                    return True

        return False

    def _apply_font_size(self):
        size = getattr(self.note, "font_size", 13)
        if hasattr(self, "title_entry"):
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_size_new((size + 2) * Pango.SCALE))
            self.title_entry.set_attributes(attrs)
        if hasattr(self, "add_entry"):
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_size_new(size * Pango.SCALE))
            self.add_entry.set_attributes(attrs)
        if hasattr(self, "text_view"):
            self._apply_buffer_font(self.text_view.get_buffer(), size)
        if hasattr(self, "listbox"):
            for row in self.listbox.get_children():
                if hasattr(row, "tv"):
                    self._apply_buffer_font(row.tv.get_buffer(), size)
        self.queue_resize()

    def _apply_buffer_font(self, buf, size=None):
        if size is None:
            size = getattr(self.note, "font_size", 13)
        tag = buf.get_tag_table().lookup("font_size")
        if tag is None:
            tag = buf.create_tag("font_size", size_points=size)
        else:
            tag.set_property("size-points", size)
        start, end = buf.get_bounds()
        buf.apply_tag(tag, start, end)

    def _on_buffer_insert(self, buf, loc, text, length):
        tag = buf.get_tag_table().lookup("font_size")
        if tag:
            start = loc.copy()
            start.backward_chars(len(text))
            buf.apply_tag(tag, start, loc)

    def _zoom_font(self, delta):
        current = getattr(self.note, "font_size", 13)
        new_size = max(10, min(26, current + delta))
        if new_size != current:
            self.note.font_size = new_size
            self._apply_font_size()
            self.schedule_save()

    def _reset_font(self):
        self.note.font_size = 13
        self._apply_font_size()
        self.schedule_save()

    def on_configure(self, widget, event):
        if self.get_visible():
            pos = self.get_position()
            if pos and (pos[0] != 0 or pos[1] != 0):
                self.note.x, self.note.y = pos[0], pos[1]
            elif event.x > 0 or event.y > 0:
                self.note.x = event.x
                self.note.y = event.y
            self.note.w = event.width
            self.note.h = event.height
            self.schedule_save()
        return False

    def _on_text_changed(self, buffer):
        self.note.content = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), True)
        self.schedule_save()

    def _on_title_changed(self, entry):
        self.note.title = entry.get_text()
        self.schedule_save()
        self.app.update_tray()

    # ---------------------------------------------------------------- todo

    def _on_add_entry_key(self, entry, event):
        if event.keyval == Gdk.KEY_Escape:
            entry.set_text("")
            return True
        return False

    def _on_add_todo(self, *a):
        text = self.add_entry.get_text().strip()
        if not text:
            return
        item = TodoItem(text)
        self.note.items.append(item)
        self._add_todo_row(item)
        self.add_entry.set_text("")
        if hasattr(self, "m_clear_done"):
            self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))
        self.schedule_save()

    def _add_todo_row(self, item):
        row = Gtk.ListBoxRow()
        h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        h.set_margin_top(2)
        h.set_margin_bottom(2)
        h.set_margin_start(4)
        h.set_margin_end(4)

        chk = Gtk.CheckButton()
        chk.set_active(item.done)
        chk.set_valign(Gtk.Align.START)
        chk.set_margin_top(3)

        tv = Gtk.TextView()
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_hexpand(True)
        tv.set_left_margin(2)
        tv.set_right_margin(2)
        tv.set_top_margin(1)
        tv.set_bottom_margin(1)
        buf = tv.get_buffer()
        buf.set_text(item.text)
        if buf.get_tag_table().lookup("done") is None:
            buf.create_tag("done", strikethrough=True, foreground="#6a6a6a")
        self._apply_buffer_font(buf, getattr(self.note, "font_size", 13))
        buf.connect_after("insert-text", self._on_buffer_insert)

        handle = Gtk.EventBox()
        handle.set_name("postit-drag-handle")
        handle.set_visible_window(False)
        img = Gtk.Image.new_from_icon_name("list-drag-handle-symbolic", Gtk.IconSize.MENU)
        handle.add(img)
        handle.set_tooltip_text(tr("drag_to_reorder"))

        TARGET = [Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 0)]
        handle.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, TARGET, Gdk.DragAction.MOVE)
        handle.connect("drag-data-get", self._on_todo_drag_data_get, item)

        row.drag_dest_set(Gtk.DestDefaults.ALL, TARGET, Gdk.DragAction.MOVE)
        row.connect("drag-data-received", self._on_todo_drag_data_received, item)

        delb = self._icon_button("edit-delete-symbolic", tr("remove"))
        delb.set_relief(Gtk.ReliefStyle.NONE)

        h.pack_start(chk, False, False, 0)
        h.pack_start(tv, True, True, 0)
        h.pack_end(delb, False, False, 0)
        h.pack_end(handle, False, False, 2)
        row.add(h)

        chk.connect("toggled", self._on_todo_toggle, item, tv)
        buf.connect("changed", self._on_todo_changed, item, tv)
        tv.connect("key-press-event", self._on_todo_key_press, item)
        delb.connect("clicked", self._on_todo_delete, item, row)
        tv.set_tooltip_text(item.text)
        self._apply_strike_buf(tv, item.done)
        self.listbox.add(row)
        row.tv = tv
        row.show_all()
        return row

    def _on_todo_drag_data_get(self, widget, context, data, info, time, item):
        data.set_text(item.id, -1)

    def _on_todo_drag_data_received(self, widget, context, x, y, data, info, time, dest_item):
        src_id = data.get_text()
        if not src_id:
            context.finish(False, False, time)
            return
        src_item = next((it for it in self.note.items if it.id == src_id), None)
        if not src_item or src_item.id == dest_item.id:
            context.finish(False, False, time)
            return
        src_idx = self.note.items.index(src_item)
        dest_idx = self.note.items.index(dest_item)
        self.note.items.pop(src_idx)
        self.note.items.insert(dest_idx, src_item)
        self._reload_todo_rows()
        self.schedule_save()
        context.finish(True, False, time)

    def _on_todo_key_press(self, tv, event, item):
        if event.state & Gdk.ModifierType.MOD1_MASK:
            if event.keyval in (Gdk.KEY_Up, Gdk.KEY_KP_Up):
                self._move_todo_item(item, -1)
                return True
            elif event.keyval in (Gdk.KEY_Down, Gdk.KEY_KP_Down):
                self._move_todo_item(item, 1)
                return True
        return False

    def _move_todo_item(self, item, delta):
        if item not in self.note.items:
            return
        idx = self.note.items.index(item)
        new_idx = idx + delta
        if 0 <= new_idx < len(self.note.items):
            self.note.items.pop(idx)
            self.note.items.insert(new_idx, item)
            self._reload_todo_rows(focus_item_id=item.id)
            self.schedule_save()

    def _reload_todo_rows(self, focus_item_id=None):
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for it in self.note.items:
            r = self._add_todo_row(it)
            if focus_item_id and it.id == focus_item_id:
                r.tv.grab_focus()
        if hasattr(self, "m_clear_done"):
            self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))

    def _on_clear_completed(self, *a):
        completed = [it for it in self.note.items if it.done]
        if not completed:
            return
        self.note.items = [it for it in self.note.items if not it.done]
        self._reload_todo_rows()
        self.schedule_save()

    def _on_todo_toggle(self, chk, item, tv):
        item.done = chk.get_active()
        self._apply_strike_buf(tv, item.done)
        if hasattr(self, "m_clear_done"):
            self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))
        self.schedule_save()

    def _on_todo_changed(self, buffer, item, tv):
        item.text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        tv.set_tooltip_text(item.text)
        self._apply_strike_buf(tv, item.done)
        self.schedule_save()

    def _on_todo_delete(self, btn, item, row):
        if item in self.note.items:
            self.note.items.remove(item)
        row.destroy()
        if hasattr(self, "m_clear_done"):
            self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))
        self.schedule_save()

    @staticmethod
    def _apply_strike_buf(tv, done):
        buf = tv.get_buffer()
        tag = buf.get_tag_table().lookup("done")
        start, end = buf.get_bounds()
        if done:
            buf.apply_tag(tag, start, end)
        else:
            buf.remove_tag(tag, start, end)

    # ---------------------------------------------------------------- menu

    def _build_menu(self):
        menu = Gtk.Menu()

        m_new = Gtk.MenuItem(label=tr("new_note_menu"))
        m_new.connect("activate", lambda *a: self.app.new_note())
        menu.append(m_new)

        menu.append(Gtk.SeparatorMenuItem())

        self.m_top = Gtk.CheckMenuItem(label=tr("always_on_top"))
        self.m_top.set_active(self.note.always_on_top)
        self.m_top.connect("activate", self._on_toggle_top)
        menu.append(self.m_top)

        self.m_straight = Gtk.CheckMenuItem(label=tr("straight_note"))
        self.m_straight.set_active(abs(self.note.rotation) < 0.01)
        self.m_straight.connect("toggled", self._on_toggle_straight)
        menu.append(self.m_straight)

        menu.append(Gtk.SeparatorMenuItem())

        colmenu = Gtk.Menu()
        self.m_colors = {}
        for c in COLORS:
            it = Gtk.RadioMenuItem(label=c.capitalize())
            it.set_active(self.note.color == c)
            it.connect("activate", self._on_color, c)
            colmenu.append(it)
            self.m_colors[c] = it
        colitem = Gtk.MenuItem(label=tr("color"))
        colitem.set_submenu(colmenu)
        menu.append(colitem)

        typemenu = Gtk.Menu()
        self.m_text = Gtk.RadioMenuItem(label=tr("text_note"))
        typemenu.append(self.m_text)
        self.m_todo = Gtk.RadioMenuItem.new_with_label_from_widget(self.m_text, tr("todo_list"))
        self.m_todo.set_active(self.note.type == "todo")
        typemenu.append(self.m_todo)
        self.m_text.connect("activate", self._on_type, "text")
        self.m_todo.connect("activate", self._on_type, "todo")
        typeitem = Gtk.MenuItem(label=tr("note_type"))
        typeitem.set_submenu(typemenu)
        menu.append(typeitem)

        sizemenu = Gtk.Menu()
        m_larger = Gtk.MenuItem(label=tr("font_larger"))
        m_larger.connect("activate", lambda *a: self._zoom_font(1))
        sizemenu.append(m_larger)

        m_smaller = Gtk.MenuItem(label=tr("font_smaller"))
        m_smaller.connect("activate", lambda *a: self._zoom_font(-1))
        sizemenu.append(m_smaller)

        m_reset_font = Gtk.MenuItem(label=tr("font_normal"))
        m_reset_font.connect("activate", lambda *a: self._reset_font())
        sizemenu.append(m_reset_font)

        sizeitem = Gtk.MenuItem(label=tr("text_size"))
        sizeitem.set_submenu(sizemenu)
        menu.append(sizeitem)

        self.m_clear_done = Gtk.MenuItem(label=tr("clear_completed"))
        self.m_clear_done.connect("activate", self._on_clear_completed)
        self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))
        menu.append(self.m_clear_done)

        m_copy = Gtk.MenuItem(label=tr("copy_content"))
        m_copy.connect("activate", self._on_copy_content)
        menu.append(m_copy)

        menu.append(Gtk.SeparatorMenuItem())

        m_del = Gtk.MenuItem(label=tr("delete_note"))
        m_del.connect("activate", self._on_delete_requested)
        menu.append(m_del)

        menu.append(Gtk.SeparatorMenuItem())

        m_about = Gtk.MenuItem(label=tr("about"))
        m_about.connect("activate", self._on_about)
        menu.append(m_about)

        m_quit = Gtk.MenuItem(label=tr("quit_app"))
        m_quit.connect("activate", lambda *a: self.app.quit_app())
        menu.append(m_quit)

        menu.show_all()
        return menu

    def _on_about(self, item):
        dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        dialog.set_program_name("Postitino")
        dialog.set_version("1.0.1")
        dialog.set_comments(tr("about_text"))
        dialog.set_website("https://github.com/andreagosto/Postitino")
        dialog.set_website_label("GitHub: andreagosto/Postitino")
        dialog.set_copyright("© 2026 Andrea Scarafoni")
        dialog.set_authors(["Andrea Scarafoni", "DeepSeek Flash (deepseek/deepseek-v4-flash)"])
        try:
            from .app import ICON_PATH
            if os.path.exists(ICON_PATH):
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(ICON_PATH, 96, 96, True)
                dialog.set_logo(pix)
        except Exception:
            pass
        dialog.run()
        dialog.destroy()

    def _on_delete_requested(self, *a):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
        )
        dialog.set_title(tr("delete_note"))
        dialog.set_markup(f"<b>{tr('delete_note')}</b>")
        dialog.format_secondary_text(tr("confirm_delete_note"))
        resp = dialog.run()
        dialog.destroy()
        if resp == Gtk.ResponseType.OK:
            self.app.delete_note(self)

    def _on_copy_content(self, *a):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        title = self.note.title.strip()
        if self.note.type == "todo":
            lines = []
            if title:
                lines.append(f"# {title}")
            for it in self.note.items:
                mark = "- [x]" if it.done else "- [ ]"
                lines.append(f"{mark} {it.text}")
            text = "\n".join(lines)
        else:
            text = f"{title}\n\n{self.note.content}".strip() if title else self.note.content
        clipboard.set_text(text, -1)

    def _on_toggle_straight(self, item):
        if self._rotation_lock:
            return
        if item.get_active():
            self.note.rotation = 0.0
        else:
            deg = round(random.uniform(0.8, 2.0), 2)
            if random.random() < 0.5:
                deg = -deg
            self.note.rotation = deg
        self.paper.rotation = math.radians(self.note.rotation)
        self.paper.queue_draw()
        self.schedule_save()

    def _on_toggle_top(self, item):
        self.note.always_on_top = item.get_active()
        self._refresh_level()
        self.schedule_save()

    def _on_color(self, item, c):
        if self._color_lock:
            return
        self._color_lock = True
        try:
            self.note.color = c
            self.paper.color = c
            self.paper.queue_draw()
            for k, it in self.m_colors.items():
                it.set_active(k == c)
            self.schedule_save()
        finally:
            self._color_lock = False

    def _on_type(self, item, t):
        if self._type_lock:
            return
        if not item.get_active() or t == self.note.type:
            return
        self._type_lock = True
        try:
            if t == "todo":
                if not self.note.items:
                    text = self.text_view.get_buffer().get_text(
                        self.text_view.get_buffer().get_start_iter(),
                        self.text_view.get_buffer().get_end_iter(), True).strip()
                    self.note.items = [
                        TodoItem(line.strip()) for line in text.splitlines() if line.strip()
                    ]
                self.note.type = "todo"
                for it in self.note.items:
                    self._add_todo_row(it)
                self._set_page(self.todo_page)
                self.mode_label.set_text(tr("mode_todo"))
            else:
                lines = "\n".join(it.text for it in self.note.items)
                self.note.type = "text"
                self.note.items = []
                buf = self.text_view.get_buffer()
                buf.set_text(lines)
                self._apply_buffer_font(buf, getattr(self.note, "font_size", 13))
                self._set_page(self.text_page)
                self.mode_label.set_text(tr("mode_note"))
            if hasattr(self, "m_clear_done"):
                self.m_clear_done.set_sensitive(any(it.done for it in self.note.items))
            self.schedule_save()
        finally:
            self._type_lock = False

    # --------------------------------------------------------------- saving

    def schedule_save(self):
        if self._save_timer:
            GLib.source_remove(self._save_timer)
        self._save_timer = GLib.timeout_add(400, self._flush_save)

    def _flush_save(self):
        self._save_timer = None
        self.app.save()
        self.app.update_tray()
        return False
