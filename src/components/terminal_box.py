import os
import signal
import re
from gi.repository import Gtk, Vte, GLib, Gdk, Pango
from core.keybindings_engine import registry
from core.event_bus import bus
from core.config_engine import config_manager


class TerminalActions:
    def __init__(self, terminal_box):
        self.box = terminal_box

    def register(self):
        registry.register_command("copy", self.copy, self.box)
        registry.register_command("paste", self.paste, self.box)
        registry.register_command("split_vertical", self.split_vertical, self.box)
        registry.register_command("split_horizontal", self.split_horizontal, self.box)
        registry.register_command("close_split", self.close_active_split, self.box)
        registry.register_command("zoom_in", self.zoom_in, self.box)
        registry.register_command("zoom_out", self.zoom_out, self.box)

        registry.register_command("navigate_left", self.navigate_left, self.box)
        registry.register_command("navigate_right", self.navigate_right, self.box)
        registry.register_command("navigate_up", self.navigate_up, self.box)
        registry.register_command("navigate_down", self.navigate_down, self.box)

        registry.register_command("new_terminal", self.new_terminal, self.box)
        
        registry.register_command("focus_terminal", self.focus_terminal, self.box)

    def get_active_term(self):
        return self.box.get_current_terminal()

    def copy(self):
        term = self.get_active_term()
        if term and term.get_has_selection():
            term.copy_clipboard()

    def paste(self):
        term = self.get_active_term()
        if term:
            term.paste_clipboard()

    def split_vertical(self):
        term = self.get_active_term()
        if term:
            position = term.get_allocation().width / 2
            self.box.split_terminal(term, Gtk.Orientation.HORIZONTAL, position)

    def split_horizontal(self):
        term = self.get_active_term()
        if term:
            position = term.get_allocation().height / 2
            self.box.split_terminal(term, Gtk.Orientation.VERTICAL, position)

    def close_active_split(self):
        term = self.get_active_term()
        if term:
            self.box.kill_term(term)

    def zoom_in(self):
        self.box._on_footer_request_zoom("in")

    def zoom_out(self):
        self.box._on_footer_request_zoom("out")

    def new_terminal(self):
        self.box.add_terminal_tab()

    def navigate_left(self):
        self._navigate_paned(Gtk.Orientation.HORIZONTAL, to_child1=True)

    def navigate_right(self):
        self._navigate_paned(Gtk.Orientation.HORIZONTAL, to_child1=False)

    def navigate_up(self):
        self._navigate_paned(Gtk.Orientation.VERTICAL, to_child1=True)

    def navigate_down(self):
        self._navigate_paned(Gtk.Orientation.VERTICAL, to_child1=False)

    def _navigate_paned(self, orientation, to_child1):
        term = self.get_active_term()
        if not term:
            return
        parent = term.get_parent()
        while parent and not isinstance(parent, Gtk.Notebook):
            if (
                isinstance(parent, Gtk.Paned)
                and parent.get_property("orientation") == orientation
            ):
                target = parent.get_child1() if to_child1 else parent.get_child2()
                if target:
                    child_term = self.box._find_terminal_recursive(target)
                    if child_term:
                        child_term.grab_focus()
                        break
            parent = parent.get_parent()

    def focus_terminal(self):
        term = self.get_active_term()
        if term:
            term.grab_focus()


class TerminalBox(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.cursor_column = 0
        self.cursor_row = 0
        self.parent = parent

        self.actions = TerminalActions(self)
        self.register_commands()

        self.add_terminal_tab()
        self.show_all()
        self.subscribe()

        self.config_handler_id = config_manager.connect(
            "config-changed", self._on_global_config_changed
        )
        self.connect("destroy", self._on_destroy)

    def register_commands(self):
        self.actions.register()

    def subscribe(self):
        bus.subscribe("request_terminal_prompt", self.send_prompt_to_chatbot)
        bus.subscribe("paste_command", self.paste_command)
        bus.subscribe("execute_command", self.execute_command)
        bus.subscribe("open_in_new_terminal", self.open_in_new_terminal)
        bus.subscribe("exec_in_new_terminal", self.exec_in_new_terminal)
        bus.subscribe(
            "change_active_terminal_shell", self._on_footer_request_shell_change
        )
        bus.subscribe("terminal_zoom", self._on_footer_request_zoom)

    def open_in_new_terminal(self, data):
        self.add_terminal_tab(data)

    def exec_in_new_terminal(self, data):
        if isinstance(data, list):
            command, title = data
        else:
            command, title = data, None

        if title:
            self.add_terminal_tab(".", title=title)
        else:
            self.add_terminal_tab(".")

        if command:
            GLib.timeout_add(50, self.execute_command, command)

    def add_terminal_tab(self, path=None, shell_path=None, title=None):
        term = self.create_vte_terminal(path=path, shell_path=shell_path)
        if not title:
            try:
                n_pages = self.parent.get_n_pages()
            except AttributeError:
                n_pages = 0
            title = f"Terminal {n_pages + 1}"

        self.parent.add_custom_tab(term, title)
        term.grab_focus()

    def on_key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if Gdk.KEY_1 <= event.keyval <= Gdk.KEY_9:
                target_page = event.keyval - Gdk.KEY_1
                if target_page < self.parent.get_n_pages():
                    self.parent.set_current_page(target_page)
                return True

        terminal = self.get_current_terminal()
        if not terminal:
            return False

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_BackSpace:
                terminal.feed_child(b"\x17")
                return True
            elif event.keyval == Gdk.KEY_Delete:
                terminal.feed_child(b"\x1bd")
                return True

        if event.keyval == Gdk.KEY_Return:
            command = self.get_command_from_current_command_line(terminal)
            if command:
                bus.publish("command_to_history", command)

        return False

    def on_cursor_moved(self, terminal):
        col, row = terminal.get_cursor_position()
        if row != self.cursor_row:
            GLib.timeout_add(50, self.update_prompt_boundary, terminal)
        bus.publish("term_cursor_move", [row, col])

    def update_prompt_boundary(self, terminal):
        col, row = terminal.get_cursor_position()
        self.cursor_column = col
        self.cursor_row = row
        return False

    def get_command_from_current_command_line(self, terminal):
        col, row = terminal.get_cursor_position()
        cols_totales = terminal.get_column_count()
        texto, _ = terminal.get_text_range_format(
            Vte.Format.TEXT, row, self.cursor_column, row, cols_totales
        )
        return texto.strip()

    def send_prompt_to_chatbot(self, data):
        terminal = self.get_current_terminal()
        if terminal:
            data = self.get_command_from_current_command_line(terminal)
            bus.publish("sent_terminal_prompt", data)

    def get_current_terminal(self):
        toplevel = self.parent.get_toplevel()
        while toplevel and not isinstance(toplevel, Gtk.Window):
            toplevel = toplevel.get_parent()

        if toplevel and hasattr(toplevel, "get_focus"):
            focused_widget = toplevel.get_focus()
            if isinstance(focused_widget, Vte.Terminal):
                return focused_widget

        current_page_index = self.parent.get_current_page()
        if current_page_index == -1:
            return None

        container = self.parent.get_nth_page(current_page_index)
        return self._find_terminal_recursive(container)

    def _find_terminal_recursive(self, widget):
        if isinstance(widget, Vte.Terminal):
            return widget
        if isinstance(widget, Gtk.Container):
            focus_child = widget.get_focus_child()
            if focus_child:
                return self._find_terminal_recursive(focus_child)
            children = widget.get_children()
            if children:
                return self._find_terminal_recursive(children[0])
        return None

    def _get_all_terminals_recursive(self, widget, terminal_list):
        if isinstance(widget, Vte.Terminal):
            terminal_list.append(widget)
        elif isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                self._get_all_terminals_recursive(child, terminal_list)

    def get_real_cwd(self, terminal):
        try:
            pid = terminal.get_child_pid()
            if pid > 0:
                return os.readlink(f"/proc/{pid}/cwd")
        except Exception:
            pass
        return self.get_cwd(terminal)

    def get_cwd(self, terminal):
        if not terminal:
            return None
        prop = terminal.get_termprop_string("xterm.title")
        if prop is None:
            return None
        title = prop[0] if isinstance(prop, (list, tuple)) else prop
        if not title:
            return None
        if ":" in title:
            return title.partition(":")[2].strip()
        return title

    def on_termprop_changed(self, terminal, prop_name):
        if prop_name == "xterm.title":
            terminal_active = self.get_current_terminal()
            if terminal_active:
                cwd = self.get_cwd(terminal_active)
                if cwd:
                    self.send_cwd_to_explorer(cwd)

    def send_cwd_to_explorer(self, cwd):
        bus.publish("sent_cwd", cwd)

    def paste_command(self, command):
        terminal = self.get_current_terminal()
        if command and terminal:
            terminal.feed_child(command.encode("utf-8"))
            terminal.grab_focus()

    def execute_command(self, command):
        terminal = self.get_current_terminal()
        if command and terminal:
            if not command.endswith("\n"):
                command += "\n"
            terminal.feed_child(command.encode("utf-8"))
            terminal.grab_focus()

    def on_button_press(self, terminal, event):
        if event.button == 3:
            self.show_context_menu(terminal, event)
            return True
        return False

    def show_context_menu(self, terminal, event):
        menu = Gtk.Menu()
        items = [
            ("Copiar", lambda i, t: self.actions.copy()),
            ("Pegar", lambda i, t: self.actions.paste()),
            ("Seleccionar todo", self.on_select_all),
            (None, None),
            ("Limpiar terminal", self.on_clear_screen),
            ("Reiniciar terminal", self.on_reset_term),
            ("Interrumpir proceso", self.on_menu_kill_process),
            ("Suspender proceso", self.on_suspended_process),
            ("Cerrar terminal", lambda i, t: self.actions.close_active_split()),
            (None, None),
            ("Dividir verticalmente", lambda i, t: self.actions.split_vertical()),
            ("Dividir horizontalmente", lambda i, t: self.actions.split_horizontal()),
            (None, None),
            ("Ejecutar selección", self.on_menu_execute_selection),
        ]

        for label, callback in items:
            if label is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            item = Gtk.MenuItem(label=label)
            item.connect("activate", callback, terminal)
            menu.append(item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def on_select_all(self, item, terminal):
        terminal.select_all()

    def on_menu_kill_process(self, item, terminal):
        terminal.feed_child(b"\x03")
        terminal.grab_focus()

    def apply_terminal_config(self, term):
        font_family = config_manager.get("appearance", "font_family") or "Monospace"
        font_size = config_manager.get("appearance", "font_size") or 11
        term.set_font(Pango.FontDescription.from_string(f"{font_family} {font_size}"))

        term.set_cursor_shape(config_manager.get_cursor_shape_vte())
        blink = config_manager.get("appearance", "cursor_blink")
        term.set_cursor_blink_mode(
            Vte.CursorBlinkMode.ON if blink is not False else Vte.CursorBlinkMode.OFF
        )

        scrollback = config_manager.get("terminal", "scrollback_lines") or 5000
        term.set_scrollback_lines(scrollback)

        scroll_on_key = config_manager.get("terminal", "scroll_on_keystroke")
        term.set_scroll_on_keystroke(
            bool(scroll_on_key) if scroll_on_key is not None else True
        )

        scroll_on_out = config_manager.get("terminal", "scroll_on_output")
        term.set_scroll_on_output(
            bool(scroll_on_out) if scroll_on_out is not None else False
        )
        bell = config_manager.get("terminal", "audible_bell")
        term.set_audible_bell(bool(bell) if bell is not None else False)

        palette_data = config_manager.get_terminal_colors()

        if palette_data:
            colors = []
            key_palette = (
                "palette_colors" if "palette_colors" in palette_data else "palette"
            )

            for hex_str in palette_data[key_palette]:
                rgba = Gdk.RGBA()
                rgba.parse(hex_str)
                colors.append(rgba)

            fg_rgba = Gdk.RGBA()
            fg_rgba.parse(palette_data["foreground"])

            bg_rgba = Gdk.RGBA()
            bg_rgba.parse(palette_data["background"])

            term.set_colors(fg_rgba, bg_rgba, colors)

            if "cursor" in palette_data:
                cur_rgba = Gdk.RGBA()
                cur_rgba.parse(palette_data["cursor"])
                term.set_color_cursor(cur_rgba)

    def create_vte_terminal(self, path=None, shell_path=None):
        term = Vte.Terminal()
        self.apply_terminal_config(term)

        term.connect("termprop-changed", self.on_termprop_changed)
        term.connect("cursor-moved", self.on_cursor_moved)
        term.connect("key-press-event", self.on_key_press)
        term.connect("button-press-event", self.on_button_press)
        term.connect("child-exited", lambda t, status: self.kill_term(t))

        path = path or os.getcwd()

        if not shell_path:
            shell_path = config_manager.get("terminal", "shell_path") or "/bin/zsh"

        if not os.path.exists(shell_path):
            shell_path = "/bin/bash"

        term.spawn_async(
            Vte.PtyFlags.DEFAULT,
            path,
            [shell_path],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            self.on_terminal_spawned,
        )
        term.shell = shell_path
        bus.publish("on_shell_changed", term.shell)

        return term

    def _on_global_config_changed(self, emitter, section, key):
        all_terminals = []
        self._get_all_terminals_recursive(self.parent, all_terminals)

        for term in all_terminals:
            if section == "appearance":
                if key in ["font_size", "font_family"]:
                    font_family = (
                        config_manager.get("appearance", "font_family") or "Monospace"
                    )
                    font_size = config_manager.get("appearance", "font_size") or 11
                    term.set_font(
                        Pango.FontDescription.from_string(f"{font_family} {font_size}")
                    )

                elif key == "cursor_blink":
                    blink = config_manager.get("appearance", "cursor_blink")
                    term.set_cursor_blink_mode(
                        Vte.CursorBlinkMode.ON
                        if blink is not False
                        else Vte.CursorBlinkMode.OFF
                    )

                elif key == "cursor_shape":
                    term.set_cursor_shape(config_manager.get_cursor_shape_vte())

                elif key == "terminal_palette" or key == "__all__":
                    self.apply_terminal_config(term)

            elif section == "terminal":
                if key == "scrollback_lines":
                    scrollback = (
                        config_manager.get("terminal", "scrollback_lines") or 5000
                    )
                    term.set_scrollback_lines(scrollback)

                elif key == "scroll_on_keystroke":
                    scroll_on_key = config_manager.get(
                        "terminal", "scroll_on_keystroke"
                    )
                    term.set_scroll_on_keystroke(bool(scroll_on_key))

                elif key == "scroll_on_output":
                    scroll_on_out = config_manager.get("terminal", "scroll_on_output")
                    term.set_scroll_on_output(bool(scroll_on_out))

                elif key == "audible_bell":
                    bell = config_manager.get("terminal", "audible_bell")
                    term.set_audible_bell(bool(bell))

            elif section == "RESET" or key == "__all__":
                self.apply_terminal_config(term)

    def on_terminal_spawned(self, terminal, pid, error):
        if error:
            print(f"ERROR Al crear terminal: {error}")
            return
        terminal._pid = pid
        terminal.tracker = TerminalTracker(terminal)

    def split_terminal(self, current_term, orientation, paned_position):
        parent = current_term.get_parent()
        paned = Gtk.Paned(orientation=orientation)
        new_term = self.create_vte_terminal()

        if isinstance(parent, Gtk.Notebook):
            page_num = parent.page_num(current_term)
            tab_label = parent.get_tab_label(current_term)

            parent.remove_page(page_num)
            paned.pack1(current_term, resize=True, shrink=False)
            paned.pack2(new_term, resize=True, shrink=False)

            paned.set_position(paned_position)
            parent.insert_page(paned, tab_label, page_num)
        else:
            if parent.get_child1() == current_term:
                parent.remove(current_term)
                paned.pack1(current_term, resize=True, shrink=False)
                paned.pack2(new_term, resize=True, shrink=False)
                paned.set_position(paned_position)
                parent.add1(paned)
            else:
                parent.remove(current_term)
                paned.pack1(current_term, resize=True, shrink=False)
                paned.pack2(new_term, resize=True, shrink=False)
                paned.set_position(paned_position)
                parent.add2(paned)

        parent.show_all()
        new_term.grab_focus()

    def on_menu_execute_selection(self, item, terminal):
        if terminal.get_has_selection():
            text = terminal.get_text_selected(Vte.Format.TEXT)
            if text:
                command = text.strip() + "\n"
                terminal.feed_child(command.encode("utf-8"))

    def kill_terminal_pid(self, terminal):
        pid = getattr(terminal, "_pid", -1)
        if pid > 0:
            try:
                os.kill(pid, signal.SIGHUP)
            except ProcessLookupError:
                pass

    def kill_term(self, terminal):
        parent = terminal.get_parent()
        self.kill_terminal_pid(terminal)
        if isinstance(parent, Gtk.Notebook):
            page_num = parent.page_num(terminal)
            if page_num != -1:
                parent.remove_page(page_num)
            return

        if isinstance(parent, Gtk.Paned):
            sibling = (
                parent.get_child2()
                if parent.get_child1() == terminal
                else parent.get_child1()
            )

            grandparent = parent.get_parent()
            if not sibling or not grandparent:
                return
            parent.remove(sibling)

            if isinstance(grandparent, Gtk.Notebook):
                page_num = grandparent.page_num(parent)
                tab_label = grandparent.get_tab_label(parent)
                grandparent.remove_page(page_num)
                grandparent.insert_page(sibling, tab_label, page_num)
            elif isinstance(grandparent, Gtk.Paned):
                if grandparent.get_child1() == parent:
                    grandparent.remove(parent)
                    grandparent.pack1(sibling, resize=True, shrink=False)
                else:
                    grandparent.remove(parent)
                    grandparent.pack2(sibling, resize=True, shrink=False)

            parent.destroy()
            self.show_all()
            sibling.grab_focus()

    def on_reset_term(self, item, term):
        term.feed_child(b"\x1bc")
        term.grab_focus()

    def on_clear_screen(self, item, term):
        term.feed_child(b"\x0c")
        term.grab_focus()

    def on_suspended_process(self, item, term):
        term.feed_child(b"\x1a")
        term.grab_focus()

    def _on_destroy(self, widget):
        if hasattr(self, "config_handler_id"):
            config_manager.disconnect(self.config_handler_id)

    def _on_footer_request_shell_change(self, shell_path):
        terminal = self.get_current_terminal()
        if not terminal:
            return
        terminal.shell = shell_path

        proc_name = self._get_active_process_name(terminal)

        if proc_name in ["python", "python3", "ipython"]:
            cmd_mutation = f'import os; os.execl("{shell_path}", "{shell_path}")\n'
            terminal.feed_child(cmd_mutation.encode("utf-8"))
        else:
            terminal.feed_child(f"exec {shell_path}\n".encode("utf-8"))

    def _get_active_process_name(self, terminal):
        try:
            pid = getattr(terminal, "_pid", -1)
            if pid <= 0:
                pid = terminal.get_property("child-pid")

            if pid <= 0:
                return None

            children_path = f"/proc/{pid}/task/{pid}/children"
            if os.path.exists(children_path):
                with open(children_path, "r") as f:
                    child_pids = f.read().split()

                if child_pids:
                    active_pid = child_pids[-1]
                    with open(f"/proc/{active_pid}/cmdline", "r") as f:
                        cmdline = f.read().split("\x00")
                        if cmdline and cmdline[0]:
                            return os.path.basename(cmdline[0])

            with open(f"/proc/{pid}/cmdline", "r") as f:
                cmdline = f.read().split("\x00")
                if cmdline and cmdline[0]:
                    return os.path.basename(cmdline[0])
        except Exception as e:
            print(f"Error detectando proceso activo: {e}")
        return None

    def _on_footer_request_zoom(self, direction):
        current_term = self.get_current_terminal()
        if not current_term:
            return

        current_font = current_term.get_font()
        font_name = current_font.get_family()
        current_size = current_font.get_size() / Pango.SCALE

        if direction == "in" and current_size < 30:
            current_size += 1
        elif direction == "out" and current_size > 6:
            current_size -= 1

        current_term.set_font(
            Pango.FontDescription.from_string(f"{font_name} {int(current_size)}")
        )


class TerminalTracker:
    def __init__(self, terminal):
        self.terminal = terminal
        self.last_status = "idle"
        self.active_process = None

        self.root_pid = getattr(terminal, "_pid", -1)
        if self.root_pid <= 0:
            self.root_pid = terminal.get_property("child-pid")

        self.terminal.connect("contents-changed", self._on_contents_changed)

        GLib.timeout_add(100, self._process_polling_loop)
        GLib.timeout_add(50, lambda: self._inject_shell_hooks() or False)

    def _inject_shell_hooks(self):
        # \033[8m  -> Activa el color INVISIBLE
        # \033[0m  -> Restaura el modo NORMAL

        zsh_hook = (
            " fc -p\n"
            ' function __tracker_precmd() { printf "\\033[8m__STATUS__%d\\033[0m\\n" $?; }\n;'
            " typeset -ag precmd_functions;"
            " if [[ ${precmd_functions[(r)__tracker_precmd]} != __tracker_precmd ]]; then"
            "   precmd_functions+=(__tracker_precmd);"
            " fi\n"
            " fc -P\n"
            " clear\n"
        )

        bash_hook = (
            " set +o history\n"
            ' if [ -z "$PROMPT_COMMAND" ]; then '
            "PROMPT_COMMAND=\"printf '\\033[8m__STATUS__%d\\033[0m\\n' \$?\"; "
            "else "
            "PROMPT_COMMAND=\"printf '\\033[8m__STATUS__%d\\033[0m' \$?; $PROMPT_COMMAND\"; "
            "fi\n"
            " set -o history\n"
            " clear\n"
        )

        if self.terminal.shell == "/bin/zsh":
            self.terminal.feed_child(zsh_hook.encode())
        elif self.terminal.shell == "/bin/bash":
            self.terminal.feed_child(bash_hook.encode())
        return False

    def _get_active_subprocess(self):
        if self.root_pid <= 0:
            return None
        try:
            children_path = f"/proc/{self.root_pid}/task/{self.root_pid}/children"
            if os.path.exists(children_path):
                with open(children_path, "r") as f:
                    child_pids = f.read().split()

                if child_pids:
                    active_pid = child_pids[-1]
                    with open(f"/proc/{active_pid}/cmdline", "r") as f:
                        cmdline = f.read().split("\x00")
                        if cmdline and cmdline[0]:
                            return os.path.basename(cmdline[0])
        except Exception:
            pass
        return None

    def _process_polling_loop(self):
        try:
            if not self.terminal or not self.terminal.get_realized():
                return False
            current_child = self._get_active_subprocess()
        except RuntimeError:
            return False

        if current_child and self.last_status == "idle":
            self.last_status = "running"
            self.active_process = current_child
            bus.publish("terminal_process_status", ["running", self.active_process])

        elif not current_child and self.last_status == "running":
            self.last_status = "idle"
            self.active_process = None

        return True

    def _on_contents_changed(self, terminal):
        col, row = terminal.get_cursor_position()
        if row < 1:
            return

        text, _ = terminal.get_text_range_format(
            Vte.Format.TEXT, row - 3, 0, row + 1, terminal.get_column_count()
        )

        match = re.search(r"__STATUS__(\d+)", text)
        if match:
            exit_code = int(match.group(1))

            if exit_code == 0:
                bus.publish("terminal_process_status", ["success", exit_code])
            else:
                bus.publish(
                    "terminal_process_status",
                    ["failed", exit_code],
                )
