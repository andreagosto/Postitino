import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

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

        self.set_title("Post-it")
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
        self._drag_active = False
        self._drag_timeout = None
        self._build_ui()
        self._apply_behavior()
        self._load_note()

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

        btn_new = self._icon_button("list-add-symbolic", "Nuova nota")
        btn_new.connect("clicked", lambda *a: self.app.new_note())

        self.menu_btn = Gtk.MenuButton()
        self.menu_btn.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.MENU))
        self.menu = self._build_menu()
        self.menu_btn.set_popup(self.menu)
        self.menu_btn.set_relief(Gtk.ReliefStyle.NONE)

        btn_close = self._icon_button("window-close-symbolic", "Nascondi")
        btn_close.connect("clicked", lambda *a: self.hide())

        header.pack_start(btn_new, False, False, 0)
        header.pack_start(self.mode_label, False, False, 0)
        header.pack_start(Gtk.Label(), True, True, 0)
        header.pack_end(btn_close, False, False, 0)
        header.pack_end(self.menu_btn, False, False, 0)

        movebox = Gtk.EventBox()
        movebox.connect("button-press-event", self.on_header_press)
        movebox.add(header)
        self.paper.pack_start(movebox, False, False, 0)

        titlebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        titlebox.set_margin_start(26)
        titlebox.set_margin_end(18)
        titlebox.set_margin_top(2)
        titlebox.set_margin_bottom(2)
        self.title_entry = Gtk.Entry()
        self.title_entry.set_name("postit-title")
        self.title_entry.set_placeholder_text("Titolo…")
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
        self.text_view.get_buffer().connect("changed", self._on_text_changed)
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
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(False)
        self.todo_scroll.add(self.listbox)
        box.pack_start(self.todo_scroll, True, True, 0)

        addrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add_entry = Gtk.Entry()
        self.add_entry.set_placeholder_text("Aggiungi task…")
        self.add_entry.connect("activate", self._on_add_todo)
        btn = self._icon_button("list-add-symbolic", "Aggiungi")
        btn.connect("clicked", self._on_add_todo)
        addrow.pack_start(self.add_entry, True, True, 0)
        addrow.pack_start(btn, False, False, 0)
        box.pack_start(addrow, False, False, 0)
        return box

    # ------------------------------------------------------------- loading

    def _load_note(self):
        self.title_entry.set_text(self.note.title)
        if self.note.type == "todo":
            for it in self.note.items:
                self._add_todo_row(it)
            self._set_page(self.todo_page)
            self.mode_label.set_text("TO-DO")
        else:
            buf = self.text_view.get_buffer()
            buf.set_text(self.note.content)
            self._set_page(self.text_page)
            self.mode_label.set_text("NOTA")

        if self.note.x is not None and self.note.y is not None:
            self.move(self.note.x, self.note.y)
        self.resize(self.note.w, self.note.h)

    def _apply_behavior(self):
        # Finestra NORMAL senza livelli speciali: su GNOME/Mutter sia il tipo
        # DESKTOP sia keep_below mettono la finestra SOTTO il desktop
        # (Nautilus, a tutto schermo) rendendola non cliccabile. Con NORMAL la
        # nota riceve sempre il mouse; quando apri altre finestre queste la
        # coprono (e' il comportamento "attaccata al desktop"). "Sempre in
        # primo piano" = keep_above.
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.set_keep_below(False)
        self.set_keep_above(self.note.always_on_top)

    def _refresh_level(self):
        """Riapplica keep_above a runtime (hide->show->present: il WM
        dimentica gli stati _NET_WM_STATE durante hide)."""
        was_visible = self.get_visible()
        self.hide()
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.set_keep_below(False)
        if was_visible:
            self.show()
            self.present()
        self.set_keep_above(self.note.always_on_top)

    # ------------------------------------------------------------- signals

    def on_header_press(self, widget, event):
        # protezione: ignora se un drag (move/resize) e' gia' attivo, per
        # evitare che un doppio click lasci un grab di input pendente
        if self._drag_active:
            return True
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self._drag_active = True
            self._arm_drag_timeout()
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)
        return True

    def _arm_drag_timeout(self):
        # rete di sicurezza: se il release non arriva mai (grab perso su
        # XWayland/multi-monitor) il flag si resetta da solo e l'app non
        # resta bloccata
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
        # keep_above va applicato a finestra realizzata/mappata per essere
        # gestito dal WM (soprattutto su X11/XWayland)
        self._apply_behavior()

    def on_window_release(self, widget, event):
        self._drag_active = False
        if self._drag_timeout:
            GLib.source_remove(self._drag_timeout)
            self._drag_timeout = None
        return False

    def _set_page(self, page):
        self._desired_page = page
        self.stack.set_visible_child(page)

    def on_close(self, widget, event):
        self.hide()
        return True

    def on_configure(self, widget, event):
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

    # ---------------------------------------------------------------- todo

    def _on_add_todo(self, *a):
        text = self.add_entry.get_text().strip()
        if not text:
            return
        item = TodoItem(text)
        self.note.items.append(item)
        self._add_todo_row(item)
        self.add_entry.set_text("")
        self.schedule_save()

    def _add_todo_row(self, item):
        row = Gtk.ListBoxRow()
        h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
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

        delb = self._icon_button("edit-delete-symbolic", "Rimuovi")
        delb.set_relief(Gtk.ReliefStyle.NONE)

        h.pack_start(chk, False, False, 0)
        h.pack_start(tv, True, True, 0)
        h.pack_end(delb, False, False, 0)
        row.add(h)

        chk.connect("toggled", self._on_todo_toggle, item, tv)
        buf.connect("changed", self._on_todo_changed, item, tv)
        delb.connect("clicked", self._on_todo_delete, item, row)
        tv.set_tooltip_text(item.text)
        self._apply_strike_buf(tv, item.done)
        self.listbox.add(row)
        row.show_all()
        return row

    def _on_todo_toggle(self, chk, item, tv):
        item.done = chk.get_active()
        self._apply_strike_buf(tv, item.done)
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

        m_new = Gtk.MenuItem("Nuova nota")
        m_new.connect("activate", lambda *a: self.app.new_note())
        menu.append(m_new)

        menu.append(Gtk.SeparatorMenuItem())

        self.m_top = Gtk.CheckMenuItem("Sempre in primo piano")
        self.m_top.set_active(self.note.always_on_top)
        self.m_top.connect("activate", self._on_toggle_top)
        menu.append(self.m_top)

        menu.append(Gtk.SeparatorMenuItem())

        colmenu = Gtk.Menu()
        self.m_colors = {}
        for c in COLORS:
            it = Gtk.RadioMenuItem(c.capitalize())
            it.set_active(self.note.color == c)
            it.connect("activate", self._on_color, c)
            colmenu.append(it)
            self.m_colors[c] = it
        colitem = Gtk.MenuItem("Colore")
        colitem.set_submenu(colmenu)
        menu.append(colitem)

        typemenu = Gtk.Menu()
        self.m_text = Gtk.RadioMenuItem("Nota di testo")
        typemenu.append(self.m_text)
        self.m_todo = Gtk.RadioMenuItem.new_with_label_from_widget(self.m_text, "Lista to-do")
        self.m_todo.set_active(self.note.type == "todo")
        typemenu.append(self.m_todo)
        self.m_text.connect("activate", self._on_type, "text")
        self.m_todo.connect("activate", self._on_type, "todo")
        typeitem = Gtk.MenuItem("Tipo di nota")
        typeitem.set_submenu(typemenu)
        menu.append(typeitem)

        menu.append(Gtk.SeparatorMenuItem())

        m_del = Gtk.MenuItem("Elimina nota")
        m_del.connect("activate", lambda *a: self.app.delete_note(self))
        menu.append(m_del)

        menu.append(Gtk.SeparatorMenuItem())

        m_quit = Gtk.MenuItem("Esci dall'app")
        m_quit.connect("activate", lambda *a: self.app.quit_app())
        menu.append(m_quit)

        menu.show_all()
        return menu

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
                self.mode_label.set_text("TO-DO")
            else:
                lines = "\n".join(it.text for it in self.note.items)
                self.note.type = "text"
                self.note.items = []
                buf = self.text_view.get_buffer()
                buf.set_text(lines)
                self._set_page(self.text_page)
                self.mode_label.set_text("NOTA")
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
        return False
