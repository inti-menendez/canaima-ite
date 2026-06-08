from gi.repository import Gtk, Gdk
from core.config_engine import config_manager
from core.terminal_palettes import TERMINAL_PALETTES

style_provider = Gtk.CssProvider()
style_provider.load_from_data(b"""
    .category-title {
        color: #0b6793;
        font-weight: bold;
        font-size: 14px;
        padding: 10px 0 0 10px;
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
    .preferences-row {
        padding: 6px 10px;
    }
    .sidebar-item-label {
        font-size: 12px;
    }
""")

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
)


class SidePreferences(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._handlers = {}
        self.search_registry = {}

        self._setup_header()
        self._setup_search_bar()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.NONE)

        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        scrolled.add(self.main_layout)
        self.pack_start(scrolled, True, True, 0)

        # Inicializar los widgets antes de renderizar la interfaz
        self._init_preference_widgets()
        self.render_interface()
        self.show_all()

        config_manager.connect("config-changed", self._on_config_changed_externally)

    def _setup_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.set_margin_top(5)
        header.set_margin_bottom(5)

        title = Gtk.Label(xalign=0)
        title.set_markup(
            "<span size='small' weight='bold' foreground='#888888'>  CONFIGURACIÓN DEL ENTORNO</span>"
        )
        header.pack_start(title, True, True, 5)

        reset_btn = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name(
            "view-refresh-symbolic", Gtk.IconSize.BUTTON
        )
        reset_btn.add(icon)
        reset_btn.set_relief(Gtk.ReliefStyle.NONE)
        reset_btn.set_tooltip_text("Restablecer valores de fábrica")
        reset_btn.connect("clicked", self._on_reset_clicked)

        header.pack_end(reset_btn, False, False, 0)
        self.pack_start(header, False, False, 0)

    def _setup_search_bar(self):
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar configuración...")
        self.search_entry.get_style_context().add_class("search")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.pack_start(self.search_entry, False, False, 0)

    def _init_preference_widgets(self):
        self.palette_combo = Gtk.ComboBoxText()
        for palette_id in TERMINAL_PALETTES.keys():
            self.palette_combo.append(palette_id, palette_id.replace("_", " ").title())
        self._handlers["palette"] = self.palette_combo.connect(
            "changed",
            lambda cb: config_manager.set(
                "appearance", "terminal_palette", cb.get_active_id()
            ),
        )

        self.font_family_combo = Gtk.ComboBoxText()
        fonts = [
            "Monospace",
            "Canaima Sans",
            "DejaVu Sans Mono",
            "Ubuntu Mono",
            "Fira Code",
            "Unifont Regular",
        ]
        for f in fonts:
            self.font_family_combo.append(f, f)
        self._handlers["font_family"] = self.font_family_combo.connect(
            "changed",
            lambda cb: config_manager.set(
                "appearance", "font_family", cb.get_active_id()
            ),
        )

        self.font_spin = Gtk.SpinButton.new_with_range(8.0, 24.0, 1.0)
        self._handlers["font_size"] = self.font_spin.connect(
            "value-changed",
            lambda sb: config_manager.set(
                "appearance", "font_size", int(sb.get_value())
            ),
        )

        self.cursor_shape_combo = Gtk.ComboBoxText()
        self.cursor_shape_combo.append("block", "Bloque")
        self.cursor_shape_combo.append("underline", "Subrayado")
        self.cursor_shape_combo.append("ibeam", "Línea (I-Beam)")
        self._handlers["cursor_shape"] = self.cursor_shape_combo.connect(
            "changed",
            lambda cb: config_manager.set(
                "appearance", "cursor_shape", cb.get_active_id()
            ),
        )

        self.blink_switch = Gtk.Switch()
        self._handlers["cursor_blink"] = self.blink_switch.connect(
            "notify::active",
            lambda sw, ps: config_manager.set(
                "appearance", "cursor_blink", sw.get_active()
            ),
        )
        self.scroll_spin = Gtk.SpinButton.new_with_range(1000, 100000, 1000)
        self._handlers["scrollback"] = self.scroll_spin.connect(
            "value-changed",
            lambda sb: config_manager.set(
                "terminal", "scrollback_lines", int(sb.get_value())
            ),
        )

        self.shell_combo = Gtk.ComboBoxText()
        self.shell_combo.append("/bin/zsh", "Zsh")
        self.shell_combo.append("/bin/bash", "Bash")
        self.shell_combo.append("/bin/sh", "Sh")
        self._handlers["shell_path"] = self.shell_combo.connect(
            "changed",
            lambda cb: config_manager.set("terminal", "shell_path", cb.get_active_id()),
        )

        self.scroll_key_switch = Gtk.Switch()
        self._handlers["scroll_keystroke"] = self.scroll_key_switch.connect(
            "notify::active",
            lambda sw, ps: config_manager.set(
                "terminal", "scroll_on_keystroke", sw.get_active()
            ),
        )

        self.scroll_out_switch = Gtk.Switch()
        self._handlers["scroll_output"] = self.scroll_out_switch.connect(
            "notify::active",
            lambda sw, ps: config_manager.set(
                "terminal", "scroll_on_output", sw.get_active()
            ),
        )

        self.bell_switch = Gtk.Switch()
        self._handlers["audible_bell"] = self.bell_switch.connect(
            "notify::active",
            lambda sw, ps: config_manager.set(
                "terminal", "audible_bell", sw.get_active()
            ),
        )
        self.sidebar_pos_combo = Gtk.ComboBoxText()
        self.sidebar_pos_combo.append("left", "Izquierda")
        self.sidebar_pos_combo.append("right", "Derecha")
        self._handlers["sidebar_position"] = self.sidebar_pos_combo.connect(
            "changed",
            lambda cb: config_manager.set(
                "ite_features", "sidebar_position", cb.get_active_id()
            ),
        )
        self.session_switch = Gtk.Switch()
        self._handlers["restore_session"] = self.session_switch.connect(
            "notify::active",
            lambda sw, ps: config_manager.set(
                "ite_features", "restore_session", sw.get_active()
            ),
        )

    def _create_row(self, label_text: str, widget: Gtk.Widget) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.get_style_context().add_class("preferences-row")

        label = Gtk.Label(label=label_text, xalign=0)
        label.get_style_context().add_class("sidebar-item-label")

        widget.set_halign(Gtk.Align.END)
        widget.set_valign(Gtk.Align.CENTER)

        hbox.pack_start(label, True, True, 0)
        hbox.pack_end(widget, False, False, 0)

        row.add(hbox)
        return row

    def render_interface(self):
        for child in self.main_layout.get_children():
            self.main_layout.remove(child)

        self.search_registry.clear()

        sections = {
            "APARIENCIA": [
                (
                    "Paleta ANSI:",
                    self.palette_combo,
                    "paleta ansi colores configuracion",
                ),
                (
                    "Tipografía:",
                    self.font_family_combo,
                    "fuente tipografia letra text font",
                ),
                ("Tamaño Letra:", self.font_spin, "tamaño letra size font"),
                (
                    "Forma Cursor:",
                    self.cursor_shape_combo,
                    "forma cursor block underline ibeam",
                ),
                (
                    "Parpadeo Cursor:",
                    self.blink_switch,
                    "parpadeo cursor blink animacion",
                ),
            ],
            "TERMINAL": [
                (
                    "Búfer Líneas:",
                    self.scroll_spin,
                    "bufer lineas scrollback historial",
                ),
                (
                    "Shell por defecto:",
                    self.shell_combo,
                    "shell terminal path bash zsh sh",
                ),
                (
                    "Scroll al Tipear:",
                    self.scroll_key_switch,
                    "scroll al tipear keystroke teclado",
                ),
                (
                    "Scroll al Recibir Salida:",
                    self.scroll_out_switch,
                    "scroll al recibir salida output",
                ),
                (
                    "Alerta Sonora (Bell):",
                    self.bell_switch,
                    "alerta sonora bell sonido campana",
                ),
            ],
            "SISTEMA E INTERFAZ": [
                (
                    "Posición Panel:",
                    self.sidebar_pos_combo,
                    "posicion panel sidebar izquierda derecha",
                ),
                (
                    "Recordar Estado:",
                    self.session_switch,
                    "recordar estado sesion guardar",
                ),
            ],
        }

        for category, items in sections.items():
            cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            cat_label = Gtk.Label(label=category)
            cat_label.set_halign(Gtk.Align.START)
            cat_label.get_style_context().add_class("category-title")
            cat_box.pack_start(cat_label, False, False, 5)

            listbox = Gtk.ListBox()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)

            registered_rows = []

            for label_text, widget, keywords in items:
                row = self._create_row(label_text, widget)
                listbox.add(row)

                search_text = f"{label_text} {keywords}".lower()
                registered_rows.append((row, search_text))

            cat_box.pack_start(listbox, False, False, 0)
            self.main_layout.pack_start(cat_box, False, False, 0)

            self.search_registry[cat_box] = registered_rows

        self.update_view_from_engine()

    def update_view_from_engine(self):
        for handler in self._handlers.values():
            if (
                self.palette_combo.handler_is_connected(handler)
                or self.font_family_combo.handler_is_connected(handler)
                or self.font_spin.handler_is_connected(handler)
                or self.cursor_shape_combo.handler_is_connected(handler)
                or self.blink_switch.handler_is_connected(handler)
                or self.scroll_spin.handler_is_connected(handler)
                or self.shell_combo.handler_is_connected(handler)
                or self.scroll_key_switch.handler_is_connected(handler)
                or self.scroll_out_switch.handler_is_connected(handler)
                or self.bell_switch.handler_is_connected(handler)
                or self.sidebar_pos_combo.handler_is_connected(handler)
                or self.session_switch.handler_is_connected(handler)
            ):
                pass

        self.palette_combo.handler_block(self._handlers["palette"])
        self.font_family_combo.handler_block(self._handlers["font_family"])
        self.font_spin.handler_block(self._handlers["font_size"])
        self.cursor_shape_combo.handler_block(self._handlers["cursor_shape"])
        self.blink_switch.handler_block(self._handlers["cursor_blink"])
        self.scroll_spin.handler_block(self._handlers["scrollback"])
        self.shell_combo.handler_block(self._handlers["shell_path"])
        self.scroll_key_switch.handler_block(self._handlers["scroll_keystroke"])
        self.scroll_out_switch.handler_block(self._handlers["scroll_output"])
        self.bell_switch.handler_block(self._handlers["audible_bell"])
        self.sidebar_pos_combo.handler_block(self._handlers["sidebar_position"])
        self.session_switch.handler_block(self._handlers["restore_session"])

        self.palette_combo.set_active_id(
            config_manager.get("appearance", "terminal_palette") or "canaima_default"
        )
        self.font_family_combo.set_active_id(
            config_manager.get("appearance", "font_family") or "Monospace"
        )
        self.font_spin.set_value(
            float(config_manager.get("appearance", "font_size") or 11.0)
        )
        self.cursor_shape_combo.set_active_id(
            config_manager.get("appearance", "cursor_shape") or "block"
        )
        self.blink_switch.set_active(
            bool(config_manager.get("appearance", "cursor_blink"))
        )
        self.scroll_spin.set_value(
            float(config_manager.get("terminal", "scrollback_lines") or 5000.0)
        )
        self.shell_combo.set_active_id(
            config_manager.get("terminal", "shell_path") or "/bin/zsh"
        )
        self.scroll_key_switch.set_active(
            bool(config_manager.get("terminal", "scroll_on_keystroke"))
        )
        self.scroll_out_switch.set_active(
            bool(config_manager.get("terminal", "scroll_on_output"))
        )
        self.bell_switch.set_active(
            bool(config_manager.get("terminal", "audible_bell"))
        )
        self.sidebar_pos_combo.set_active_id(
            config_manager.get("ite_features", "sidebar_position") or "right"
        )
        self.session_switch.set_active(
            bool(config_manager.get("ite_features", "restore_session"))
        )

        self.palette_combo.handler_unblock(self._handlers["palette"])
        self.font_family_combo.handler_unblock(self._handlers["font_family"])
        self.font_spin.handler_unblock(self._handlers["font_size"])
        self.cursor_shape_combo.handler_unblock(self._handlers["cursor_shape"])
        self.blink_switch.handler_unblock(self._handlers["cursor_blink"])
        self.scroll_spin.handler_unblock(self._handlers["scrollback"])
        self.shell_combo.handler_unblock(self._handlers["shell_path"])
        self.scroll_key_switch.handler_unblock(self._handlers["scroll_keystroke"])
        self.scroll_out_switch.handler_unblock(self._handlers["scroll_output"])
        self.bell_switch.handler_unblock(self._handlers["audible_bell"])
        self.sidebar_pos_combo.handler_unblock(self._handlers["sidebar_position"])
        self.session_switch.handler_unblock(self._handlers["restore_session"])

    def _on_reset_clicked(self, button):
        toplevel = self.get_toplevel()
        confirm = Gtk.MessageDialog(
            transient_for=toplevel,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="¿Restablecer configuración?",
        )
        confirm.format_secondary_text(
            "Esto borrará todas tus personalizaciones de interfaz y restaurará los valores de fábrica."
        )
        response = confirm.run()
        confirm.destroy()

        if response == Gtk.ResponseType.YES:
            config_manager.reset_to_defaults()
            self.update_view_from_engine()

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

    def _on_config_changed_externally(self, emitter, section, key):
        self.update_view_from_engine()
