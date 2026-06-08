import threading
import requests
from typing import Dict, List, Callable, Optional
import keyring
import keyring.errors
from gi.repository import GLib
from core.app_storage import storage

APP_ID = "canaima-ite"


class IAModelManager:
    PROVIDERS = {
        "openrouter": {
            "name": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "models_url": "https://openrouter.ai/api/v1/models",
            "requires_auth": False,
            "default_model": "openrouter/free",
            "priority": 1,
            "parser": lambda data: [model["id"] for model in data.get("data", [])],
        },
        "groq": {
            "name": "Groq",
            "base_url": "https://api.groq.com/openai/v1",
            "models_url": "https://api.groq.com/openai/v1/models",
            "requires_auth": True,
            "default_model": "llama-3.3-70b-versatile",
            "priority": 2,
            "parser": lambda data: [model["id"] for model in data.get("data", [])],
        },
        "cerebras": {
            "name": "Cerebras",
            "base_url": "https://api.cerebras.ai/v1",
            "models_url": "https://api.cerebras.ai/v1/models",
            "requires_auth": True,
            "default_model": "llama3.1-8b",
            "priority": 3,
            "parser": lambda data: [model["id"] for model in data.get("data", [])],
        },
    }

    FALLBACK_MODELS = {
        "openrouter": [
            "openrouter/free",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3.2-3b-instruct",
        ],
        "groq": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        "cerebras": ["llama3.1-8b", "llama-3.3-70b"],
    }

    def __init__(self):
        self.cache = {}
        self.loading_callbacks = {}

    def get_provider_config(self, provider: str) -> Optional[Dict]:
        return self.PROVIDERS.get(provider)

    def get_all_providers(self) -> List[str]:
        return list(self.PROVIDERS.keys())

    def get_default_model(self, provider: str) -> str:
        config = self.PROVIDERS.get(provider, {})
        return config.get("default_model", "")

    def get_models(
        self,
        provider: str,
        api_key: Optional[str] = None,
        callback: Optional[Callable] = None,
    ):
        if provider in self.cache and self.cache[provider]:
            models = self.cache[provider]
            if callback:
                GLib.idle_add(callback, models, None)
            return models

        if callback:
            self._load_models_async(provider, api_key, callback)

        return None

    def _load_models_async(
        self, provider: str, api_key: Optional[str], callback: Callable
    ):
        def load_thread():
            try:
                config = self.PROVIDERS.get(provider) or self._get_custom_config(
                    provider
                )

                if not config:
                    GLib.idle_add(callback, [], f"Proveedor {provider} no encontrado")
                    return

                headers = {}
                effective_api_key = api_key
                if not effective_api_key:
                    try:
                        effective_api_key = keyring.get_password(APP_ID, provider)
                    except Exception as e:
                        print(
                            f"[Keyring] Advertencia al resolver de forma implícita para '{provider}': {e}"
                        )

                    if not effective_api_key:
                        ia_config = storage.get_preference("IA_component") or {}
                        if config.get("is_custom"):
                            effective_api_key = (
                                ia_config.get("custom_providers", {})
                                .get(provider, {})
                                .get("api_key")
                            )
                        else:
                            effective_api_key = ia_config.get(f"api_key_{provider}")

                if effective_api_key:
                    headers["Authorization"] = f"Bearer {effective_api_key}"
                elif config["requires_auth"]:
                    GLib.idle_add(
                        callback,
                        self.FALLBACK_MODELS.get(provider, []),
                        "API key requerida",
                    )
                    return

                response = requests.get(
                    config["models_url"], headers=headers, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    models = config["parser"](data)
                    models = self._filter_models(models, provider)
                    models.sort()
                    self.cache[provider] = models
                    GLib.idle_add(callback, models, None)
                else:
                    msg = f"HTTP {response.status_code}: {response.text[:50]}"
                    GLib.idle_add(callback, self.FALLBACK_MODELS.get(provider, []), msg)

            except Exception as e:
                GLib.idle_add(
                    callback,
                    self.FALLBACK_MODELS.get(provider, []),
                    f"Error: {str(e)}",
                )

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _filter_models(self, models: List[str], provider: str) -> List[str]:
        if provider == "openrouter":
            popular = ["free", "gemini", "llama", "mistral", "mixtral"]
            filtered = [m for m in models if any(k in m.lower() for k in popular)]
            return filtered[:25]
        else:
            return models

    def refresh_cache(
        self,
        provider: str,
        api_key: Optional[str] = None,
        callback: Optional[Callable] = None,
    ):
        if provider in self.cache:
            del self.cache[provider]
        return self.get_models(provider, api_key, callback)

    def get_fallback_models(self, provider: str) -> List[str]:
        return self.FALLBACK_MODELS.get(provider, [])

    def _get_custom_config(self, provider_id: str) -> Optional[Dict]:
        ia_config = storage.get_preference("IA_component") or {}
        customs = ia_config.get("custom_providers", {})

        if provider_id in customs:
            data = customs[provider_id]
            return {
                "name": data["name"],
                "base_url": data["base_url"],
                "models_url": f"{data['base_url'].rstrip('/')}/models",
                "requires_auth": True,
                "default_model": "auto",
                "parser": lambda data: [model["id"] for model in data.get("data", [])],
                "is_custom": True,
            }
        return None


model_manager = IAModelManager()
