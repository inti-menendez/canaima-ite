from gi.repository import Gtk
from .ia_settings_window import IASettingsWindow

WELCOME_CSS = """
.welcome-page {
    background-color: #141414;
}
.welcome-page viewport {
    background-color: #141414;
    border: none;
}
"""


class WelcomeTab(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.ia_setting_window = None

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(WELCOME_CSS.encode())
        self.get_style_context().add_provider(
            style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.get_style_context().add_class("welcome-page")

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_top(40)
        main_box.set_margin_bottom(40)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        self.add(main_box)

        title_label = Gtk.Label()
        title_label.set_markup(
            "<span size='xx-large' weight='bold' foreground='#ffffff'>Canaima ITE</span>"
        )
        title_label.set_xalign(0)
        main_box.pack_start(title_label, False, True, 0)

        subtitle_label = Gtk.Label()
        subtitle_label.set_markup(
            "<span color='#a9b1d6'>Entorno Integrado de Terminal con Asistencia Pedagógica</span>"
        )
        subtitle_label.set_xalign(0)
        main_box.pack_start(subtitle_label, False, True, 0)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(separator, False, True, 10)

        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(columns_box, True, True, 0)

        col1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        columns_box.pack_start(col1_box, True, True, 0)

        ollama_title = Gtk.Label()
        ollama_title.set_markup(
            "<span size='large' weight='bold' color='#0b6793'>1. Configuración de Ollama</span>"
        )
        ollama_title.set_xalign(0)
        col1_box.pack_start(ollama_title, False, False, 0)

        ollama_text = Gtk.Label()
        ollama_text.set_markup(
            "Para trabajar de forma local, instale Ollama:\n"
            "<span font_family='monospace' background='#191919' foreground='#00ff66'> curl -fsSL https://ollama.com/install.sh | sh </span>\n\n"
            "Luego, descargue e inicialice el modelo base:\n"
            "<span font_family='monospace' background='#191919' foreground='#00ff66'> ollama run qwen2.5:0.5b </span>"
        )
        ollama_text.set_xalign(0)
        ollama_text.set_line_wrap(True)
        ollama_text.set_max_width_chars(10)
        col1_box.pack_start(ollama_text, False, False, 0)

        api_title = Gtk.Label()
        api_title.set_markup(
            "<span size='large' weight='bold' color='#0b6793'>2. Proveedores Cloud (Opcional)</span>"
        )
        api_title.set_xalign(0)
        col1_box.pack_start(api_title, False, False, 10)

        api_text = Gtk.Label()
        api_text.set_markup(
            "Si prefiere usar servicios en la nube, la aplicación soporta:\n"
            "• <b>OpenRouter:</b> Acceso a múltiples modelos abiertos.\n"
            "• <b>Groq:</b> Inferencia de alta velocidad.\n"
            "• <b>Cerebras:</b> Procesamiento de baja latencia.\n\n"
            "Configure las credenciales abriendo los <a href='settings://open'>ajustes de IA aquí</a>."
        )
        api_text.set_xalign(0)
        api_text.set_line_wrap(True)
        api_text.set_selectable(True)
        api_text.set_track_visited_links(False)
        api_text.set_max_width_chars(10)
        api_text.connect("activate-link", self._on_link_clicked)
        col1_box.pack_start(api_text, False, False, 0)

        col2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        columns_box.pack_start(col2_box, True, True, 0)

        cmd_title = Gtk.Label()
        cmd_title.set_markup(
            "<span size='large' weight='bold' color='#0b6793'>3. Flujo de Trabajo y Atajos</span>"
        )
        cmd_title.set_xalign(0)
        col2_box.pack_start(cmd_title, False, False, 0)

        cmd_text = Gtk.Label()
        cmd_text.set_markup(
            "Optimice el uso de las pestañas mediante las siguientes acciones:\n"
            "• <b>Doble clic en espacio libre:</b> Abre una nueva terminal.\n"
            "• <b>Doble clic en pestaña:</b> Cambiar nombre actual.\n"
            "• <b>Clic derecho en pestaña:</b> Menú de cierre rápido.\n\n"
        )
        cmd_text.set_xalign(0)
        cmd_text.set_line_wrap(True)
        cmd_text.set_max_width_chars(10)
        col2_box.pack_start(cmd_text, False, False, 0)

        doc_title = Gtk.Label()
        doc_title.set_markup(
            "<span size='large' weight='bold' color='#0b6793'>4. Documentación del Proyecto</span>"
        )
        doc_title.set_xalign(0)
        col2_box.pack_start(doc_title, False, False, 10)

        doc_text = Gtk.Label()
        doc_text.set_markup(
            "Para consultar los manuales de usuario, guías de desarrollo y opciones avanzadas de compilación, visite el sitio oficial:"
        )
        doc_text.set_xalign(0)
        doc_text.set_line_wrap(True)
        doc_text.set_max_width_chars(10)
        col2_box.pack_start(doc_text, False, False, 0)

        link_button = Gtk.LinkButton.new_with_label(
            uri="https://inti-menendez.github.io/canaima-ite/",
            label="Visitar documentación en GitHub Pages",
        )
        link_button.set_halign(Gtk.Align.START)
        col2_box.pack_start(link_button, False, False, 5)

        self.show_all()

    def _on_link_clicked(self, label, uri):
        if uri == "settings://open":
            self.open_settings()
            return True
        return False

    def open_settings(self):
        if self.ia_setting_window is None or not self.ia_setting_window.get_visible():
            from core.ia_client import client

            self.ia_setting_window = IASettingsWindow(
                callback_on_save=lambda: client.reload()
            )
        else:
            self.ia_setting_window.present()
