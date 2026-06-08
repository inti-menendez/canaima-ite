import ollama
import shutil
import keyring
from contextlib import closing
from openai import OpenAI
from .app_storage import storage
from .ia_model_manager import model_manager
from .system_instructions import system_instructions
from .event_bus import bus

APP_ID = "canaima-ite"


class IAClient:
    def __init__(self):
        self.conf = storage.get_preference("IA_component") or {}
        self.failover_mode = self.conf.get("failover", False)
        self.provider_clients = {}
        self.reload()
        bus.subscribe("request_provider_status", self.check_provider_status)

    def reload(self):
        self.conf = storage.get_preference("IA_component") or {}
        self.failover_mode = self.conf.get("failover", False)
        self.provider_clients = {}
        self.check_provider_status()

    def check_provider_status(self, data=None):
        if self.conf.get("provider") == "local":
            ollama_ok = self.check_local_service_status()
            model = self.conf.get("local_model", "llama3.2:1b")

            bus.publish(
                "provider_change",
                {
                    "mode": "local",
                    "status": "online" if ollama_ok else "offline",
                    "label": f"({model})",
                    "tooltip": "Modo local: Servicio de Ollama disponible"
                    if ollama_ok
                    else "Modo local: Servicio de Ollama no disponible"
                    if ollama_ok
                    else "Ollama no responde o no está instalado",
                },
            )
        else:
            self._init_cloud_providers()
            provider = self.conf.get("default_provider", "openrouter")
            model = self.conf.get(f"{provider}_model", "auto")

            if self.has_internet():
                bus.publish(
                    "provider_change",
                    {
                        "mode": "cloud",
                        "status": "online",
                        "label": f"({provider})",
                        "tooltip": f"Modo online: Conectado a {provider} ({model})",
                    },
                )
            else:
                bus.publish(
                    "provider_change",
                    {
                        "mode": "cloud",
                        "status": "no_internet",
                        "label": "Nube (Sin Internet)",
                        "tooltip": "Modo online: no hay conexión de red",
                    },
                )

    def check_local_service_status(self) -> bool:
        if not shutil.which("ollama"):
            return False
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def get_available_providers(self) -> list:
        return list(self.provider_clients.keys())

    def get_current_model_info(self) -> dict:
        if self.conf.get("provider") == "local":
            return {
                "type": "local",
                "provider": "ollama",
                "model": self.conf.get("local_model", "llama3.2:1b"),
            }
        else:
            provider = self.conf.get("default_provider", "openrouter")
            if provider in self.provider_clients:
                return {
                    "type": "cloud",
                    "provider": provider,
                    "model": self.provider_clients[provider]["model"],
                    "base_url": self.provider_clients[provider]["base_url"],
                }
            return {
                "type": "cloud",
                "provider": provider,
                "model": "no configurado",
            }

    def _init_cloud_providers(self):
        for provider_key in model_manager.get_all_providers():
            config = model_manager.get_provider_config(provider_key)

            api_key = ""
            try:
                api_key = keyring.get_password(APP_ID, provider_key)
            except Exception as e:
                print(
                    f"[Keyring] Error al obtener credencial de inicialización para '{provider_key}': {e}"
                )

            if not api_key:
                api_key = self.conf.get(f"api_key_{provider_key}", "")

            model = self.conf.get(
                f"{provider_key}_model", ""
            ) or model_manager.get_default_model(provider_key)
            self._setup_provider(provider_key, config, api_key, model)

        customs = self.conf.get("custom_providers", {})
        for p_id, data in customs.items():
            config = {
                "name": data["name"],
                "base_url": data["base_url"],
                "priority": 10,
                "requires_auth": True,
            }

            api_key = ""
            try:
                api_key = keyring.get_password(APP_ID, p_id)
            except Exception as e:
                print(
                    f"[Keyring] Error al obtener credencial del endpoint personalizado '{p_id}': {e}"
                )

            if not api_key:
                api_key = data.get("api_key", "")

            self._setup_provider(
                p_id,
                config,
                api_key,
                data.get("selected_model", "auto"),
            )

    def _setup_provider(self, p_key, config, api_key, model):
        if config.get("requires_auth") and not api_key:
            return
        try:
            self.provider_clients[p_key] = {
                "client": OpenAI(base_url=config["base_url"], api_key=api_key),
                "model": model,
                "priority": config.get("priority", 999),
                "base_url": config["base_url"],
            }
        except Exception as e:
            print(f"Error inicializando {p_key}: {e}")

    def get_ai_response(
        self,
        user_message: str,
        system_prompt: str = None,
        stop_event=None,
    ):
        sys_prompt = system_prompt or self._get_default_system_prompt()

        if self.conf.get("provider") == "local":
            return self._get_local_response(user_message, sys_prompt, stop_event)

        if self.failover_mode:
            return self._get_response_with_failover(
                user_message, sys_prompt, stop_event
            )

        default_p = self.conf.get("default_provider", "openrouter")
        return self._get_response_from_provider(
            user_message, sys_prompt, default_p, stop_event
        )

    def _get_local_response(self, user_message, system_prompt, stop_event=None):
        model = self.conf.get("local_model", "")
        try:
            try:
                ollama.list()
            except Exception:
                yield {
                    "status": "error",
                    "content": "Ollama no responde. ¿Está corriendo el servicio?",
                }
                return

            with closing(
                ollama.chat(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    stream=True,
                )
            ) as stream:
                for chunk in stream:
                    if stop_event and stop_event.is_set():
                        print("[- ITE] Conexión local con Ollama abortada con éxito.")
                        return

                    yield {
                        "status": "success",
                        "content": chunk["message"]["content"],
                    }

        except Exception as e:
            yield {"status": "error", "content": f"Error en Ollama: {str(e)}"}

    def _get_response_from_provider(
        self, user_message, system_prompt, provider_name, stop_event=None
    ):
        if provider_name not in self.provider_clients:
            yield {
                "status": "error",
                "content": f"Proveedor '{provider_name}' no configurado.",
            }
            return

        p = self.provider_clients[provider_name]
        response = None
        try:
            response = p["client"].chat.completions.create(
                model=p["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                stream=True,
            )
            for chunk in response:
                if stop_event and stop_event.is_set():
                    print(f"[- ITE] Cerrando stream HTTP con {provider_name}...")
                    if hasattr(response, "close"):
                        response.close()
                    print(
                        f"[- ITE] Conexión con {provider_name} destruida limpiamente."
                    )
                    return

                content = chunk.choices[0].delta.content or ""
                if content:
                    yield {"status": "success", "content": content}
        except Exception as e:
            if stop_event and stop_event.is_set():
                print(
                    f"[- ITE] Conexión con {provider_name} interrumpida por excepción controlada."
                )
                return
            yield {
                "status": "error",
                "content": f"Error en {provider_name}: {str(e)}",
            }

    def _get_response_with_failover(self, user_message, system_prompt, stop_event=None):
        default_p = self.conf.get("default_provider", "openrouter")

        backup_p = sorted(
            [item for item in self.provider_clients.items() if item[0] != default_p],
            key=lambda p: p[1]["priority"],
        )
        default_c = self.provider_clients.get(default_p)
        sorted_p = ([(default_p, default_c)] + backup_p) if default_c else backup_p

        for p_name, _ in sorted_p:
            if stop_event and stop_event.is_set():
                print("[- ITE] Failover cancelado por el usuario.")
                return

            try:
                stream = self._get_response_from_provider(
                    user_message, system_prompt, p_name, stop_event
                )

                first_chunk = next(stream)

                if first_chunk["status"] == "error":
                    print(f"Provider {p_name} reportó error, saltando...")
                    continue

                yield first_chunk

                for chunk in stream:
                    if stop_event and stop_event.is_set():
                        print(f"[- ITE] Deteniendo flujo de failover en {p_name}.")
                        return
                    yield chunk
                return

            except (StopIteration, Exception) as e:
                if stop_event and stop_event.is_set():
                    print("[- ITE] Streaming en failover detenido por el usuario.")
                    return
                print(f"Excepción en failover con {p_name}: {e}")
                continue

        yield {
            "status": "error",
            "content": "Todos los proveedores fallaron o no están configurados. Revisa tu conexión.",
        }

    def _get_default_system_prompt(self):
        custom = self.conf.get("user_system_prompt", "").strip()
        return f"{system_instructions}\n\n{custom}" if custom else system_instructions

    def check_health(self):
        report = []
        provider_mode = self.conf.get("provider", "local")

        if provider_mode == "local":
            if not shutil.which("ollama"):
                report.append("ollama_not_installed")
            else:
                try:
                    models_data = ollama.list()

                    if not models_data.get("models"):
                        report.append("no_local_models")

                    elif self.conf.get("local_model") not in [
                        m["model"] for m in models_data["models"]
                    ]:
                        report.append("selected_model_not_found")
                except Exception:
                    report.append("ollama_service_down")

        else:
            default_p = self.conf.get("default_provider", "openrouter")
            if default_p not in self.provider_clients:
                report.append("missing_api_key")

        is_ok = len([e for e in report if e not in ["no_local_models"]]) == 0
        return is_ok, report

    def has_internet(self):
        import socket

        try:
            socket.create_connection(("1.1.1.1", 53), timeout=1.5)
            return True
        except OSError:
            return False


client = IAClient()
