from gi.repository import Gtk

from .components import MainBox, CustomHeader, Footer
from core.keybindings_engine import registry


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.set_default_size(1100, 600)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        # <footer statusBar>
        ## TODO aca lo estamos poniendo arriba del todo
        # para que se subscriba antes de que se publique y no despues
        # tratar de corregir para que se vea mas entendible
        self.vbox.pack_end(Footer(), False, False, 0)

        registry.load_initial_shortcuts()

        registry.register_command("app_close", app.quit, app)
        # </footer statusBar>
        # <headerBar>
        self.main_box = MainBox()
        self.set_titlebar(CustomHeader(self.main_box))
        # </headerBar>

        # <box main body>

        self.vbox.pack_start(self.main_box, True, True, 0)

        # </box main body>

        self.show_all()

        self.connect(
            "destroy",
            lambda w: (self.main_box.side_panel.chatbot.cleanup(), app.quit()),
        )
