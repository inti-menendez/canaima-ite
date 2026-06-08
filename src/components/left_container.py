from gi.repository import Gtk, Vte, Gdk
from .terminal_box import TerminalBox
from core.event_bus import bus
from .command_detail import CommandDetail
from core.keybindings_engine import registry
import os

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logo_path = os.path.join(current_dir, "..", "assets", "canaima-logo.png")

CSS = f"""
.notebook {{
    background: url('file://{logo_path}') no-repeat center;
    background-size: 300px;
    border: none;
}}

.notebook stack {{
    background-color: transparent;
}}

.notebook header {{
    background-color: #141414;
    border-bottom: 1px solid #1f232a;
    padding: 2px;
}}

.notebook tab {{
    background-color: #141414;
    color: #565f89;
    font-weight: 500;
    border: 1px solid transparent;
    border-bottom: none;
    padding: 4px 8px;
    margin: 0 2px;
    border-radius: 4px 4px 0 0;
}}

notebook tab:checked {{
    background-color: #191919;
    color: #ffffff;
    border-left: 1px solid #1f232a;
    border-right: 1px solid #1f232a;
}}

notebook tab:hover:not(:checked) {{
    background-color: #1c2026;
    color: #a9b1d6;
}}

toolbar {{
    background-color: transparent;
    border: none;
    padding: 0;
}}

.linked button {{
    color: #a9b1d6;
    padding: 4px 6px;
    border: 1px solid #292e42;
    background-color: #191919;
}}

.linked button:hover {{
    color: #ffffff;
    background-color: #24283b;
}}

.linked button:first-child {{
    border-radius: 4px 0 0 4px;
}}

.linked button:last-child {{
    border-radius: 0 4px 4px 0;
    border-left: none;
}}

.tab-entry {{
    background: #141414;
    color: #ffffff;
    border: 1px solid #0b6793;
    border-radius: 3px;
    padding: 0 4px;
    margin: 0;
    font-size: 12px;
}}

.tab-close-btn {{
    color: #aaa;
    padding: 0;
    margin: 0 0 0 4px;
}}

.tab-close-btn:hover {{
    background-color: transparent;
}}

menu {{
    background-color: #141414;
    border: 1px solid #292e42;
    padding: 4px;
}}

menu menuitem {{
    color: #a9b1d6;
    padding: 6px 12px;
}}

menu menuitem:hover {{
    background-color: #0b6793;
    color: #ffffff;
}}
"""


class LeftContainer(Gtk.Notebook):
    def __init__(self):
        super().__init__()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self.get_style_context().add_class("notebook")

        self.set_scrollable(True)
        self.config_tool_bar(self.new_term_btn, self.menu_btn)

        self.terminal = TerminalBox(self)

        self.set_group_name("tabs")

        bus.subscribe("show_command_details", self.open_detail_tab)
        self.connect("switch-page", self.on_change_tab)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self.on_notebook_clicked)

        self.connect("page-added", self.added_pages)
        self.connect("page-removed", self.removed_pages)

        self.show_all()
        self.register()

    def register(self):
        registry.register_command("close", self.close_tab, self)
        registry.register_command("close_all", self.close_all_tabs, self)

    def added_pages(self, notebook, widget, idx_tab):
        bus.publish("notebook_num_pages", self.get_n_pages())

    def removed_pages(self, notebook, widget, idx_tab):
        bus.publish("notebook_num_pages", self.get_n_pages())

    def on_notebook_clicked(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            self.terminal.add_terminal_tab()
            return True
        return False

    def close_tab_by_child(self, child_widget):
        if not child_widget:
            return

        child_widget.destroy()

        idx = self.page_num(child_widget)
        if idx != -1:
            self.remove_page(idx)

    def close_tab(self):
        current_idx_page = self.get_current_page()
        tab = self.get_nth_page(current_idx_page)
        self.close_tab_by_child(tab)

    def add_custom_tab(self, child_widget, title):
        event_box = Gtk.EventBox()
        event_box.get_style_context().add_class("tab-event-box")

        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        stack = Gtk.Stack()
        label = Gtk.Label(label=title)

        entry = Gtk.Entry()
        entry.get_style_context().add_class("tab-entry")
        entry.set_has_frame(False)
        entry.set_width_chars(10)
        entry.set_alignment(0)

        stack.add_named(label, "label")
        stack.add_named(entry, "entry")

        btn_close = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU
        )
        btn_close.set_relief(Gtk.ReliefStyle.NONE)
        btn_close.get_style_context().add_class("tab-close-btn")

        btn_close.connect("clicked", lambda x: self.close_tab_by_child(child_widget))

        tab_box.pack_start(stack, True, True, 2)
        tab_box.pack_start(btn_close, False, False, 0)

        event_box.add(tab_box)
        event_box.show_all()

        event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        event_box.connect("button-press-event", self.on_tab_event, stack, child_widget)

        entry.connect("activate", self.finish_rename, stack)
        entry.connect("focus-out-event", lambda w, e: self.finish_rename(w, stack))

        index = self.append_page(child_widget, event_box)
        self.set_tab_reorderable(child_widget, True)
        self.show_all()
        self.set_current_page(index)

    def on_tab_event(self, widget, event, stack, child):
        if event.button == 3:
            self.show_tab_context_menu(event, child)
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            label = stack.get_child_by_name("label")
            entry = stack.get_child_by_name("entry")
            entry.set_text(label.get_text())
            stack.set_visible_child_name("entry")
            entry.grab_focus()
            return True

        return False

    def finish_rename(self, entry, stack):
        label = stack.get_child_by_name("label")
        new_text = entry.get_text().strip()
        if new_text:
            label.set_text(new_text)
        stack.set_visible_child_name("label")

    def show_tab_context_menu(self, event, child):
        menu = Gtk.Menu()

        item_close = Gtk.MenuItem(label="Cerrar esta pestaña")
        item_close.connect("activate", lambda x: self.close_tab_by_child(child))

        item_close_others = Gtk.MenuItem(label="Cerrar las demás")
        item_close_others.connect("activate", self.close_other_tabs, child)

        menu.append(item_close)
        menu.append(item_close_others)
        menu.show_all()
        menu.popup_at_pointer(event)

    def close_other_tabs(self, widget, keep_child):
        for i in range(self.get_n_pages() - 1, -1, -1):
            page = self.get_nth_page(i)
            if page != keep_child:
                self.close_tab_by_child(page)

    def on_change_tab(self, notebook, page, page_num):
        if isinstance(page, Vte.Terminal):
            cwd = self.terminal.get_real_cwd(page)
            if cwd:
                bus.publish("sent_cwd", cwd)
            if hasattr(page, "shell"):
                bus.publish("on_shell_changed", page.shell)

    def open_detail_tab(self, data):
        detail_view = CommandDetail(data)
        lbl = "Detalle: " + data["command"][:5] + "..."
        self.add_custom_tab(detail_view, lbl)

    def new_term_btn(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox.get_style_context().add_class("linked")

        main_btn = Gtk.Button()
        main_btn.set_tooltip_text("Nueva Terminal")
        icon_plus = Gtk.Image.new_from_icon_name(
            "tab-new-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        main_btn.add(icon_plus)
        main_btn.set_relief(Gtk.ReliefStyle.NONE)
        main_btn.connect("clicked", lambda x: self.terminal.add_terminal_tab())

        arrow_btn = Gtk.MenuButton()
        arrow_btn.set_tooltip_text("Abrir con")
        icon_arrow = Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.MENU)
        arrow_btn.add(icon_arrow)
        arrow_btn.set_relief(Gtk.ReliefStyle.NONE)

        menu = Gtk.Menu()
        opciones = [
            ("Zsh", "/bin/zsh"),
            ("Bash", "/bin/bash"),
            ("Sh", "/bin/sh"),
            ("Python", "/usr/bin/python3"),
        ]

        for nombre, path in opciones:
            if os.path.exists(path):
                item = Gtk.MenuItem(label=f"{nombre}")
                item.connect(
                    "activate",
                    lambda x, p=path: self.terminal.add_terminal_tab(shell_path=p),
                )
                menu.append(item)

        menu.show_all()
        arrow_btn.set_popup(menu)
        hbox.pack_start(main_btn, False, False, 0)
        hbox.pack_start(arrow_btn, False, False, 0)

        tool_item = Gtk.ToolItem()
        tool_item.add(hbox)
        tool_item.show_all()
        return tool_item

    def menu_btn(self):
        menu_btn = Gtk.MenuButton()
        icon = Gtk.Image.new_from_icon_name(
            "view-more-horizontal-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        menu_btn.add(icon)
        menu_btn.set_tooltip_text("Mas acciones")
        menu_btn.set_relief(Gtk.ReliefStyle.NONE)

        tool_item = Gtk.ToolItem()
        tool_item.add(menu_btn)

        menu = Gtk.Menu()
        item1 = Gtk.MenuItem(label="Cerrar todas las pestañas")
        item1.connect("activate", lambda x: self.close_all_tabs())
        item2 = Gtk.MenuItem(label="alguna otra cosa")
        menu.append(item1)
        menu.append(item2)
        menu.show_all()

        menu_btn.set_popup(menu)
        return tool_item

    def close_all_tabs(self):
        for i in range(self.get_n_pages() - 1, -1, -1):
            page = self.get_nth_page(i)
            self.close_tab_by_child(page)

    def config_tool_bar(self, *args):
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)

        for tool_widget in args:
            toolbar.insert(tool_widget(), -1)

        self.set_action_widget(toolbar, Gtk.PackType.END)
        toolbar.show_all()
