from gi.repository import Gtk, Gdk

COMMAND_DETAIL_CSS = """
.command-detail-view {
    background-color: #191919;
}

.detail-title {
    color: #ffffff;
}

.detail-key {
    color: #fff;
    font-weight: bold;
    font-size: 12px;
}

.detail-val {
    color: #fff;
    font-size: 13px;
}

.command-box {
    background-color: #141414;
    border: 1px solid #1f232a;
    border-radius: 4px;
    padding: 8px 12px;
}
"""


class CommandDetail(Gtk.ScrolledWindow):
    def __init__(self, data):
        super().__init__()
        self.get_style_context().add_class("command-detail-view")
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(COMMAND_DETAIL_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_border_width(24)
        self.add(vbox)

        title = Gtk.Label(xalign=0)
        title.get_style_context().add_class("detail-title")
        title.set_markup("<span size='large' weight='bold'>Detalles del Comando</span>")
        vbox.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=16, row_spacing=12)
        vbox.pack_start(grid, False, False, 0)

        details = [
            (
                "Comando:",
                f"<span font_family='monospace' weight='bold' foreground='#73daca'>$ {data['command']}</span>",
                True,
            ),
            ("Ejecutado en:", f"<span>{data.get('cwd', '/')}</span>", False),
            ("Hora:", f"<span>{data['time']}</span>", False),
            (
                "Fecha ISO:",
                f"<span size='small' foreground='#565f89'>{data['full_date']}</span>",
                False,
            ),
        ]

        for i, (label, value, is_command) in enumerate(details):
            lbl_key = Gtk.Label(label=label, xalign=1)
            lbl_key.get_style_context().add_class("detail-key")

            lbl_val = Gtk.Label(xalign=0)
            lbl_val.set_markup(value)
            lbl_val.set_line_wrap(True)
            lbl_val.set_selectable(True)
            lbl_val.get_style_context().add_class("detail-val")

            if is_command:
                cmd_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                cmd_container.get_style_context().add_class("command-box")
                cmd_container.pack_start(lbl_val, True, True, 0)
                grid.attach(lbl_key, 0, i, 1, 1)
                grid.attach(cmd_container, 1, i, 1, 1)
            else:
                grid.attach(lbl_key, 0, i, 1, 1)
                grid.attach(lbl_val, 1, i, 1, 1)

        self.show_all()
