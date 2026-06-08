from gi.repository import Gtk, Gdk
from core.keybindings_engine import registry

style_provider = Gtk.CssProvider()
style_provider.load_from_data(b"""
    .key {
        background-color: #2d3139;
        color: #a9b1d6;
        border: 1px solid #0b6793;
        border-radius: 4px;
        padding-left: 6px;
        padding-right: 6px;
        padding-top: 2px;
        padding-bottom: 2px;
        font-family: 'Monospace', 'Courier New', monospace;
        font-size: 11px;
        font-weight: bold;
    }
    .shortcut-separator {
        color: #565f89;
        font-weight: bold;
        font-size: 12px;
    }
    .category-title {
        color: #0b6793;
        font-weight: bold;
        font-size: 14px;
        padding: 0 0 0 10px;
    }
    .search {
        background-color: #1f232a;
        color: #a9b1d6;
        border: 1px solid #2d3139;
        border-radius: 6px;
        margin: 5px 10px 10px 10px;
        padding: 4px 4px 4px 8px;
    }
    .search:focus {
        border-color: #0b6793;
    }
""")

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
)


class SideKeybindings(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._setup_header()
        self._setup_search_bar()

        self.search_registry = {}

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        scrolled.add(self.main_layout)
        self.pack_start(scrolled, True, True, 0)

        self.render_interface()
        self.show_all()

    def _setup_header(self):

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.set_margin_top(5)
        header.set_margin_bottom(5)
        title = Gtk.Label(xalign=0)
        title.set_markup(
            "<span size='small' weight='bold' foreground='#888888'>  ATAJOS DEL TECLADO</span>"
        )
        header.pack_start(title, True, True, 5)

        reset_btn = Gtk.Button()

        icon = Gtk.Image.new_from_icon_name(
            "view-refresh-symbolic", Gtk.IconSize.BUTTON
        )
        reset_btn.add(icon)
        reset_btn.set_relief(Gtk.ReliefStyle.NONE)
        reset_btn.set_tooltip_text("Restablecer atajos de fábrica")
        reset_btn.connect("clicked", self._on_reset_clicked)

        header.pack_end(reset_btn, False, False, 0)
        self.pack_start(header, False, False, 0)

    def _on_reset_clicked(self, button):
        toplevel = self.get_toplevel()

        confirm = Gtk.MessageDialog(
            transient_for=toplevel,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="¿Restablecer atajos?",
        )
        confirm.format_secondary_text(
            "Esto borrará todas tus personalizaciones y restaurará los comandos por defecto."
        )
        response = confirm.run()
        confirm.destroy()

        if response == Gtk.ResponseType.YES:
            if registry.reset_to_defaults():
                self.render_interface()
                self.show_all()

    def _setup_search_bar(self):
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar atajo...")
        self.search_entry.get_style_context().add_class("search")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.pack_start(self.search_entry, False, False, 0)

    def create_key_badge(self, text: str) -> Gtk.Box:
        box = Gtk.Box()
        box.get_style_context().add_class("key")
        label = Gtk.Label(label=text)
        box.add(label)
        return box

    def render_interface(self):
        for child in self.main_layout.get_children():
            self.main_layout.remove(child)

        self.search_registry.clear()

        data = registry.get_shortcuts_by_category()

        for category, items in data.items():
            cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

            cat_label = Gtk.Label(label=category.upper())
            cat_label.set_halign(Gtk.Align.START)
            cat_label.get_style_context().add_class("category-title")
            cat_box.pack_start(cat_label, False, False, 5)

            listbox = Gtk.ListBox()

            listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

            listbox.connect(
                "row-activated",
                lambda lb, row, cat=category: self._on_row_activated(row, cat),
            )
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)

            registered_rows = []

            for item in items:
                row = Gtk.ListBoxRow()

                row.action_name = item["action"]
                row.action_label = item["label"]

                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hbox.set_margin_start(6)
                hbox.set_margin_end(6)
                hbox.set_margin_top(6)
                hbox.set_margin_bottom(6)

                label_text = Gtk.Label(label=item["label"])
                label_text.set_halign(Gtk.Align.START)
                hbox.pack_start(label_text, True, True, 0)

                shortcut_box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=4
                )
                shortcut_box.set_halign(Gtk.Align.END)
                shortcut_box.set_valign(Gtk.Align.CENTER)

                keys = registry.split_shortcut_keys(item["shortcut"])

                for i, key in enumerate(keys):
                    shortcut_box.pack_start(self.create_key_badge(key), False, False, 0)
                    if i < len(keys) - 1:
                        sep = Gtk.Label(label="+")
                        sep.get_style_context().add_class("shortcut-separator")
                        shortcut_box.pack_start(sep, False, False, 2)

                hbox.pack_end(shortcut_box, False, False, 0)
                row.add(hbox)
                listbox.add(row)
                search_text = f"{item['label']} {' '.join(keys)}".lower()
                registered_rows.append((row, search_text))

            cat_box.pack_start(listbox, False, False, 0)
            self.main_layout.pack_start(cat_box, False, False, 0)

            self.search_registry[cat_box] = registered_rows

    def _on_row_activated(self, row, category):

        toplevel = self.get_toplevel()

        dialog = KeyCaptureDialog(toplevel, row.action_label)
        response = dialog.run()

        if response == Gtk.ResponseType.OK and dialog.result_shortcut:
            success = registry.update_shortcut(
                category, row.action_name, dialog.result_shortcut
            )

            if success:
                self.render_interface()
                self.show_all()
            else:
                error_dialog = Gtk.MessageDialog(
                    transient_for=toplevel,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Atajo ocupado",
                )
                error_dialog.format_secondary_text(
                    "La combinación seleccionada ya está asignada a otra función."
                )
                error_dialog.run()
                error_dialog.destroy()

        dialog.destroy()

    def _on_search_changed(self, entry):
        search_query = entry.get_text().strip().lower()

        if not search_query:
            for cat_box, rows in self.search_registry.items():
                cat_box.show()
                for row, _ in rows:
                    row.show()
            return

        for cat_box, rows in self.search_registry.items():
            visible_rows_in_category = 0

            for row, search_text in rows:
                if search_query in search_text:
                    row.show()
                    visible_rows_in_category += 1
                else:
                    row.hide()

            if visible_rows_in_category > 0:
                cat_box.show()
            else:
                cat_box.hide()


class KeyCaptureDialog(Gtk.Dialog):
    def __init__(self, parent, action_label):
        super().__init__(title="Cambiar Atajo", transient_for=parent, flags=0)
        self.set_modal(True)
        self.set_default_size(300, 150)

        self.result_shortcut = None
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(15)
        box.set_margin_end(15)
        box.set_margin_top(15)

        msg = Gtk.Label()
        msg.set_markup(
            f"<span size='medium'>Presiona la nueva combinación para:</span>\n<b>{action_label}</b>"
        )
        msg.set_justify(Gtk.Justification.CENTER)
        box.pack_start(msg, False, False, 0)

        self.keys_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.keys_container.set_halign(Gtk.Align.CENTER)
        self.keys_container.set_valign(Gtk.Align.CENTER)
        box.pack_start(self.keys_container, True, True, 10)

        self.placeholder_label = Gtk.Label()
        self.placeholder_label.set_markup(
            "<span foreground='#666666' style='italic'>Esperando entrada de teclado...</span>"
        )
        self.keys_container.pack_start(self.placeholder_label, True, True, 0)

        self.connect("key-press-event", self._on_key_press)

        self.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        self.add_button("Guardar", Gtk.ResponseType.OK)

        self.show_all()

    def create_key_badge(self, text: str) -> Gtk.Box:
        box = Gtk.Box()
        box.get_style_context().add_class("key")
        label = Gtk.Label(label=text)
        box.add(label)
        return box

    def _on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)

        if keyname in [
            "Control_L",
            "Control_R",
            "Shift_L",
            "Shift_R",
            "Alt_L",
            "Alt_R",
            "Super_L",
            "Super_R",
        ]:
            return True

        parts = []
        readable_keys = []

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            parts.append("<control>")
            readable_keys.append("Ctrl")
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            parts.append("<shift>")
            readable_keys.append("Shift")
        if event.state & Gdk.ModifierType.MOD1_MASK:
            parts.append("<alt>")
            readable_keys.append("Alt")

        parts.append(keyname.lower())
        readable_keys.append(keyname.upper())

        self.result_shortcut = "".join(parts)

        for child in self.keys_container.get_children():
            self.keys_container.remove(child)

        for i, key in enumerate(readable_keys):
            self.keys_container.pack_start(self.create_key_badge(key), False, False, 0)

            if i < len(readable_keys) - 1:
                sep = Gtk.Label(label="+")
                sep.get_style_context().add_class("shortcut-separator")
                self.keys_container.pack_start(sep, False, False, 4)

        self.keys_container.show_all()
        return True
