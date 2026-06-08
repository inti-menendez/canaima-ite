import copy
import json
import os
from core.config import default_config
from core.terminal_palettes import TERMINAL_PALETTES
from gi.repository import GObject

try:
    from gi.repository import Vte
except ImportError:
    Vte = None


class ConfigEngine(GObject.Object):
    _instance = None

    __gsignals__ = {
        "config-changed": (GObject.SignalFlags.RUN_LAST, None, (str, str)),
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigEngine, cls).__new__(cls)
            cls._instance.current_config = {}

            config_dir = os.path.join(
                os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
                "canaima-ite",
            )
            cls._instance.user_config_path = os.path.join(
                config_dir, "user_preferences.json"
            )

            GObject.Object.__init__(cls._instance)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.load_config()

    def get(self, section, key):
        return self.current_config.get(section, {}).get(key, None)

    def set(self, section, key, value):
        if section not in self.current_config:
            self.current_config[section] = {}

        if self.current_config[section].get(key) != value:
            self.current_config[section][key] = value
            self._save_to_disk()
            self.emit("config-changed", section, key)

    def load_config(self):
        if os.path.exists(self.user_config_path):
            try:
                with open(self.user_config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)

                self.current_config = copy.deepcopy(default_config)
                for category, settings in user_data.items():
                    if category in self.current_config:
                        self.current_config[category].update(settings)

                print("Configuraciones integradas con éxito.")
                return
            except Exception as e:
                print(f"Error leyendo user_preferences.json ({e}). Usando fábrica.")

        self.current_config = copy.deepcopy(default_config)
        self._save_to_disk()

    def get_terminal_colors(self) -> dict:
        palette_name = self.get("appearance", "terminal_palette")
        return TERMINAL_PALETTES.get(palette_name, TERMINAL_PALETTES["canaima_default"])

    def get_cursor_shape_vte(self):
        if not Vte:
            return 0

        shape_str = self.get("appearance", "cursor_shape")
        mapping = {
            "block": Vte.CursorShape.BLOCK,
            "underline": Vte.CursorShape.UNDERLINE,
            "ibeam": Vte.CursorShape.IBEAM,
        }
        return mapping.get(shape_str, Vte.CursorShape.BLOCK)

    def reset_to_defaults(self):
        if os.path.exists(self.user_config_path):
            try:
                os.remove(self.user_config_path)
            except Exception as e:
                print(f"No se pudo limpiar el archivo: {e}")

        self.current_config = copy.deepcopy(default_config)

        for category, settings in self.current_config.items():
            for key in settings.keys():
                self.emit("config-changed", category, key)
        print("Configuraciones restablecidas a los valores de fábrica.")

    def _save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(self.user_config_path), exist_ok=True)
            with open(self.user_config_path, "w", encoding="utf-8") as f:
                json.dump(self.current_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error escribiendo configuración: {e}")


config_manager = ConfigEngine()
