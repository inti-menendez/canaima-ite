from gi.repository import Gtk
from core.config_engine import config_manager

from .left_container import LeftContainer
from .activity_bar import ActivityBar
from .side_panel import SidePanel


class MainBox(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.left_container = LeftContainer()
        self.side_panel = SidePanel()
        self.activity_bar = ActivityBar(self.side_panel)

        self.block_save = False

        self.order_view()

        config_manager.connect("config-changed", self._on_config_changed)

        self.paned.connect("notify::position", self.on_position_changed)
        self.show_all()

    def order_view(self):
        self.block_save = True

        for child in self.get_children():
            self.remove(child)

        for child in self.paned.get_children():
            self.paned.remove(child)

        posicion = config_manager.get("ite_features", "sidebar_position") or "right"
        total_width = self.paned.get_allocated_width()
        ancho_guardado = config_manager.get("ite_features", "sidebar_width") or 300

        if posicion == "right":
            self.paned.pack1(self.left_container, True, False)
            self.paned.pack2(self.side_panel, False, True)

            self.pack_start(self.paned, True, True, 0)
            self.pack_start(self.activity_bar, False, False, 0)
            self.paned.set_position(total_width - int(ancho_guardado))
        else:
            self.paned.pack1(self.side_panel, False, True)
            self.paned.pack2(self.left_container, True, False)

            self.pack_start(self.activity_bar, False, False, 0)
            self.pack_start(self.paned, True, True, 0)
            self.paned.set_position(int(ancho_guardado))

        self.block_save = False
        self.show_all()

    def on_position_changed(self, paned, scroll_type):
        if self.block_save:
            return

        pos = self.paned.get_position()
        total_width = self.paned.get_allocated_width()

        if total_width < 100 or pos <= 0:
            return

        posicion = config_manager.get("ite_features", "sidebar_position") or "right"
        widget_panel = (
            self.paned.get_child1() if posicion == "left" else self.paned.get_child2()
        )

        ancho_actual_panel = pos if posicion == "left" else (total_width - pos)

        if ancho_actual_panel < 150:
            if widget_panel:
                widget_panel.hide()
        else:
            if widget_panel:
                widget_panel.show()
            config_manager.set("ite_features", "sidebar_width", ancho_actual_panel)

    def _on_config_changed(self, emitter, section, key):
        if section == "ite_features" and key == "sidebar_position":
            self.order_view()
