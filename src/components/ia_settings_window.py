from gi.repository import Gtk, Gdk, Pango
import ollama
import keyring
import keyring.errors
from core.app_storage import storage
from core.ia_model_manager import model_manager
from core.event_bus import bus

APP_ID = "canaima-ite"

SETTINGS_CSS = """
.settings-window {
    background-color: #191919;
}
.sidebar-box {
    background-color: #141414;
    border-right: 1px solid #1f232a;
    padding-top: 10px;
}
.sidebar-list {
    background-color: transparent;
}
.sidebar-row {
    padding: 10px 14px;
    border-radius: 6px;
    margin: 2px 8px;
    color: #fff;
    font-weight: 500;
}
.sidebar-row:selected {
    background-color: #0b6793;
    color: #ffffff;
}
.sidebar-row:hover:not(:selected) {
    background-color: #1f232a;
}
.content-area {
    background-color: #191919;
    padding: 24px;
}
.section-title {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 4px;
}
.dim-label {
    color: #fff;
    font-size: 14px;
}
.form-entry {
    border-radius: 6px;
    border: 1px solid #292e42;
    background-color: #1f232a;
    color: #fff;
    padding: 6px 10px;
}
.form-entry:focus {
    border-color: #0b6793;
}
.form-combo {
    border-radius: 6px;
    border: 1px solid #292e42;
    background-color: #1f232a;
    color: #fff;
}
.custom-notebook {
    background-color: transparent;
    border: 1px solid #292e42;
    border-radius: 6px;
}
.custom-notebook header {
    background-color: #141414;
    border-bottom: 1px solid #292e42;
}
.custom-notebook tab {
    padding: 6px 12px;
    color: #fff;
    font-weight: bold;
}
.custom-notebook tab:checked {
    color: #ffffff;
    border-bottom: 2px solid #0b6793;
}
.settings-footer {
    background-color: #141414;
    border-top: 1px solid #1f232a;
    padding: 12px 24px;
}
.save-btn {
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: bold;
}
.scrolled-list {
    background-color: #141414;
    border: 1px solid #292e42;
    border-radius: 6px;
}
.custom-provider-row {
    padding: 8px;
    border-bottom: 1px solid #1f232a;
}
.library-link {
    color: #0b6793;
    font-size: 16px;
}
"""


class IASettingsWindow(Gtk.Window):
    def __init__(self, callback_on_save=None):
        super().__init__(title="Configuración de Inteligencia Artificial")
        self.set_default_size(750, 520)
        self.set_border_width(0)
        self.set_resizable(False)
        self.get_style_context().add_class("settings-window")
        self.callback_on_save = callback_on_save

        self.config = storage.get_preference("IA_component") or {}

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(SETTINGS_CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(main_hbox)

        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.get_style_context().add_class("sidebar-box")
        sidebar_box.set_size_request(200, -1)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.get_style_context().add_class("sidebar-list")
        self.sidebar_list.connect("row-selected", self._on_sidebar_row_selected)
        sidebar_box.pack_start(self.sidebar_list, True, True, 0)

        main_hbox.pack_start(sidebar_box, False, False, 0)

        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.stack_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.stack_container.get_style_context().add_class("content-area")

        self.stack_container.set_size_request(550, -1)

        self.stack_container.pack_start(self.stack, True, True, 0)
        right_vbox.pack_start(self.stack_container, True, True, 0)

        footer = Gtk.ActionBar()
        footer.get_style_context().add_class("settings-footer")

        save_btn = Gtk.Button(label="Guardar Configuración")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.get_style_context().add_class("save-btn")
        save_btn.connect("clicked", self.save_settings)
        footer.pack_end(save_btn)
        right_vbox.pack_end(footer, False, False, 0)

        main_hbox.pack_start(right_vbox, True, True, 0)

        self.sidebar_map = {}

        self._init_local_page()
        self._init_cloud_page()
        self._init_system_page()
        self._init_custom_provider_page()

        self._refresh_custom_list_visual()

        first_row = self.sidebar_list.get_row_at_index(0)
        if first_row:
            self.sidebar_list.select_row(first_row)

        self.show_all()

    def _add_stack_page(self, widget, name, title):
        self.stack.add_named(widget, name)
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("sidebar-row")
        label = Gtk.Label(label=title, xalign=0)
        row.add(label)
        self.sidebar_list.add(row)
        self.sidebar_map[row] = name

    def _on_sidebar_row_selected(self, listbox, row):
        if row in self.sidebar_map:
            self.stack.set_visible_child_name(self.sidebar_map[row])

    def _init_local_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        title = Gtk.Label(label="Ollama (Modelos Locales)", xalign=0)
        title.get_style_context().add_class("section-title")
        vbox.pack_start(title, False, False, 0)

        self.local_model_combo = Gtk.ComboBoxText()
        self.local_model_combo.get_style_context().add_class("form-combo")
        self.refresh_local_models()

        hbox = Gtk.Box(spacing=10)
        hbox.pack_start(self.local_model_combo, True, True, 0)

        refresh_btn = Gtk.Button.new_from_icon_name(
            "view-refresh-symbolic", Gtk.IconSize.BUTTON
        )
        refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        refresh_btn.connect("clicked", lambda x: self.refresh_local_models())
        hbox.pack_start(refresh_btn, False, False, 0)

        lbl_sel = Gtk.Label(label="Modelo activo en el sistema:", xalign=0)
        lbl_sel.get_style_context().add_class("dim-label")
        vbox.pack_start(lbl_sel, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        vbox.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6
        )

        lbl_dl = Gtk.Label(
            label="Descargar nuevo modelo desde la biblioteca de Ollama:", xalign=0
        )
        lbl_dl.get_style_context().add_class("dim-label")
        vbox.pack_start(lbl_dl, False, False, 0)

        dl_hbox = Gtk.Box(spacing=10)
        self.dl_entry = Gtk.Entry()
        self.dl_entry.get_style_context().add_class("form-entry")
        self.dl_entry.set_placeholder_text("Ej: llama3, qwen2.5:1.5b...")

        dl_btn = Gtk.Button(label="Descargar")
        dl_btn.connect("clicked", self.download_model)
        dl_hbox.pack_start(self.dl_entry, True, True, 0)
        dl_hbox.pack_start(dl_btn, False, False, 0)
        vbox.pack_start(dl_hbox, False, False, 0)
        link_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        link_btn = Gtk.LinkButton.new_with_label(
            "https://ollama.com/library", "Explorar modelos disponibles en ollama.com"
        )
        link_btn.get_style_context().add_class("library-link")
        link_btn.set_halign(Gtk.Align.START)
        link_hbox.pack_start(link_btn, False, False, 0)
        vbox.pack_start(link_hbox, False, False, 0)

        self._add_stack_page(vbox, "local", "Local / Ollama")

    def _init_cloud_page(self):
        self.cloud_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self._refresh_cloud_content()
        self._add_stack_page(self.cloud_vbox, "cloud", "Nube / API")

    def _refresh_cloud_content(self):
        for child in self.cloud_vbox.get_children():
            self.cloud_vbox.remove(child)

        title = Gtk.Label(label="Proveedores en la Nube", xalign=0)
        title.get_style_context().add_class("section-title")
        self.cloud_vbox.pack_start(title, False, False, 0)

        failover_box = Gtk.Box(spacing=10)
        self.failover_switch = Gtk.Switch(active=self.config.get("failover", False))
        self.failover_switch.set_valign(Gtk.Align.CENTER)

        lbl_failover = Gtk.Label(
            label="Respaldo inteligente (Failover local si la API falla)", xalign=0
        )
        lbl_failover.get_style_context().add_class("dim-label")
        failover_box.pack_start(lbl_failover, True, True, 0)
        failover_box.pack_end(self.failover_switch, False, False, 0)
        self.cloud_vbox.pack_start(failover_box, False, False, 0)

        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("custom-notebook")

        self.notebook.set_scrollable(True)
        self.notebook.set_show_border(True)

        self.provider_widgets = {}

        for p_id, cfg in model_manager.PROVIDERS.items():
            page = self._create_provider_page(p_id, cfg["name"], is_custom=False)
            self.notebook.append_page(page, Gtk.Label(label=cfg["name"]))

        customs = self.config.get("custom_providers", {})
        for p_id, data in customs.items():
            page = self._create_provider_page(p_id, data["name"], is_custom=True)
            self.notebook.append_page(page, Gtk.Label(label=data["name"]))

        self.cloud_vbox.pack_start(self.notebook, True, True, 0)

        default_box = Gtk.Box(spacing=12)
        self.default_provider_combo = Gtk.ComboBoxText()
        self.default_provider_combo.get_style_context().add_class("form-combo")

        for p_id, cfg in model_manager.PROVIDERS.items():
            self.default_provider_combo.append(p_id, cfg["name"])
        for p_id, data in customs.items():
            self.default_provider_combo.append(p_id, data["name"])

        self.default_provider_combo.set_active_id(
            self.config.get("default_provider", "openrouter")
        )

        lbl_priority = Gtk.Label(label="Proveedor prioritario:", xalign=0)
        lbl_priority.get_style_context().add_class("dim-label")
        default_box.pack_start(lbl_priority, False, False, 0)
        default_box.pack_start(self.default_provider_combo, True, True, 0)
        self.cloud_vbox.pack_start(default_box, False, False, 0)
        self.cloud_vbox.show_all()

    def _init_system_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        title = Gtk.Label(label="Comportamiento del Sistema (System Prompt)", xalign=0)
        title.get_style_context().add_class("section-title")
        vbox.pack_start(title, False, False, 0)

        desc = Gtk.Label(
            label="Modifica el rol base de las respuestas dadas por la IA:", xalign=0
        )
        desc.get_style_context().add_class("dim-label")
        vbox.pack_start(desc, False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.get_style_context().add_class("scrolled-list")

        self.system_prompt_buffer = Gtk.TextBuffer()
        self.system_prompt_buffer.set_text(self.config.get("user_system_prompt", ""))

        textview = Gtk.TextView(buffer=self.system_prompt_buffer)
        textview.get_style_context().add_class("form-entry")
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        textview.set_left_margin(8)
        textview.set_right_margin(8)
        textview.set_top_margin(8)
        textview.set_bottom_margin(8)
        sw.add(textview)

        vbox.pack_start(sw, True, True, 0)
        self._add_stack_page(vbox, "system", "Personalización")

    def _init_custom_provider_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        title = Gtk.Label(
            label="Endpoints Personalizados (OpenAI Compatible)", xalign=0
        )
        title.get_style_context().add_class("section-title")
        vbox.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=12, row_spacing=8)

        self.custom_name_entry = Gtk.Entry(placeholder_text="Ej: Groq o Servidor Local")
        self.custom_url_entry = Gtk.Entry(placeholder_text="https://api.ejemplo.com/v1")
        self.custom_key_entry = Gtk.Entry(placeholder_text="sk-...", visibility=False)

        entries = [self.custom_name_entry, self.custom_url_entry, self.custom_key_entry]
        for e in entries:
            e.set_hexpand(True)
            e.get_style_context().add_class("form-entry")

        grid.attach(Gtk.Label(label="Nombre:", xalign=1), 0, 0, 1, 1)
        grid.attach(self.custom_name_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Base URL:", xalign=1), 0, 1, 1, 1)
        grid.attach(self.custom_url_entry, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="API Key:", xalign=1), 0, 2, 1, 1)
        grid.attach(self.custom_key_entry, 1, 2, 1, 1)

        vbox.pack_start(grid, False, False, 0)

        add_btn = Gtk.Button(label="Añadir Proveedor")
        add_btn.get_style_context().add_class("suggested-action")
        add_btn.connect("clicked", self._on_add_custom_provider)
        vbox.pack_start(add_btn, False, False, 4)

        self.custom_list_box = Gtk.ListBox()
        self.custom_list_box.get_style_context().add_class("sidebar-list")
        self.custom_list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.get_style_context().add_class("scrolled-list")
        scrolled.set_size_request(-1, 130)
        scrolled.add(self.custom_list_box)

        lbl_list = Gtk.Label(label="Proveedores adicionales configurados:", xalign=0)
        lbl_list.get_style_context().add_class("dim-label")
        vbox.pack_start(lbl_list, False, False, 0)
        vbox.pack_start(scrolled, True, True, 0)

        self._add_stack_page(vbox, "custom", "Endpoints Propios")

    def _create_provider_page(
        self, provider_id, provider_name, default_models=None, is_custom=False
    ):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)

        if is_custom:
            url = (
                self.config.get("custom_providers", {})
                .get(provider_id, {})
                .get("base_url", "")
            )
            lbl_url = Gtk.Label(label=f"Endpoint: {url}", xalign=0)
            lbl_url.get_style_context().add_class("dim-label")
            vbox.pack_start(lbl_url, False, False, 0)

        api_label = Gtk.Label(label="Clave de la API (API Key):", xalign=0)
        api_label.get_style_context().add_class("dim-label")
        api_entry = Gtk.Entry(visibility=False)
        api_entry.get_style_context().add_class("form-entry")

        saved_key = ""
        try:
            saved_key = keyring.get_password(APP_ID, provider_id)
        except Exception as e:
            print(f"[Keyring] Error al leer credenciales para '{provider_id}': {e}")

        if not saved_key:
            saved_key = (
                self.config.get("custom_providers", {})
                .get(provider_id, {})
                .get("api_key", "")
                if is_custom
                else self.config.get(f"api_key_{provider_id}", "")
            )

        api_entry.set_text(saved_key or "")
        vbox.pack_start(api_label, False, False, 0)
        vbox.pack_start(api_entry, False, False, 0)

        model_label = Gtk.Label(label="Modelo por defecto:", xalign=0)
        model_label.get_style_context().add_class("dim-label")

        model_combo = Gtk.ComboBoxText()
        model_combo.get_style_context().add_class("form-combo")
        model_combo.append_text("Comprobando credenciales...")
        model_combo.set_active(0)

        cells = model_combo.get_cells()
        if cells:
            cells[0].set_property("width-chars", 20)
            cells[0].set_property("max-width-chars", 30)
            cells[0].set_property("ellipsize", Pango.EllipsizeMode.END)

        model_combo.set_size_request(250, -1)
        model_combo.set_hexpand(False)

        spinner = Gtk.Spinner()
        model_box = Gtk.Box(spacing=8)
        model_box.pack_start(model_combo, True, True, 0)
        model_box.pack_start(spinner, False, False, 0)

        vbox.pack_start(model_label, False, False, 0)
        vbox.pack_start(model_box, False, False, 0)

        refresh_btn = Gtk.Button(label="Verificar y Sincronizar Modelos")
        refresh_btn.connect(
            "clicked", self._on_refresh_models, provider_id, model_combo, spinner
        )
        vbox.pack_start(refresh_btn, False, False, 6)

        self.provider_widgets[provider_id] = {
            "api_entry": api_entry,
            "model_combo": model_combo,
            "spinner": spinner,
        }
        self._load_provider_models(provider_id)
        return vbox

    def _refresh_custom_list_visual(self):
        for child in self.custom_list_box.get_children():
            self.custom_list_box.remove(child)

        customs = self.config.get("custom_providers", {})
        for p_id, data in customs.items():
            row = Gtk.ListBoxRow()
            row.get_style_context().add_class("custom-provider-row")
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            label = Gtk.Label(label=data["name"].replace("custom_", ""), xalign=0)
            delete_btn = Gtk.Button.new_from_icon_name(
                "user-trash-symbolic", Gtk.IconSize.BUTTON
            )
            delete_btn.set_relief(Gtk.ReliefStyle.NONE)
            delete_btn.connect("clicked", self._on_delete_custom_provider, p_id)

            hbox.pack_start(label, True, True, 0)
            hbox.pack_end(delete_btn, False, False, 0)
            row.add(hbox)
            self.custom_list_box.add(row)
        self.custom_list_box.show_all()

    def refresh_local_models(self):
        self.local_model_combo.remove_all()
        try:
            models = ollama.list().get("models", [])
            for m in models:
                name = m.get("model", m.get("name"))
                self.local_model_combo.append(name, name)

            current = self.config.get("local_model", "")
            if current:
                self.local_model_combo.set_active_id(current)
            else:
                self.local_model_combo.set_active_index(0)
        except Exception:
            self.local_model_combo.append("error", "Servicio Ollama inaccesible")
            self.local_model_combo.set_active_id("error")

    def save_settings(self, btn):
        current_customs = self.config.get("custom_providers", {})

        new_config = {
            "local_model": self.local_model_combo.get_active_id(),
            "failover": self.failover_switch.get_active(),
            "default_provider": self.default_provider_combo.get_active_id(),
            "user_system_prompt": self.system_prompt_buffer.get_text(
                self.system_prompt_buffer.get_start_iter(),
                self.system_prompt_buffer.get_end_iter(),
                True,
            ),
            "custom_providers": current_customs,
        }

        for provider_id, widgets in self.provider_widgets.items():
            api_key = widgets["api_entry"].get_text().strip()
            current_model = widgets["model_combo"].get_active_id()
            is_valid_model = current_model and not current_model.startswith("Error")

            if api_key:
                try:
                    keyring.set_password(APP_ID, provider_id, api_key)
                except Exception as e:
                    print(
                        f"[Keyring] No se pudo guardar la clave para '{provider_id}': {e}"
                    )
            else:
                try:
                    keyring.delete_password(APP_ID, provider_id)
                except keyring.errors.PasswordDeleteError:
                    pass
                except Exception as e:
                    print(
                        f"[Keyring] Error al limpiar clave vacía de '{provider_id}': {e}"
                    )
            if provider_id in current_customs:
                if "api_key" in current_customs[provider_id]:
                    del current_customs[provider_id]["api_key"]
                if is_valid_model:
                    current_customs[provider_id]["selected_model"] = current_model
            else:
                storage.set_preference("IA_component", f"api_key_{provider_id}", None)
                if is_valid_model:
                    new_config[f"{provider_id}_model"] = current_model

        for k, v in new_config.items():
            storage.set_preference("IA_component", k, v)

        if self.callback_on_save:
            self.callback_on_save()

        self.destroy()

    def download_model(self, btn):
        model = self.dl_entry.get_text().strip()
        if not model:
            return
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"¿Confirmar descarga del modelo {model}?",
        )
        dialog.format_secondary_text("Se instalará el modelo desde la terminal.")
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            bus.publish("execute_command", f"ollama pull {model}")
        dialog.destroy()

    def _load_provider_models(self, provider_id: str):
        widgets = self.provider_widgets[provider_id]
        api_key = widgets["api_entry"].get_text().strip()
        widgets["spinner"].start()

        if provider_id != "openrouter" and not api_key:
            fallback = model_manager.get_fallback_models(provider_id)
            self._update_model_combo(provider_id, fallback, "API key no configurada")
            widgets["spinner"].stop()
            return

        def on_models_loaded(models, error):
            widgets["spinner"].stop()
            self._update_model_combo(provider_id, models, error)

        model_manager.get_models(provider_id, api_key, on_models_loaded)

    def _update_model_combo(self, provider_id: str, models: str, error: str = None):
        widgets = self.provider_widgets[provider_id]
        combo = widgets["model_combo"]
        combo.remove_all()

        if error and not models:
            combo.append_text(f"Error: {error or 'No se encontraron modelos'}")
            combo.set_active(0)
            return

        for model in models:
            combo.append(model, model)

        saved_model = self.config.get(f"{provider_id}_model", "")
        if not saved_model and provider_id in self.config.get("custom_providers", {}):
            saved_model = (
                self.config.get("custom_providers", {})
                .get(provider_id, {})
                .get("selected_model", "")
            )

        if saved_model and saved_model in models:
            combo.set_active_id(saved_model)
        elif models:
            combo.set_active(0)

    def _on_refresh_models(self, btn, provider_id, model_combo, spinner):
        api_key = self.provider_widgets[provider_id]["api_entry"].get_text().strip()
        spinner.start()

        def on_refreshed(models, error):
            spinner.stop()
            self._update_model_combo(provider_id, models, error)

        model_manager.refresh_cache(provider_id, api_key, on_refreshed)

    def _on_add_custom_provider(self, btn):
        name = "custom_" + self.custom_name_entry.get_text().strip()
        url = self.custom_url_entry.get_text().strip()
        key = self.custom_key_entry.get_text().strip()

        if not name or not url:
            return

        provider_id = name.lower().replace(" ", "_")

        if key:
            try:
                keyring.set_password(APP_ID, provider_id, key)
            except Exception as e:
                print(
                    f"[Keyring] No se pudo almacenar la clave para el endpoint personalizado '{provider_id}': {e}"
                )

        customs = self.config.get("custom_providers", {})
        customs[provider_id] = {"name": name, "base_url": url}
        self.config["custom_providers"] = customs

        storage.set_preference("IA_component", "custom_providers", customs)

        page = self._create_provider_page(provider_id, name, is_custom=True)
        self.notebook.append_page(page, Gtk.Label(label=f"{name}"))
        self.notebook.show_all()

        self.custom_name_entry.set_text("")
        self.custom_url_entry.set_text("")
        self.custom_key_entry.set_text("")
        self._refresh_custom_list_visual()
        self._refresh_cloud_content()

    def _on_delete_custom_provider(self, btn, p_id):
        customs = self.config.get("custom_providers", {})
        if p_id in customs:
            del customs[p_id]
            storage.set_preference("IA_component", "custom_providers", customs)

        try:
            keyring.delete_password(APP_ID, p_id)
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception as e:
            print(
                f"[Keyring] Error al eliminar credencial del proveedor extinto '{p_id}': {e}"
            )

        self._refresh_cloud_content()
        self._refresh_custom_list_visual()
