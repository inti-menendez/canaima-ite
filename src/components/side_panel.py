from gi.repository import Gtk

from .chat_bot import ChatBot
from .side_keybindings import SideKeybindings
from .side_explorer import sideExplorer
from .side_history import SideHistory
from core.keybindings_engine import registry
from .side_preferences import SidePreferences


class SidePanelActions:
    def __init__(self, side_panel):
        self.panel = side_panel

    def register(self):
        registry.register_command("side_chatbot", self.switch_to_chatbot, self.panel)
        registry.register_command("side_explorer", self.switch_to_explorer, self.panel)
        registry.register_command("side_history", self.switch_to_history, self.panel)
        registry.register_command(
            "side_keybindings", self.switch_to_keybindings, self.panel
        )
        registry.register_command("side_settings", self.switch_to_settings, self.panel)
        registry.register_command("toggle", self.toggle_panel_visibility, self.panel)

    def switch_to_chatbot(self):
        self.panel.switch_to("side_chatbot")

    def switch_to_explorer(self):
        self.panel.switch_to("side_explorer")

    def switch_to_history(self):
        self.panel.switch_to("side_history")

    def switch_to_keybindings(self):
        self.panel.switch_to("side_keybindings")

    def switch_to_settings(self):
        self.panel.switch_to("side_settings")

    def toggle_panel_visibility(self):
        is_revealed = self.panel.get_reveal_child()
        if is_revealed:
            self.panel.set_reveal_child(False)
        else:
            self.panel.set_visible(True)
            self.panel.set_reveal_child(True)


class SidePanel(Gtk.Revealer):
    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.NONE)
        self.width = 300
        self.stack = Gtk.Stack()
        self.stack.set_size_request(self.width, -1)
        self.add(self.stack)

        self.chat_bot = ChatBot()
        self.explorer = sideExplorer()
        self.history = SideHistory()
        self.keybindings = SideKeybindings()
        self.preferences = SidePreferences()

        self.stack.add_named(self.chat_bot, "side_chatbot")
        self.stack.add_named(self.explorer, "side_explorer")
        self.stack.add_named(self.history, "side_history")
        self.stack.add_named(self.keybindings, "side_keybindings")
        self.stack.add_named(self.preferences, "side_settings")

        self.actions = SidePanelActions(self)
        self.actions.register()

        self.connect("notify::child-revealed", self.on_reveal_child_notify)
        self.connect("size-allocate", self.report_size)

        self.connect("focus-in-event", self._on_focus_in)
        self.connect("focus-out-event", self._on_focus_out)
        self.get_style_context().add_class("ite-side-panel")

        self.show_all()
        self.set_reveal_child(True)

    def report_size(self, widget, allocate):
        self.width = allocate.width

    def on_reveal_child_notify(self, revealer, pspec):
        if not self.get_reveal_child() and not self.get_child_revealed():
            self.set_visible(False)

    def _on_focus_in(self, widget, event):
        self.get_style_context().add_class("side-panel-activo")
        return False

    def _on_focus_out(self, widget, event):
        self.get_style_context().remove_class("side-panel-activo")
        return False

    def switch_to(self, nombre_stack):
        active_child = self.get_child_revealed()
        is_same = self.stack.get_visible_child_name() == nombre_stack
        if active_child and is_same:
            self.set_visible(False)
            self.set_reveal_child(False)
        else:
            self.set_visible(True)
            self.set_reveal_child(True)
            self.stack.set_visible_child_name(nombre_stack)

        hijo_actual = self.stack.get_visible_child()
        if hijo_actual:
            if hasattr(hijo_actual, "grab_focus_internal"):
                hijo_actual.grab_focus_internal()
            else:
                hijo_actual.grab_focus()
