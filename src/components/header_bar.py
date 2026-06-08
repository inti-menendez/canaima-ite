from gi.repository import Gtk, Gdk
from core.config_engine import config_manager

HEADER_CSS = """
headerbar {
    background-color: #141414;
    background-image: none;
    border-bottom: 1px solid #1f232a;
    padding: 6px;
    box-shadow: none;
}

headerbar .title {
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
}
headerbar .subtitle {
    color: #565f89;
    font-size: 12px;
}

.linked button {
    color: #a9b1d6;
    padding: 4px 8px;
    border: 1px solid #292e42;
    background-color: #191919;
    background-image: none;
    box-shadow: none;
}
.linked button:hover {
    color: #ffffff;
    background-color: #24283b;
}
.linked button:first-child {
    border-radius: 4px 0 0 4px;
}
.linked button:last-child {
    border-radius: 0 4px 4px 0;
    border-left: none;
}

menu {
    background-color: #141414;
    border: 1px solid #292e42;
    padding: 4px;
}
menu menuitem {
    color: #a9b1d6;
    padding: 6px 14px;
}
menu menuitem:hover {
    background-color: #0b6793;
    color: #ffffff;
}
"""


class CustomHeader(Gtk.HeaderBar):
    def __init__(self, main_box=None):
        super().__init__()
        self.main_box = main_box
        self.set_show_close_button(True)

        self.set_title("Canaima ITE")
        self.set_subtitle("CNTI - Pasantías")

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(HEADER_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.box_layout_controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=0
        )
        self.box_layout_controls.get_style_context().add_class("linked")

        self.btn_toggle_sidebar = Gtk.Button()
        self.btn_toggle_sidebar.set_tooltip_text("Alternar Panel Lateral")
        self._update_sidebar_icon()
        self.btn_toggle_sidebar.connect("clicked", self._on_toggle_sidebar_clicked)
        self.box_layout_controls.pack_start(self.btn_toggle_sidebar, False, False, 0)

        self.btn_position_menu = Gtk.MenuButton()
        self.btn_position_menu.set_tooltip_text("Posición del Panel Lateral")
        img_menu = Gtk.Image.new_from_icon_name(
            "go-down-symbolic", Gtk.IconSize.BUTTON
        )
        self.btn_position_menu.add(img_menu)

        self.menu_posiciones = Gtk.Menu()

        item_left = Gtk.MenuItem(label="Mover a la izquierda")
        item_left.connect("activate", lambda w: self._change_position("left"))
        self.menu_posiciones.append(item_left)

        item_right = Gtk.MenuItem(label="Mover a la derecha")
        item_right.connect("activate", lambda w: self._change_position("right"))
        self.menu_posiciones.append(item_right)

        self.menu_posiciones.show_all()
        self.btn_position_menu.set_popup(self.menu_posiciones)
        self.box_layout_controls.pack_start(self.btn_position_menu, False, False, 0)

        self.pack_end(self.box_layout_controls)

        config_manager.connect("config-changed", self._on_config_changed)

        self.show_all()

    def _update_sidebar_icon(self):
        posicion = config_manager.get("ite_features", "sidebar_position") or "right"

        if posicion == "right":
            icon_name = "view-right-pane-symbolic"
        else:
            icon_name = "view-left-pane-symbolic"

        try:
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        except Exception:
            img = Gtk.Image.new_from_icon_name(
                "format-justify-fill-symbolic", Gtk.IconSize.BUTTON
            )

        old_child = self.btn_toggle_sidebar.get_child()
        if old_child:
            self.btn_toggle_sidebar.remove(old_child)

        self.btn_toggle_sidebar.add(img)
        self.btn_toggle_sidebar.show_all()

    def _on_toggle_sidebar_clicked(self, button):
        if not self.main_box:
            return

        side_panel = self.main_box.side_panel
        is_revealed = side_panel.get_reveal_child()

        if is_revealed:
            side_panel.set_reveal_child(False)
            for btn in self.main_box.activity_bar.get_btns():
                btn.set_active(False)
        else:
            side_panel.set_reveal_child(True)
            side_panel.show()

    def _change_position(self, new_pos):
        current_pos = config_manager.get("ite_features", "sidebar_position") or "right"
        if new_pos != current_pos:
            config_manager.set("ite_features", "sidebar_position", new_pos)

    def _on_config_changed(self, emitter, section, key):
        if section == "ite_features" and key == "sidebar_position":
            self._update_sidebar_icon()
