import json
import os
from gi.repository import Gtk, Gio
from core.keybindings import keybindings


class KeybindingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeybindingEngine, cls).__new__(cls)
            cls._instance.app = Gtk.Application.get_default()
            cls._instance.structured_bindings = {}

            config_dir = os.path.join(
                os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
                "canaima-ite",
            )
            cls._instance.user_json_path = os.path.join(
                config_dir, "user_keybindings_preferences.json"
            )

        return cls._instance

    def load_initial_shortcuts(self):
        if os.path.exists(self.user_json_path):
            try:
                with open(self.user_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"Preferencias locales cargadas desde: {self.user_json_path}")
                self.setup_shortcuts(data)
                return
            except Exception as e:
                print(
                    f"Error leyendo las preferencias locales ({e}). Cargando valores por defecto..."
                )

        try:
            print("Cargando atajos por defecto desde core.keybindings...")
            import copy

            data = copy.deepcopy(keybindings)

            self.setup_shortcuts(data)
            self._save_to_user_config(data)
        except Exception as e:
            print(f"Error crítico: No se pudo procesar el diccionario por defecto. {e}")

    def setup_shortcuts(self, structured_keybindings: dict):
        app = Gtk.Application.get_default()
        if not app:
            return

        self.structured_bindings = structured_keybindings

        for category, items in structured_keybindings.items():
            for item in items:
                action_name = item["action"]
                shortcut = item["shortcut"]
                app.set_accels_for_action(action_name, [shortcut])

    def update_shortcut(
        self, category: str, action_name: str, new_shortcut: str
    ) -> bool:
        app = Gtk.Application.get_default()
        if not app:
            return False

        for cat, items in self.structured_bindings.items():
            for item in items:
                if item["shortcut"] == new_shortcut and item["action"] != action_name:
                    print(
                        f"Conflicto: El atajo {new_shortcut} ya está asignado a {item['label']}"
                    )
                    return False

        for cat, items in self.structured_bindings.items():
            if cat == category:
                for item in items:
                    if item["action"] == action_name:
                        app.set_accels_for_action(action_name, [])
                        item["shortcut"] = new_shortcut
                        app.set_accels_for_action(action_name, [new_shortcut])
                        self._save_to_user_config(self.structured_bindings)
                        return True
        return False

    def reset_to_defaults(self) -> bool:
        try:
            if os.path.exists(self.user_json_path):
                os.remove(self.user_json_path)

            print(
                "Archivo de preferencias eliminado. Restaurando el diccionario base..."
            )

            import copy

            data = copy.deepcopy(keybindings)

            self.setup_shortcuts(data)
            return True
        except Exception as e:
            print(f"Error al restablecer valores de fábrica: {e}")
            return False

    def _save_to_user_config(self, data: dict):
        try:
            os.makedirs(os.path.dirname(self.user_json_path), exist_ok=True)

            with open(self.user_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Preferencias guardadas con éxito en {self.user_json_path}")
        except Exception as e:
            print(f"No se pudieron guardar las preferencias locales: {e}")

    def get_shortcuts_by_category(self) -> dict:
        return self.structured_bindings

    def split_shortcut_keys(self, shortcut: str) -> list:
        parts = shortcut.replace("<", "").split(">")
        keys = []
        for part in parts:
            if not part:
                continue
            if part == "control":
                keys.append("Ctrl")
            elif part == "shift":
                keys.append("Shift")
            elif part == "alt":
                keys.append("Alt")
            else:
                keys.append(part.upper())
        return keys

    def register_command(self, action_id, callback, widget=None):
        app = Gtk.Application.get_default()
        window = app.get_active_window()

        if not window:
            target = app
            prefix = "app"
        else:
            target = window
            prefix = "win"

        action = Gio.SimpleAction.new(action_id, None)
        action.connect("activate", lambda a, p: callback())

        group = target.get_action_group(prefix)
        if not group:
            group = Gio.SimpleActionGroup()
            target.insert_action_group(prefix, group)

        group.add_action(action)


registry = KeybindingEngine()
