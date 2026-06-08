from gi.repository import Gtk, GLib, Gdk
from core.keybindings_engine import registry
from core.event_bus import bus
from .ia_settings_window import IASettingsWindow
from core.ia_client import client

import os
import threading
import html
import re


def format_text_to_pango(text):
    text = html.escape(text)

    text = re.sub(r"`(.*?)`", r'<tt><span foreground="#0b6793">\1</span></tt>', text)

    labels = [
        "comando:",
        "flags:",
        "ejemplo",
        "estructura",
        "Estructura",
        "casos de uso",
    ]
    for label in labels:
        text = text.replace(label, f'<b><span foreground="#9ae1ff">{label}</span></b>')

    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    text = re.sub(r"^\s*[\*\-]\s+", r" • ", text, flags=re.MULTILINE)

    return text


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "..", "assets", "canaima-logo.png")

CHAT_CSS = f"""
.chatbot{{
    background-color:#191919;
}}
.header-actionbar {{
    background-color: transparent;
}}
.chat-viewport {{ 
    background-color: transparent; 
    background-image: url('file://{LOGO_PATH}');
    background-size: 200px;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0.9;
}}
.welcome-floating {{ 
    margin-top: 80px; 
}}
.welcome-text {{
    font-size: 18px;
    font-weight: bold;
    color: #565f89;
}}
.chat-list {{ 
    background-color: transparent; 
}}
.chat-bubble {{
    border-radius: 10px;
    padding: 10px 14px;
}}
.msg-ai {{
    background-color: #1f232a;
    color: #a9b1d6;
    border: 1px solid #292e42;
    font-family: sans-serif;
}}
.msg-user {{
    background-color: #0b6793;
    color: #ffffff;
    border: 1px solid #0f7fa3;
}}
.msg-ui {{
    background-color: #1a233a;
    color: #7aa2f7;
    border: 1px solid #243354;
}}
.chat-entry {{
    border-radius: 6px;
    border: 1px solid #292e42;
    background-color: #1f232a;
    color: #a9b1d6;
    padding: 6px 10px;
}}
.chat-entry:focus {{
    border-color: #0b6793;
}}
.send-btn {{
    margin-left: 6px;
}}
.msg-error {{
    background-color: #3d1a1a; 
    color: #ff9494;
    border: 1px solid #722f2f;
}}
.msg-warning {{
    background-color: #332b00;
    color: #ffeb94;
    border: 1px solid #5c4d00;
}}
.mode-indicator-label {{
    color: #565f89;
    font-size: 11px;
    font-weight: bold;
}}
"""


class SideChatbot(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("chatbot")
        self.stop_event = threading.Event()
        self.is_responding = False
        self.current_ai_buffer = ""
        self.ia_setting_window = None

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CHAT_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.NONE)
        self.scroll.get_style_context().add_class("chat-viewport")

        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.list_box.get_style_context().add_class("chat-list")
        self.list_box.set_margin_top(10)
        self.scroll.add(self.list_box)

        self.welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.welcome_box.get_style_context().add_class("welcome-floating")
        self.welcome_box.set_valign(Gtk.Align.CENTER)
        self.welcome_box.set_halign(Gtk.Align.CENTER)

        self.welcome_label = Gtk.Label()
        self.welcome_label.get_style_context().add_class("welcome-text")
        self.welcome_label.set_markup("¿Qué hay pa' hoy mano?")
        self.welcome_box.pack_start(self.welcome_label, True, True, 0)
        self.list_box.pack_start(self.welcome_box, True, True, 0)

        header_box = Gtk.ActionBar()
        header_box.get_style_context().add_class("header-actionbar")

        self.new_chat_btn = Gtk.Button.new_from_icon_name(
            "document-new-symbolic", Gtk.IconSize.MENU
        )
        self.new_chat_btn.set_tooltip_text("Nueva conversación")
        self.new_chat_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.new_chat_btn.connect("clicked", self._on_new_chat_clicked)
        header_box.pack_start(self.new_chat_btn)

        self.copy_all_btn = Gtk.Button.new_from_icon_name(
            "edit-copy-symbolic", Gtk.IconSize.MENU
        )
        self.copy_all_btn.set_tooltip_text("Copiar conversación")
        self.copy_all_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.copy_all_btn.connect("clicked", self._on_copy_all_clicked)
        header_box.pack_start(self.copy_all_btn)

        self.mode_button = Gtk.Button()
        self.mode_button.set_relief(Gtk.ReliefStyle.NONE)
        self.mode_button.set_tooltip_text("Cambiar entre modo Local y Nube")
        self.mode_button.connect("clicked", self._on_mode_button_clicked)

        self.mode_button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6
        )
        self.local_icon = Gtk.Image.new_from_icon_name(
            "drive-harddisk-symbolic", Gtk.IconSize.MENU
        )
        self.cloud_icon = Gtk.Image.new_from_icon_name(
            "network-workgroup-symbolic", Gtk.IconSize.MENU
        )
        self.mode_label = Gtk.Label()
        self.mode_label.get_style_context().add_class("mode-indicator-label")

        self.mode_button_box.pack_start(self.local_icon, False, False, 0)
        self.mode_button_box.pack_start(self.cloud_icon, False, False, 0)
        self.mode_button_box.pack_start(self.mode_label, False, False, 0)
        self.mode_button.add(self.mode_button_box)

        header_box.set_center_widget(self.mode_button)

        self.settings_btn = Gtk.Button.new_from_icon_name(
            "emblem-system-symbolic", Gtk.IconSize.MENU
        )
        self.settings_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.settings_btn.set_tooltip_text("Configuración de IA")
        self.settings_btn.connect("clicked", self.open_settings)
        header_box.pack_end(self.settings_btn)

        input_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        input_container.set_margin_start(12)
        input_container.set_margin_end(12)
        input_container.set_margin_bottom(12)
        input_container.set_margin_top(4)

        self.entry = Gtk.Entry()
        self.entry.get_style_context().add_class("chat-entry")
        self.entry.set_placeholder_text("Pregúntale algo a la IA...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self._on_send)

        self.action_btn = Gtk.Button.new_from_icon_name(
            "mail-send-symbolic", Gtk.IconSize.MENU
        )
        self.action_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.action_btn.get_style_context().add_class("send-btn")
        self.action_btn.connect("clicked", self._on_action_clicked)

        input_container.pack_start(self.entry, True, True, 0)
        input_container.pack_start(self.action_btn, False, False, 0)

        self.pack_start(header_box, False, False, 0)
        self.pack_start(self.scroll, True, True, 0)
        self.pack_end(input_container, False, False, 0)

        self.show_all()
        GLib.idle_add(lambda: (self._check_initial_setup(), False)[1])

        registry.register_command("ask_chatbot", self.focus_chatbot, self)
        bus.subscribe("sent_terminal_prompt", self._on_received_terminal_prompt)

        self._update_mode_ui()

    def _on_mode_button_clicked(self, button):
        if hasattr(self, "_changing_mode") and self._changing_mode:
            return

        self._changing_mode = True
        current_is_local = self.mode_label.get_text() == "LOCAL"
        new_is_local = not current_is_local

        from core.app_storage import storage

        storage.set_preference(
            "IA_component", "provider", "local" if new_is_local else "cloud"
        )

        self.reload_client()
        self._update_mode_ui()
        self._check_initial_setup()
        self._changing_mode = False

    def _update_mode_ui(self):
        is_local = client.conf.get("provider", "cloud") == "local"

        if is_local:
            self.local_icon.set_opacity(1.0)
            self.cloud_icon.set_opacity(0.2)
            self.mode_label.set_text("LOCAL")
            self.mode_button.set_tooltip_text(
                "Modo Local (Ollama) - Click para cambiar a Nube"
            )
        else:
            self.local_icon.set_opacity(0.2)
            self.cloud_icon.set_opacity(1.0)
            self.mode_label.set_text("NUBE")
            self.mode_button.set_tooltip_text(
                "Modo Nube (API) - Click para cambiar a Local"
            )

        info = client.get_current_model_info()
        bus.publish("ia_model_changed", info.get("model", "Desconocido"))

    def reload_client(self):
        client.reload()
        self.current_ai_buffer = ""

        children = self.list_box.get_children()
        if children:
            last_child = children[-1]
            if hasattr(last_child, "get_children"):
                try:
                    label = last_child.get_children()[0].get_children()[0]
                    if label.get_text() == "Analizando tu consulta...":
                        self.list_box.remove(last_child)
                except Exception:
                    pass

        if self.is_responding:
            self.stop_event.set()
            self._set_ui_responding(False)

    def _set_ui_responding(self, responding, was_cancelled=False):
        self.is_responding = responding
        image = self.action_btn.get_image()

        if responding:
            image.set_from_icon_name("process-stop-symbolic", Gtk.IconSize.MENU)
            self.action_btn.set_tooltip_text("Detener respuesta")
        else:
            image.set_from_icon_name("mail-send-symbolic", Gtk.IconSize.MENU)
            self.action_btn.set_tooltip_text("Enviar mensaje")

            if was_cancelled:
                children = self.list_box.get_children()
                if children:
                    last_bubble = children[-1]
                    try:
                        event_box = last_bubble.get_children()[0]
                        label = event_box.get_child()

                        if label.get_text() == "Analizando tu consulta...":
                            label.set_text("")

                        event_box.get_style_context().add_class("msg-warning")
                        formatted_text = format_text_to_pango(self.current_ai_buffer)
                        separator = "\n\n" if self.current_ai_buffer else ""

                        label.set_markup(
                            f"{formatted_text}{separator}<i>---Respuesta detenida por el usuario.---</i>"
                        )
                        self._scroll_to_bottom()
                    except Exception as e:
                        print(f"Error al estampar mensaje de detenido: {e}")

        return False

    def _on_action_clicked(self, btn):
        if self.is_responding:
            self.stop_event.set()
        else:
            self._on_send(self.entry)

    def _on_send(self, entry):
        texto = entry.get_text().strip()
        if not texto or self.is_responding:
            return

        if self.welcome_box.get_parent() == self.list_box:
            self.list_box.remove(self.welcome_box)

        self.list_box.pack_start(self.chat_bubble(texto, is_ai=False), False, False, 0)
        entry.set_text("")
        if not self._check_initial_setup():
            GLib.idle_add(self._set_ui_responding, False)
            return
        bubble = self.chat_bubble("Analizando tu consulta...", is_ai=True)
        self.list_box.pack_start(bubble, False, False, 0)

        self.stop_event.clear()
        self._set_ui_responding(True)

        bus.publish("ia_state_changed", "thinking")

        thread = threading.Thread(target=self.print_ai_response, args=(texto,))
        thread.daemon = True
        thread.start()

        self.current_ai_buffer = ""
        self._scroll_to_bottom()

    def print_ai_response(self, user_message):
        try:
            stream = client.get_ai_response(user_message, stop_event=self.stop_event)
            for chunk in stream:
                if self.stop_event.is_set():
                    break
                GLib.idle_add(self.update_ui_with_chunk, chunk)
        except Exception as e:
            GLib.idle_add(
                self.update_ui_with_chunk, {"status": "error", "content": str(e)}
            )
        finally:
            was_cancelled = self.stop_event.is_set()
            if was_cancelled:
                bus.publish("ia_state_changed", "stopped")
            else:
                bus.publish("ia_state_changed", "reposo")
            GLib.idle_add(self._set_ui_responding, False, was_cancelled)

    def update_ui_with_chunk(self, chunk_data):
        status = chunk_data.get("status")
        content = chunk_data.get("content", "")

        last_bubble = self.list_box.get_children()[-1]
        event_box = last_bubble.get_children()[0]
        label = event_box.get_child()

        if label.get_text() == "Analizando tu consulta...":
            label.set_text("")

        if status == "error":
            event_box.get_style_context().add_class("msg-error")
            label.set_markup(f"<b>Error:</b> {content}")
            return False

        self.current_ai_buffer += content
        formatted_text = format_text_to_pango(self.current_ai_buffer)
        label.set_markup(formatted_text)

        self._scroll_to_bottom()
        return False

    def chat_bubble(self, text, is_ai=False, is_ui=False):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_margin_start(6)
        container.set_margin_end(6)
        container.set_margin_bottom(8)

        bubble_eb = Gtk.EventBox()
        bubble_eb.get_style_context().add_class("chat-bubble")

        label = Gtk.Label()
        label.set_selectable(True)
        label.set_use_markup(True)
        label.set_markup(text)
        label.set_line_wrap(True)
        label.set_max_width_chars(42)
        label.set_xalign(0)
        label.set_margin_start(12)
        label.set_margin_end(12)
        label.set_margin_top(8)
        label.set_margin_bottom(8)
        label.connect("activate-link", self._on_link_clicked)

        bubble_eb.add(label)

        if is_ai:
            container.set_halign(Gtk.Align.START)
            bubble_eb.get_style_context().add_class("msg-ai")
        elif is_ui:
            container.set_halign(Gtk.Align.FILL)
            bubble_eb.get_style_context().add_class("msg-ui")
        else:
            container.set_halign(Gtk.Align.END)
            bubble_eb.get_style_context().add_class("msg-user")

        container.pack_start(bubble_eb, False, False, 0)
        container.show_all()
        return container

    def _scroll_to_bottom(self):
        adj = self.scroll.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper()))

    def focus_chatbot(self):
        bus.publish("request_terminal_prompt", "necesito datos mano")
        self.entry.grab_focus()

    def _on_received_terminal_prompt(self, data):
        self.entry.set_text(data)

    def open_settings(self, btn):
        if self.ia_setting_window is None or not self.ia_setting_window.get_visible():
            self.ia_setting_window = IASettingsWindow(
                callback_on_save=self.reload_client
            )
        else:
            self.ia_setting_window.present()

    def set_ui_content(self, text):
        if self.welcome_box.get_parent() == self.list_box:
            self.list_box.remove(self.welcome_box)
        bubble = self.chat_bubble(text, is_ui=True)
        self.list_box.pack_start(bubble, False, False, 0)
        self._scroll_to_bottom()

    def _check_initial_setup(self):
        is_ok, diagnostic = client.check_health()

        if is_ok and not diagnostic:
            return True

        msg = "<b>¡Bienvenido al Entorno de Terminal Integrado de Canaima!</b>\n"
        msg += "Para comenzar a usar la IA, necesitamos ajustar unos detalles:\n\n"

        if "ollama_not_installed" in diagnostic:
            msg += "• <b>Ollama no está en el sistema:</b>\n"
            msg += "  <i>Instálalo con:</i> <tt>curl -fsSL https://ollama.com/install.sh | sh</tt>\n\n"

        elif "ollama_service_down" in diagnostic:
            msg += "• <b>El servicio de Ollama está apagado:</b>\n"
            msg += "  <i>Inícialo con:</i> <tt>systemctl start ollama</tt>\n\n"

        if "no_local_models" in diagnostic or "selected_model_not_found" in diagnostic:
            msg += "• <b>No tienes modelos locales:</b>\n"
            msg += "  Puedes descargar uno (ej: <tt>ollama pull [modelo]</tt>) o configurar la <a href='settings://open'>Nube aquí</a>.\n\n"
            msg += "  Para ver los modelos disponibles puedes visitar https://ollama.com/search.\n"

        if "missing_api_key" in diagnostic:
            msg += "• <b>Falta configuración de API:</b>\n"
            msg += "  Si prefieres usar la nube, añade tu api key en los <a href='settings://open'>ajustes</a>.\n"

        self.set_ui_content(msg)
        return is_ok

    def _on_link_clicked(self, label, uri):
        if uri == "settings://open":
            self.open_settings(None)
            return True
        return False

    def _on_new_chat_clicked(self, btn):
        for child in self.list_box.get_children():
            self.list_box.remove(child)
        self.list_box.pack_start(self.welcome_box, True, True, 0)
        self.list_box.show_all()
        self._check_initial_setup()

    def _on_copy_all_clicked(self, btn):
        full_text = ""
        for wrapper in self.list_box.get_children():
            if wrapper == self.welcome_box:
                continue
            try:
                eb = wrapper.get_children()[0]
                label = eb.get_children()[0]
                prefix = (
                    "AI: "
                    if "msg-ai" in eb.get_style_context().list_classes()
                    else "Tú: "
                )
                full_text += f"{prefix}{label.get_text()}\n\n"
            except Exception:
                continue
        if full_text:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(full_text, -1)

    def cleanup(self):
        if self.is_responding:
            print("[- ITE] Limpiando conexiones y deteniendo inferencia de IA...")
            self.stop_event.set()
            import time

            time.sleep(0.1)
            print("[- ITE] Procesos de IA liberados.")
