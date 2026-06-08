from gi.repository import Gtk, Pango, GLib, Gdk
from core.app_storage import storage
from core.event_bus import bus
import os

style_provider = Gtk.CssProvider()
style_provider.load_from_data(b"""
    .history-header {
        padding: 5px 0;
    }
    .history-row {
        padding: 8px 10px;
        border-bottom: 1px solid #1f232a;
    }
    .history-row:hover {
        background-color: #1f232a;
    }
    .command-label {
        font-family: 'Monospace', monospace;
        font-size: 14px;
        color: #a9b1d6;
    }
    .dim-label {
        color: #565f89;
        font-size: 12px;
    }
    .popover-menu-box {
        padding: 4px;
        background-color: #1f232a;
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


class SideHistory(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._setup_header()
        self._setup_search_bar()
        self.search_registry = {}

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_shadow_type(Gtk.ShadowType.NONE)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.connect("row-activated", self.on_row_selected)

        self.scrolled.add(self.listbox)
        self.pack_start(self.scrolled, True, True, 0)

        self.refresh_ui()
        bus.subscribe("command_to_history", self.add_command)

    def _setup_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("history-header")

        title = Gtk.Label(xalign=0)
        title.set_markup(
            "<span size='small' weight='bold' foreground='#888888'>  HISTORIAL RECIENTE</span>"
        )
        header.pack_start(title, True, True, 5)

        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(
            Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        )
        menu_btn.set_relief(Gtk.ReliefStyle.NONE)

        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.get_style_context().add_class("popover-menu-box")

        item_clear = Gtk.ModelButton()
        item_clear.set_property("text", "Limpiar historial")
        item_clear.set_alignment(0.0, 0.5)

        item_clear.connect("clicked", self.on_clear_history)
        item_clear.connect("clicked", lambda _: popover.popdown())

        vbox.add(item_clear)
        vbox.show_all()
        popover.add(vbox)
        menu_btn.set_popover(popover)

        header.pack_end(menu_btn, False, False, 5)
        self.pack_start(header, False, False, 0)

    def _setup_search_bar(self):
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar comando...")
        self.search_entry.get_style_context().add_class("search")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.pack_start(self.search_entry, False, False, 0)

    def _on_search_changed(self, entry):
        search_query = entry.get_text().strip().lower()

        if not search_query:
            for row, command in self.search_registry.items():
                row.show()
            return

        for row, command in self.search_registry.items():
            if search_query in command:
                row.show()
            else:
                row.hide()

    def _create_row(self, data):

        row = Gtk.ListBoxRow()
        row.data = data
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.get_style_context().add_class("history-row")

        event_box = Gtk.EventBox()
        event_box.add(hbox)
        row.add(event_box)

        icon = Gtk.Image.new_from_icon_name(
            "utilities-terminal-symbolic", Gtk.IconSize.MENU
        )

        label = Gtk.Label(xalign=0)
        label.set_markup(
            f"<span foreground='#62ff00'>$</span> <b>{GLib.markup_escape_text(data['command'])}</b>"
        )
        label.get_style_context().add_class("command-label")
        label.set_ellipsize(Pango.EllipsizeMode.END)

        time_label = Gtk.Label(label=data["time"], xalign=1)
        time_label.get_style_context().add_class("dim-label")
        time_label.set_valign(Gtk.Align.CENTER)

        hbox.pack_start(icon, False, False, 0)
        hbox.pack_start(label, True, True, 0)

        hbox.pack_end(time_label, False, False, 0)

        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        event_box.connect("button-press-event", self.on_row_clicked, row)
        row.connect("popup-menu", self.on_row_popup_menu)

        row.show_all()
        self.search_registry[row] = data["command"]
        return row

    def on_row_selected(self, listbox, row):
        if not row:
            return
        action = storage.get_preference(
            "history_component", "default_click_action", "paste"
        )

        if action == "execute":
            bus.publish("execute_command", row.data["command"])
        elif action == "detail":
            bus.publish("show_command_details", row.data)
        else:
            bus.publish("paste_command", row.data["command"])

    def show_context_menu(self, event, row):
        menu = Gtk.Menu()
        d = row.data

        actions = [
            ("Ejecutar", lambda _: bus.publish("execute_command", d["command"])),
            ("Pegar", lambda _: bus.publish("paste_command", d["command"])),
            ("Copiar", lambda _: self.handle_copy(d["command"])),
            ("Eliminar", lambda _: self.handle_delete(row)),
            None,
            ("Ver detalles", lambda _: bus.publish("show_command_details", d)),
        ]

        for act in actions:
            if act is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            item = Gtk.MenuItem(label=act[0])
            item.connect("activate", act[1])
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())
        config_item = Gtk.MenuItem(label="Al clickear...")
        submenu = Gtk.Menu()
        current_pref = storage.get_preference(
            "history_component", "default_click_action", "paste"
        )

        group = None
        for label, action_id in [
            ("Pegar", "paste"),
            ("Ejecutar", "execute"),
            ("Detalles", "detail"),
        ]:
            radio = Gtk.RadioMenuItem.new_with_label_from_widget(group, label)
            group = radio
            radio.set_active(action_id == current_pref)
            radio.connect("activate", self._set_default_action, action_id)
            submenu.append(radio)

        config_item.set_submenu(submenu)
        menu.append(config_item)
        menu.show_all()

        if event:
            menu.popup_at_pointer(event)
        else:
            menu.popup_at_widget(
                row, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
            )

    def handle_copy(self, text):
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)

    def handle_delete(self, row):
        if storage.delete_entry_by_date(row.data["full_date"]):
            self.listbox.remove(row)

    def _set_default_action(self, widget, action_id):
        if widget.get_active():
            storage.set_preference(
                "history_component", "default_click_action", action_id
            )

    def add_command(self, command):
        children = self.listbox.get_children()
        if children and children[0].data["command"] == command:
            return

        command_data = storage.save_to_history(command, os.getcwd())

        row = self._create_row(command_data)
        self.listbox.insert(row, 0)

    def refresh_ui(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        self.search_registry.clear()

        for item in storage.load_history():
            row = self._create_row(item)
            self.listbox.add(row)

    def on_clear_history(self, btn):
        storage.delete_history()
        self.refresh_ui()

    def on_row_clicked(self, widget, event, row):
        if event.button == 3:
            self.show_context_menu(event, row)
            return True
        return False

    def on_row_popup_menu(self, row):
        self.show_context_menu(None, row)
        return True
