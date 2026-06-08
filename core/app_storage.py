import os
import json
from datetime import datetime
from platformdirs import user_config_dir, user_data_dir


class AppStorage:
    def __init__(self):

        self.config_dir = user_config_dir("canaima-ite")
        self.data_dir = user_data_dir("canaima-ite")

        self.history_path = os.path.join(self.data_dir, "history.json")
        self.prefs_path = os.path.join(self.config_dir, "user_config.json")

        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        self._init_files()

    def _init_files(self):
        if not os.path.exists(self.prefs_path):
            initial_prefs = default_preferences
            with open(self.prefs_path, "w") as f:
                json.dump(initial_prefs, f, indent=4)

        if not os.path.exists(self.history_path):
            with open(self.history_path, "w") as f:
                json.dump([], f)

    def get_preference(self, component, key=None, default=None):
        try:
            if (
                not os.path.exists(self.prefs_path)
                or os.stat(self.prefs_path).st_size == 0
            ):
                return default

            with open(self.prefs_path, "r") as f:
                data = json.load(f)

                if key is None:
                    return data.get(component, default)

                return data.get(component, {}).get(key, default)

        except (json.JSONDecodeError, IOError, Exception) as e:
            print(f"Error leyendo preferencias: {e}")
            return default

    def set_preference(self, component, key, value):
        try:
            data = {}
            if os.path.exists(self.prefs_path):
                with open(self.prefs_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}

            if component not in data or not isinstance(data[component], dict):
                data[component] = {}

            data[component][key] = value

            with open(self.prefs_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando preferencia: {e}")

    def save_to_history(self, command, cwd="/"):
        try:
            history = self.load_history()

            new_entry = {
                "command": command,
                "time": datetime.now().strftime("%H:%M:%S"),
                "cwd": cwd,
                "full_date": datetime.now().isoformat(),
            }

            history.insert(0, new_entry)

            limit = self.get_preference("history_component", "limit", 1000)
            history = history[:limit]

            with open(self.history_path, "w") as f:
                json.dump(history, f, indent=4)

            return new_entry
        except Exception as e:
            print(f"Error guardando historial: {e}")
            return None

    def load_history(self):
        if (
            not os.path.exists(self.history_path)
            or os.stat(self.history_path).st_size == 0
        ):
            return []

        try:
            with open(self.history_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def delete_entry_by_date(self, full_date):
        try:
            history = self.load_history()

            new_history = [e for e in history if e.get("full_date") != full_date]

            with open(self.history_path, "w") as f:
                json.dump(new_history, f, indent=4)
            return True
        except Exception as e:
            print(f"Error eliminando entrada: {e}")
            return False

    def delete_history(self):
        try:
            with open(self.history_path, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error limpiando historial: {e}")


default_preferences = {
    "IA_component": {
        "provider": "local",
        "openrouter_model": "openrouter/free",
        "default_provider": "openrouter",
        "local_model": "",
    },
    "history_component": {"default_click_action": "paste", "limit": 1000},
}

storage = AppStorage()
