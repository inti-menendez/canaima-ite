from gi.repository import Gtk, Gdk
from core.config_engine import config_manager

ACTIVITY_BAR_CSS = """
.activity-bar {
    background-color: #141414;
}
.activity-bar-left {
    border-right: 1px solid #1f232a;
}
.activity-bar-right {
    border-left: 1px solid #1f232a;
}
.nav-button {
    color: #fff;
    padding: 12px 4px;
    border-radius: 0px;
}
.nav-button:hover {
    color: #a9b1d6;
    background-color: transparent;
}
.activity-bar-left .nav-button:checked {
    border-left: 2px solid #0b6793;
    border-right: none;
}
.activity-bar-right .nav-button:checked {
    border-right: 2px solid #0b6793;
    border-left: none;
}
"""


class ActivityBar(Gtk.Box):
    """
    el parametro side panel representa el panel lateral que este activity bar controla
    lo ideal seria evitar el acoplamiento pero como ambos componentes estan
    fuertemente relacionados pues bueno
    """

    def __init__(self, side_panel):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("activity-bar")

        self.update_position()

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(ACTIVITY_BAR_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.side_panel = side_panel
        self.side_panel_stack = side_panel.stack
        self.set_size_request(60, -1)

        self.btn_chat = self._create_nav_button(
            "chat-message-new-symbolic",
            "side_chatbot",
            "Chat con inteligencia Artificial",
        )
        self.btn_settings = self._create_nav_button(
            "emblem-system-symbolic", "side_settings", "Configuración"
        )
        self.btn_any_util = self._create_nav_button(
            "dialog-information-symbolic", "side_keybindings", "Atajos de teclado"
        )
        self.btn_show_history = self._create_nav_button(
            "document-open-recent-symbolic", "side_history", "Historial de Comandos"
        )
        self.btn_directories = self._create_nav_button(
            "inode-directory-symbolic", "side_explorer", "Explorador de Archivos"
        )

        self.pack_start(self.btn_chat, False, False, 0)
        self.pack_start(self.btn_directories, False, False, 0)
        self.pack_start(self.btn_show_history, False, False, 0)
        self.pack_end(self.btn_settings, False, False, 0)
        self.pack_end(self.btn_any_util, False, False, 0)

        self.show_all()

    def update_position(self):
        context = self.get_style_context()
        position = config_manager.get("ite_features", "sidebar_position") or "right"

        if position == "right":
            context.remove_class("activity-bar-left")
            context.add_class("activity-bar-right")
        else:
            context.remove_class("activity-bar-right")
            context.add_class("activity-bar-left")

    def _create_nav_button(self, icon_name, page_name, tooltip_text):
        btn = Gtk.ToggleButton()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(tooltip_text)

        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        btn.add(img)
        btn.get_style_context().add_class("nav-button")

        btn.connect("clicked", self._on_nav_clicked, page_name)
        return btn

    def _on_nav_clicked(self, button, page_name):
        """
        maneja los eventos de click en el activity bar
        si se hace click en un boton que no esta activo,
        se activa y se muestra su pagina si se hace click
        en un boton que ya esta activo, se cierra el panel lateral
        """
        is_active = button.get_active()
        current_page = self.side_panel_stack.get_visible_child_name()
        is_open = self.side_panel.get_reveal_child()

        if is_active:
            for b in self.get_btns():
                if b != button:
                    b.set_active(False)
            self.side_panel_stack.set_visible_child_name(page_name)
            self.update_position()

            total_width = self.side_panel.get_parent().get_allocated_width()
            position = config_manager.get("ite_features", "sidebar_position") or "right"
            width = self.side_panel.width
            if position == "right":
                self.side_panel.get_parent().set_position(total_width - width)
            else:
                self.side_panel.get_parent().set_position(width)

            self.side_panel.show()
            self.side_panel.set_reveal_child(True)
            config_manager.set("ite_features", "show_sidebar", True)

        else:
            if is_open and current_page == page_name:
                self.side_panel.set_reveal_child(False)
                config_manager.set("ite_features", "show_sidebar", False)

    def get_btns(self):
        for i in vars(self):
            if i.startswith("btn_"):
                yield getattr(self, i)
