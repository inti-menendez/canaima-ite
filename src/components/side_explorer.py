import os
import shutil
import subprocess
from pathlib import Path
from gi.repository import Gtk, Gio, Gdk, GLib, Pango
from core.event_bus import bus

style_provider = Gtk.CssProvider()
style_provider.load_from_data(b"""
    .explorer-header {
        padding: 5px 0;
    }
    .custom-treeview {
        background-color: transparent;
        color: #fff;
        font-size: 14px;
    }
    .custom-treeview:hover {
        background-color: transparent;
    }
    .custom-treeview:selected {
        background-color: #1f232a;
        color: #0b6793;
    }
    .popover-menu-box {
        padding: 6px;
        background-color: #1f232a;
    }
    .destructive-action {
        background-image: none;
        background-color: #e01b24;
        color: white;
        font-size: 12px;
        font-weight: bold;
        border-radius: 4px;
    }
    .destructive-action:hover {
        background-color: #c01c24;
    }
""")

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
)


class sideExplorer(Gtk.Box):
    def __init__(self, root_path="."):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.show_hidden = False
        self.current_root = root_path
        self.history = []

        self._setup_header()

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_shadow_type(Gtk.ShadowType.NONE)

        self.store = Gtk.TreeStore(str, str, str, bool, bool, bool, bool)
        self.treeview = Gtk.TreeView(model=self.store)
        self.treeview.set_headers_visible(False)
        self.treeview.set_enable_search(False)

        self.treeview.get_style_context().add_class("custom-treeview")

        column = Gtk.TreeViewColumn("Archivos")

        icon_renderer = Gtk.CellRendererPixbuf()
        icon_renderer.set_property("xpad", 6)
        column.pack_start(icon_renderer, False)
        column.add_attribute(icon_renderer, "icon-name", 0)

        self.text_renderer = Gtk.CellRendererText()
        self.text_renderer.set_property("ypad", 4)
        self.text_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.text_renderer.connect("edited", self.on_name_edited)
        self.text_renderer.connect("editing-canceled", self.on_editing_canceled)

        column.pack_start(self.text_renderer, True)
        column.add_attribute(self.text_renderer, "text", 1)

        self.treeview.append_column(column)
        self.treeview.connect("row-expanded", self.on_row_expanded)
        self.treeview.connect("row-activated", self.on_row_activated)
        self.treeview.connect("button-press-event", self.on_right_click)
        self.treeview.connect("key-press-event", self.on_key_press)

        self.scrolled.add(self.treeview)
        self.pack_start(self.scrolled, True, True, 0)

        bus.subscribe("sent_cwd", self.update_explorer_from_cwd)
        self.update_explorer_from_cwd(root_path)
        self.show_all()

    def on_editing_canceled(self, renderer):
        renderer.set_property("editable", False)
        model = self.treeview.get_model()

        def remove_ghost(store, tree_path, tree_iter):
            if store.get_value(tree_iter, 5):
                store.remove(tree_iter)
                return True
            return False

        model.foreach(remove_ghost)

    def _setup_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("explorer-header")

        title = Gtk.Label(xalign=0)
        title.set_markup(
            "<span size='small' weight='bold' foreground='#888888'>  EXPLORADOR</span>"
        )
        header.pack_start(title, True, True, 5)

        menu_button = Gtk.MenuButton()
        menu_button.set_image(
            Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        )
        menu_button.set_relief(Gtk.ReliefStyle.NONE)

        popover = Gtk.Popover()
        vbox_menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox_menu.get_style_context().add_class("popover-menu-box")

        check_hidden = Gtk.CheckButton(label="Mostrar archivos ocultos")
        check_hidden.set_active(self.show_hidden)
        check_hidden.connect("toggled", self.on_show_hidden_toggled)
        vbox_menu.pack_start(check_hidden, False, False, 0)

        btn_collapse = Gtk.ModelButton(text="Colapsar carpetas")
        btn_collapse.connect("clicked", self.on_collapse_all_clicked)
        vbox_menu.pack_start(btn_collapse, False, False, 0)

        vbox_menu.show_all()
        popover.add(vbox_menu)
        menu_button.set_popover(popover)

        self.btn_back = Gtk.Button()
        self.btn_back.set_image(
            Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU)
        )
        self.btn_back.set_relief(Gtk.ReliefStyle.NONE)
        self.btn_back.set_tooltip_text("Volver al directorio anterior")
        self.btn_back.set_sensitive(False)
        self.btn_back.connect("clicked", self.on_back_clicked)

        btn_refresh = Gtk.Button()
        btn_refresh.set_image(
            Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.MENU)
        )
        btn_refresh.set_relief(Gtk.ReliefStyle.NONE)
        btn_refresh.set_tooltip_text("Actualizar vista")
        btn_refresh.connect("clicked", lambda _: self.refresh_explorer())

        btn_insert = Gtk.Button()
        btn_insert.set_image(
            Gtk.Image.new_from_icon_name("insert-text-symbolic", Gtk.IconSize.MENU)
        )
        btn_insert.set_relief(Gtk.ReliefStyle.NONE)
        btn_insert.set_tooltip_text("Insertar ruta en terminal")
        btn_insert.connect("clicked", self.on_insert_path_clicked)

        header.pack_end(menu_button, False, False, 5)
        header.pack_end(btn_refresh, False, False, 0)
        header.pack_end(btn_insert, False, False, 0)
        header.pack_end(self.btn_back, False, False, 0)

        self.pack_start(header, False, False, 0)

    def refresh_explorer(self):
        self.update_explorer_from_cwd(self.current_root)

    def on_show_hidden_toggled(self, button):
        self.show_hidden = button.get_active()
        self.refresh_explorer()

    def on_collapse_all_clicked(self, button):
        model = self.treeview.get_model()
        root_iter = model.get_iter_first()
        if root_iter:
            child_iter = model.iter_children(root_iter)
            while child_iter:
                self.treeview.collapse_row(model.get_path(child_iter))
                child_iter = model.iter_next(child_iter)
        self.popover.popdown()

    def update_explorer_from_cwd(self, data):
        if hasattr(self, "current_root") and data != self.current_root:
            self.history.append(self.current_root)
            self.btn_back.set_sensitive(True)

        self.current_root = data
        self.store.clear()

        abs_path = str(Path(data).expanduser().resolve())
        folder_name = abs_path.split("/")[-1].upper() or "/"

        root_iter = self.store.append(
            None, ["folder-open", folder_name, abs_path, True, False, False, False]
        )

        gfile = Gio.File.new_for_path(abs_path)
        if gfile.query_exists():
            self.add_nodes(gfile, root_iter)
            self.store.set_value(root_iter, 4, True)
            self.treeview.expand_row(self.store.get_path(root_iter), False)
        bus.publish("explorer_path_change", abs_path)

    def on_back_clicked(self, btn):
        if self.history:
            last_root = self.history.pop()
            if not self.history:
                self.btn_back.set_sensitive(False)
            self._force_update_no_history(last_root)

    def _force_update_no_history(self, data):
        self.current_root = data
        self.store.clear()
        abs_path = str(Path(data).expanduser().resolve())
        folder_name = abs_path.split("/")[-1].upper() or "/"
        root_iter = self.store.append(
            None, ["folder-open", folder_name, abs_path, True, False, False, False]
        )
        gfile = Gio.File.new_for_path(abs_path)
        if gfile.query_exists():
            self.add_nodes(gfile, root_iter)
            self.store.set_value(root_iter, 4, True)
            self.treeview.expand_row(self.store.get_path(root_iter), False)

    def on_insert_path_clicked(self, btn):
        selection = self.treeview.get_selection()
        model, tree_iter = selection.get_selected()

        if tree_iter:
            path_to_insert = model.get_value(tree_iter, 2)
        else:
            path_to_insert = self.current_root

        bus.publish("paste_command", f"'{path_to_insert}'")

    def add_nodes(self, gfile, parent_iter):
        try:
            enumerator = gfile.enumerate_children(
                "standard::name,standard::type,standard::icon,access::can-read",
                Gio.FileQueryInfoFlags.NONE,
                None,
            )
            items = []
            
            while True:
                info = enumerator.next_file(None)
                if info is None:
                    break
                
                if not self.show_hidden and info.get_name().startswith("."):
                    continue
                items.append(info)

            items.sort(
                key=lambda i: (
                    i.get_file_type() != Gio.FileType.DIRECTORY,
                    i.get_name().lower(),
                )
            )

            for info in items:
                name = info.get_name()
                child_file = gfile.get_child(name)
                is_dir = info.get_file_type() == Gio.FileType.DIRECTORY
                can_read = info.get_attribute_boolean("access::can-read")

                icon_name = (
                    "folder"
                    if is_dir
                    else (
                        info.get_icon().get_names()[0]
                        if info.get_icon()
                        else "text-x-generic"
                    )
                )
                if not can_read:
                    icon_name = "changes-prevent-symbolic"

                curr_iter = self.store.append(
                    parent_iter,
                    [
                        icon_name,
                        name,
                        child_file.get_path(),
                        is_dir,
                        not can_read,
                        False,
                        False,
                    ],
                )
                if is_dir and can_read:
                    self.store.append(
                        curr_iter,
                        [
                            "process-working-symbolic",
                            "...",
                            "",
                            False,
                            False,
                            False,
                            True,
                        ],
                    )

        except Exception as e:
            print(f"Error add_nodes: {e}")

    def on_row_expanded(self, treeview, tree_iter, path):
        if not self.store.get_value(tree_iter, 4):
            folder_path = self.store.get_value(tree_iter, 2)
            child = self.store.iter_children(tree_iter)
            while child:
                self.store.remove(child)
                child = self.store.iter_children(tree_iter)

            self.add_nodes(Gio.File.new_for_path(folder_path), tree_iter)
            self.store.set_value(tree_iter, 4, True)

    def on_row_activated(self, treeview, path, column):
        model = treeview.get_model()
        tree_iter = model.get_iter(path)
        if model.get_value(tree_iter, 3):
            if treeview.row_expanded(path):
                treeview.collapse_row(path)
            else:
                GLib.idle_add(treeview.expand_row, path, False)

    def on_right_click(self, treeview, event):
        if event.button == 3:
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))

            if path_info is not None:
                path, col, cell_x, cell_y = path_info

                selection = treeview.get_selection()
                selection.select_path(path)
                treeview.set_cursor(path, None, False)

                model = treeview.get_model()
                tree_iter = model.get_iter(path)

                self.show_context_menu(event, model, tree_iter)
                return True
        return False

    def show_context_menu(self, event, model, tree_iter):
        menu = Gtk.Menu()
        file_path = model.get_value(tree_iter, 2)
        file_name = model.get_value(tree_iter, 1)

        is_dir = model.get_value(tree_iter, 3)
        target_dir = file_path if is_dir else str(Path(file_path).parent)

        it_new_file = Gtk.MenuItem(label="Nuevo archivo")
        it_new_file.connect(
            "activate",
            lambda _: self.prepare_inline_creation(
                model, tree_iter, target_dir, is_dir, False
            ),
        )
        menu.append(it_new_file)

        it_new_dir = Gtk.MenuItem(label="Nueva carpeta")
        it_new_dir.connect(
            "activate",
            lambda _: self.prepare_inline_creation(
                model, tree_iter, target_dir, is_dir, True
            ),
        )
        menu.append(it_new_dir)

        menu.append(Gtk.SeparatorMenuItem())

        it_open = Gtk.MenuItem(label="Abrir con micro")
        it_open.connect(
            "activate",
            lambda _: bus.publish(
                "exec_in_new_terminal", [f"micro {file_path}", file_name]
            ),
        )
        menu.append(it_open)

        it_open = Gtk.MenuItem(label="Abrir con nano")
        it_open.connect(
            "activate",
            lambda _: bus.publish(
                "exec_in_new_terminal", [f"nano {file_path}", file_name]
            ),
        )
        menu.append(it_open)

        it_new = Gtk.MenuItem(label="Ir en nueva terminal")
        it_new.connect(
            "activate", lambda _: bus.publish("open_in_new_terminal", f"{target_dir}")
        )
        menu.append(it_new)

        it_cd = Gtk.MenuItem(label="Ir en terminal actual")
        it_cd.connect(
            "activate", lambda _: bus.publish("execute_command", f'cd "{target_dir}"')
        )
        menu.append(it_cd)

        it_open = Gtk.MenuItem(label="Abrir en Gestor de Archivos")
        it_open.connect(
            "activate", lambda _: subprocess.Popen(["xdg-open", target_dir])
        )
        menu.append(it_open)

        menu.append(Gtk.SeparatorMenuItem())

        it_cp = Gtk.MenuItem(label="Copiar ruta absoluta")
        it_cp.connect("activate", lambda _: self._to_clipboard(file_path))
        menu.append(it_cp)

        menu.append(Gtk.SeparatorMenuItem())

        it_ren = Gtk.MenuItem(label="Renombrar")
        it_ren.connect("activate", lambda _: self.handle_rename(model, tree_iter))
        menu.append(it_ren)

        it_del = Gtk.MenuItem(label="Eliminar")
        it_del.connect(
            "activate", lambda _: self.handle_delete(model, tree_iter, file_path)
        )
        menu.append(it_del)

        menu.show_all()

        if event.type == Gdk.EventType.KEY_PRESS:
            model, tree_iter = self.treeview.get_selection().get_selected()
            if tree_iter:
                path = model.get_path(tree_iter)
                column = self.treeview.get_column(0)
                rect = self.treeview.get_cell_area(path, column)
                bin_window = self.treeview.get_bin_window()

                menu.popup_at_rect(
                    bin_window,
                    rect,
                    Gdk.Gravity.SOUTH_WEST,
                    Gdk.Gravity.NORTH_WEST,
                    event,
                )
            else:
                menu.popup_at_pointer(event)
        else:
            menu.popup_at_pointer(event)

    def _to_clipboard(self, text):
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)

    def handle_rename(self, model, tree_iter):
        self.text_renderer.set_property("editable", True)
        self.treeview.set_cursor_on_cell(
            model.get_path(tree_iter),
            self.treeview.get_column(0),
            self.text_renderer,
            True,
        )

    def on_name_edited(self, renderer, path, new_text):
        renderer.set_property("editable", False)
        new_text = new_text.strip()

        model = self.treeview.get_model()
        tree_iter = model.get_iter(path)

        is_creating = (
            model.get_value(tree_iter, 5) if model.get_n_columns() > 5 else False
        )

        if is_creating:
            target_dir = model.get_value(tree_iter, 2)
            create_folder = model.get_value(tree_iter, 6)

            if not new_text or "/" in new_text:
                model.remove(tree_iter)
                return

            full_path = os.path.join(target_dir, new_text)

            try:
                if create_folder:
                    os.makedirs(full_path, exist_ok=True)
                else:
                    with open(full_path, "a"):
                        os.utime(full_path, None)

                model.set_value(tree_iter, 1, new_text)
                model.set_value(tree_iter, 2, full_path)
                model.set_value(tree_iter, 5, False)

                if create_folder:
                    model.append(
                        tree_iter,
                        [
                            "process-working-symbolic",
                            "...",
                            "",
                            False,
                            False,
                            True,
                            True,
                        ],
                    )

            except Exception as e:
                print(f"Error al crear elemento en línea: {e}")
                model.remove(tree_iter)

        else:
            if not new_text or "/" in new_text:
                return

            old_path = model.get_value(tree_iter, 2)
            new_path = os.path.join(os.path.dirname(old_path), new_text)

            try:
                os.rename(old_path, new_path)
                model.set_value(tree_iter, 1, new_text)
                model.set_value(tree_iter, 2, new_path)
            except Exception as e:
                print(f"Error al renombrar: {e}")

    def on_key_press(self, widget, event):
        model, tree_iter = widget.get_selection().get_selected()

        if event.keyval == Gdk.KEY_F2:
            if tree_iter:
                self.handle_rename(model, tree_iter)
                return True

        elif event.keyval == Gdk.KEY_Escape:
            self.text_renderer.set_property("editable", False)

            def remove_ghost(store, tree_path, tree_iter):
                if store.get_value(tree_iter, 5):
                    store.remove(tree_iter)
                    return True
                return False

            model.foreach(remove_ghost)
            return True

        elif event.keyval == Gdk.KEY_Delete:
            if tree_iter:
                file_path = model.get_value(tree_iter, 2)
                self.handle_delete(model, tree_iter, file_path)
                return True

        elif event.keyval == Gdk.KEY_Menu:
            if tree_iter:
                selection = widget.get_selection()
                model, tree_iter = selection.get_selected()
                if tree_iter:
                    self.show_context_menu(event, model, tree_iter)
                    return True

        return False

    def handle_delete(self, model, tree_iter, path_to_del):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="¿Eliminar permanentemente?",
        )
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        del_btn = dialog.add_button("Eliminar todo", Gtk.ResponseType.YES)
        del_btn.get_style_context().add_class("destructive-action")

        dialog.format_secondary_text(f"Se eliminará: {os.path.basename(path_to_del)}")
        if dialog.run() == Gtk.ResponseType.YES:
            try:
                if os.path.isdir(path_to_del):
                    shutil.rmtree(path_to_del)
                else:
                    os.remove(path_to_del)
                model.remove(tree_iter)
            except Exception as e:
                print(f"Error eliminar: {e}")
        dialog.destroy()

    def prepare_inline_creation(
        self, model, tree_iter, target_dir, is_target_dir, create_folder=False
    ):
        parent_iter = tree_iter if is_target_dir else model.iter_parent(tree_iter)

        if is_target_dir and not model.get_value(tree_iter, 4):
            self.treeview.expand_row(model.get_path(tree_iter), False)

        icon_name = "folder" if create_folder else "text-x-generic"

        dummy_iter = model.insert(
            parent_iter,
            0,
            [icon_name, "", target_dir, create_folder, False, True, create_folder],
        )

        if parent_iter:
            self.treeview.expand_row(model.get_path(parent_iter), False)

        self.text_renderer.set_property("editable", True)
        self.treeview.set_cursor_on_cell(
            model.get_path(dummy_iter),
            self.treeview.get_column(0),
            self.text_renderer,
            True,
        )
