from gi.repository import Gtk, Gdk, GLib
from core.event_bus import bus
import os

FOOTER_CSS = """
.app-footer {
    background-color: #191919;
    border-top: 1px solid #1f232a;
    padding: 8px 12px;
}
.footer-label {
    color: #fff;
    font-size: 13px;
    font-weight: 500;
}
.footer-label-accent {
    color: #7aa2f7;
    font-weight: bold;
}
.footer-separator {
    color: #292e42;
    margin-left: 8px;
    margin-right: 8px;
}

.footer-btn {
    color: #a9b1d6;
    padding: 2px 6px;
    border: none;
    background: transparent;
    font-size: 12px;
}
.footer-btn:hover {
    color: #ffffff;
    background-color: #24283b;
    border-radius: 4px;
}
.status-running {
    color: #e0af68; 
    font-weight: bold;
}
.status-success {
    color: #9ece6a; 
    font-weight: bold;
}
.status-error {
    color: #f7768e; 
    font-weight: bold;
}

.ia-status-container {
    margin-left: 4px;
}
.ia-model-name {
    color: #bb9af7;
    font-weight: bold;
}
.ia-state-stopped {
    color: #ff9e64;
    font-style: italic;
}
"""


class Footer(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.get_style_context().add_class("app-footer")

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(FOOTER_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.pack_start(self.left_box, True, True, 0)
        self.pack_end(self.right_box, False, False, 0)

        self.btn_shell = Gtk.MenuButton()
        self.btn_shell.get_style_context().add_class("footer-btn")
        self.btn_shell.set_label("Zsh")
        self._build_shell_menu()

        self.lbl_notebook = self._create_label("Páginas: 1")
        self.lbl_explorer = self._create_label("~")

        self.lbl_process_status = self._create_label("• Listo")
        self.lbl_process_status.get_style_context().add_class("status-success")

        self.left_box.pack_start(self.btn_shell, False, False, 0)
        self.left_box.pack_start(self._create_divider(), False, False, 0)
        self.left_box.pack_start(self.lbl_notebook, False, False, 0)
        self.left_box.pack_start(self._create_divider(), False, False, 0)
        self.left_box.pack_start(self.lbl_explorer, False, False, 0)
        self.left_box.pack_start(self._create_divider(), False, False, 0)
        self.left_box.pack_start(self.lbl_process_status, False, False, 0)

        self.lbl_terminal = self._create_label("Ln: 1, Col: 1")

        self.zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.btn_zoom_out = Gtk.Button(label="-")
        self.btn_zoom_in = Gtk.Button(label="+")
        self.btn_zoom_in.get_style_context().add_class("footer-btn")
        self.btn_zoom_out.get_style_context().add_class("footer-btn")

        self.btn_zoom_in.connect(
            "clicked", lambda w: bus.publish("terminal_zoom", "in")
        )
        self.btn_zoom_out.connect(
            "clicked", lambda w: bus.publish("terminal_zoom", "out")
        )

        self.ia_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.ia_box.get_style_context().add_class("ia-status-container")

        self.ia_spinner = Gtk.Spinner()

        self.ia_icon = Gtk.Image()
        self.ia_label = Gtk.Label()
        self.ia_label.get_style_context().add_class("footer-label-accent")

        self.lbl_ia_status = self._create_label("• Reposo")
        self.lbl_ia_status.get_style_context().add_class("status-success")

        self.ia_box.pack_start(self.ia_spinner, False, False, 0)
        self.ia_box.pack_start(self.lbl_ia_status, False, False, 0)
        self.ia_box.pack_start(self.ia_label, False, False, 0)
        self.ia_box.pack_start(self.ia_icon, False, False, 0)

        self.right_box.pack_start(self.lbl_terminal, False, False, 0)
        self.right_box.pack_start(self._create_divider(), False, False, 0)
        self.zoom_box.pack_start(self.btn_zoom_out, False, False, 0)
        self.zoom_box.pack_start(self.btn_zoom_in, False, False, 0)
        self.right_box.pack_start(self.zoom_box, False, False, 0)
        self.right_box.pack_start(self._create_divider(), False, False, 0)
        self.right_box.pack_start(self.ia_box, False, False, 0)

        self.subscribe()
        self.show_all()
        self.ia_spinner.hide()
        GLib.timeout_add(5000, self.request_provider_status)

    def request_provider_status(self):
        bus.publish("request_provider_status")
        return True

    def _create_label(self, default_text):
        label = Gtk.Label(label=default_text)
        label.get_style_context().add_class("footer-label")
        return label

    def _create_divider(self):
        div = Gtk.Label(label="|")
        div.get_style_context().add_class("footer-separator")
        return div

    def _build_shell_menu(self):
        menu = Gtk.Menu()
        opciones = [
            ("Zsh", "/bin/zsh"),
            ("Bash", "/bin/bash"),
            ("Sh", "/bin/sh"),
            ("Python", "/usr/bin/python3"),
        ]
        for nombre, path in opciones:
            if os.path.exists(path):
                item = Gtk.MenuItem(label=nombre)
                item.connect("activate", self._on_shell_selected, nombre, path)
                menu.append(item)
        menu.show_all()
        self.btn_shell.set_popup(menu)

    def _on_shell_selected(self, widget, nombre, path):
        self.btn_shell.set_label(nombre)
        bus.publish("change_active_terminal_shell", path)

    def subscribe(self):
        bus.subscribe("notebook_num_pages", self.set_notebook_num_pages)
        bus.subscribe("on_shell_changed", self.set_shell)
        bus.subscribe("term_cursor_move", self.set_cursor_pos)
        bus.subscribe("explorer_path_change", self.set_explorer_path)
        bus.subscribe("provider_change", self._on_ia_provider_changed)
        bus.subscribe("terminal_process_status", self.set_process_status)
        bus.subscribe("ia_state_changed", self.set_ia_state)

    def set_notebook_num_pages(self, data):
        self.lbl_notebook.set_text(f"Páginas: {data}")

    def set_shell(self, data):
        self.btn_shell.set_label(str(data))

    def set_cursor_pos(self, data):
        row, col = data
        self.lbl_terminal.set_text(f"Ln {row}, Col {col}")

    def set_explorer_path(self, data):
        path = str(data)
        if len(path) > 35:
            path = "..." + path[-32:]
        self.lbl_explorer.set_text(path)

    def _on_ia_provider_changed(self, info):
        def update_provider_ui():
            mode = info.get("mode")
            status = info.get("status")
            label_text = info.get("label", "")
            tooltip_text = info.get("tooltip", "")

            self.ia_label.set_text(label_text)

            self.ia_icon.set_tooltip_text(tooltip_text)
            self.ia_label.set_tooltip_text(tooltip_text)

            if mode == "local":
                if status == "online":
                    self.ia_icon.set_from_icon_name(
                        "computer-symbolic", Gtk.IconSize.MENU
                    )
                else:
                    self.ia_icon.set_from_icon_name(
                        "computer-fail-symbolic", Gtk.IconSize.MENU
                    )
            elif mode == "cloud":
                if status == "online":
                    self.ia_icon.set_from_icon_name(
                        "network-transmit-receive-symbolic", Gtk.IconSize.MENU
                    )
                elif status == "no_internet":
                    self.ia_icon.set_from_icon_name(
                        "network-offline-symbolic", Gtk.IconSize.MENU
                    )
            return False

        GLib.idle_add(update_provider_ui)

    def set_ia_state(self, state):

        def update_ui():
            context = self.lbl_ia_status.get_style_context()
            context.remove_class("status-running")
            context.remove_class("status-success")
            context.remove_class("ia-state-stopped")

            if state == "thinking":
                self.ia_spinner.show()
                self.ia_spinner.start()
                self.lbl_ia_status.set_text("● Generando...")
                context.add_class("status-running")

            elif state == "stopped":
                self.ia_spinner.stop()
                self.ia_spinner.hide()
                self.lbl_ia_status.set_text("■ Detenida")
                context.add_class("ia-state-stopped")

            else:
                self.ia_spinner.stop()
                self.ia_spinner.hide()
                self.lbl_ia_status.set_text("• Reposo")
                context.add_class("status-success")
            return False

        GLib.idle_add(update_ui)

    def set_process_status(self, data):
        context = self.lbl_process_status.get_style_context()
        context.remove_class("status-running")
        context.remove_class("status-success")
        context.remove_class("status-error")
        status, exit_code = data
        if status == "running":
            self.lbl_process_status.set_text("● Ejecutando...")
            context.add_class("status-running")
        elif status == "success":
            self.lbl_process_status.set_text("✔ Éxito")
            context.add_class("status-success")
        elif status == "failed":
            self.lbl_process_status.set_text(f"✖ Error: {exit_code}")
            context.add_class("status-error")
