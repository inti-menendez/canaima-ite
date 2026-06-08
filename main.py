import gi
import os
import sys

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")

from gi.repository import Gtk  # noqa: E402
from src.window import MainWindow  # noqa: E402
from core.config_engine import config_manager  # noqa


def set_appearance():
    settings = Gtk.Settings.get_default()

    if settings is None:
        return

    settings.set_property("gtk-application-prefer-dark-theme", True)
    settings.set_property("gtk-theme-name", "Adwaita")

    home_icons = os.path.expanduser("~/.local/share/icons/Tela")
    system_icons = "/usr/share/icons/Tela"

    if os.path.exists(home_icons) or os.path.exists(system_icons):
        settings.set_property("gtk-icon-theme-name", "Tela")
    else:
        settings.set_property("gtk-icon-theme-name", "Adwaita")


def main():
    app = Gtk.Application()

    def on_activate(application):
        set_appearance()
        MainWindow(application)

    app.connect("activate", on_activate)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
