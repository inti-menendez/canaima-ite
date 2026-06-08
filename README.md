# Canaima ITE - Entorno Integrado de Terminal

Canaima Entorno Integrado de Terminal (ITE) es una plataforma avanzada de terminal diseñada para potenciar la productividad y el desarrollo técnico dentro del ecosistema Canaima GNU/Linux y distribuciones basadas en Debian. Este entorno fusiona las capacidades robustas de una terminal multinivel con la asistencia contextualizada de modelos de Inteligencia Artificial (IA), tanto en ejecución local como a través de proveedores remotos, promoviendo la soberanía tecnológica y la adopción de Software Libre.

Desarrollado en el marco del Centro Nacional de Tecnologías de Información (CNTI) de la República Bolivariana de Venezuela, en colaboración institucional con la Universidad Nacional Experimental Politécnica de la Fuerza Armada Nacional Bolivariana (UNEFA), Canaima ITE representa una evolución en las herramientas de interfaz de línea de comandos (CLI) tradicionales, proporcionando un ecosistema visual y funcionalmente unificado.

## Características Principales

* **Terminal Multitesta Integrada:** Emulación de terminal de alto rendimiento basada en la biblioteca nativa Vte 2.91, permitiendo la gestión avanzada de pestañas y sesiones simultáneas con soporte POSIX completo.
* **Asistencia Inteligente Dual (Local y Remota):** Sistema híbrido que interactúa de manera transparente con modelos locales mediante Ollama (preservando la privacidad de los datos) y proveedores en la nube bajo el estándar de OpenAI (OpenRouter, Groq y Cerebras).
* **Arquitectura de Componentes Extensible:** Panel lateral dinámico (SidePanel) que organiza módulos de manera modular: Chat Bot de IA, Explorador de Archivos, Historial de Comandos Centralizado, Gestor de Atajos de Teclado y Panel de Preferencias.
* **Gestión Dinámica de Configuración y Atajos:** Interfaz intuitiva para personalizar el comportamiento del entorno y remapear combinaciones de teclas en tiempo real sin necesidad de reiniciar la aplicación.
* **Distribución Optimizada:** Compilación estática mediante Nuitka para generar un binario único en formato ELF, eliminando la complejidad de la gestión de dependencias en caliente y optimizando el consumo de recursos en el sistema operativo.

## Arquitectura del Sistema

El software se rige bajo un enfoque de diseño modular de alta cohesión y bajo acoplamiento, combinando patrones arquitectónicos modernos adaptados a interfaces gráficas:

1. **Diseño Orientado a Componentes:** Cada sección del Panel Lateral (`side_chatbot.py`, `side_explorer.py`, `side_history.py`, `side_keybindings.py`, `side_preferences.py`) funciona de forma autónoma, facilitando el mantenimiento y la escalabilidad del sistema sin romper la estabilidad funcional.
2. **Bus de Eventos (Event Bus):** Implementado en `event_bus.py`, centraliza la comunicación inter-componente mediante la publicación y suscripción de eventos, evitando dependencias directas entre la interfaz de usuario y los motores de lógica de negocio.
3. **Motores en Patrón Singleton:** Instancias críticas del núcleo, tales como `KeybindingEngine` y `ConfigEngine`, garantizan una única fuente de verdad para el estado de la aplicación y la persistencia de configuraciones globales.
4. **Reactividad Nativa GObject:** Aprovechamiento de señales e hilos (threading) integrados con el bucle de eventos principal (Main Loop) de GTK 3 para procesar respuestas asíncronas de la Inteligencia Artificial, impidiendo que la interfaz de usuario sufra bloqueos o congelamientos durante la latencia de red.


## Requisitos del Sistema

### Entorno de Ejecución Objetivo
* **Sistema Operativo:** Canaima GNU/Linux 8 o superior / Debian GNU/Linux Stable.
* **Arquitectura:** x86_64 (procesadores de 64 bits).

### Dependencias del Entorno de Desarrollo (si se ejecuta desde código fuente)
* Python 3.9 o superior
* PyGObject (GObject Introspection para Python)
* GTK 3 (gir1.2-gtk-3.0)
* Vte 2.91 (gir1.2-vte-2.91)
* Clientes API de OpenAI y Requests

## Guía de Configuración e Inicio Rápido

Canaima ITE se distribuye principalmente como un binario ejecutable precompilado (ELF). No obstante, para su correcto aprovechamiento es necesario configurar los servicios de Inteligencia Artificial que alimentan el asistente.

### 1. Configuración de Asistencia Local (Ollama)
Para disponer de un modelo de lenguaje completamente local y desconectado de internet:

1. Instale Ollama en su distribución Linux:

```zsh
   curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh

```

2. Asegúrese de que el servicio se encuentre activo en el puerto por defecto (11434):
```zsh
systemctl status ollama

```


3. Descargue un modelo compatible optimizado para asistencia en terminal (por ejemplo, Llama 3 o Mistral):
```zsh
ollama run llama3

```



### 2. Configuración de Asistencia Online (Proveedores en la Nube)

Si prefiere utilizar modelos remotos de alta velocidad y precisión, Canaima ITE ofrece soporte preconfigurado de fábrica para:

* **OpenRouter**
* **Groq**
* **Cerebras**

**Pasos para la integración:**

1. Obtenga la API Key del proveedor correspondiente desde su consola oficial.
2. Inicie Canaima ITE, diríjase al módulo de **Preferencias** en el panel lateral.
3. Introduzca la clave en el campo del proveedor seleccionado y guarde los cambios.

*Nota: Canaima ITE permite registrar endpoints personalizados de cualquier proveedor que cumpla de con el estándar de la API de OpenAI.*


## Compilación y Despliegue

Para replicar el proceso de empaquetado profesional y generar el ejecutable binario standalone, se utiliza el compilador Nuitka. Este proceso reduce sustancialmente el tamaño de despliegue en disco y optimiza la velocidad de ejecución.

Ejecute el comando de compilación dentro del directorio raíz del proyecto:

```zsh
nuitka --standalone --python-flag=-O --enable-plugin=pygobject --include-package=gi main.py

```

El resultado será un binario ejecutable optimizado listo para ser integrado en los repositorios oficiales de software de Canaima.

---

## Licencia

Este proyecto se distribuye bajo los términos de la **Licencia Pública General de GNU versión 3 (GPLv3)**. Como software libre, usted tiene la libertad de ejecutar, estudiar, compartir y modificar el programa para garantizar que la tecnología permanezca siempre al servicio del conocimiento colectivo y el desarrollo soberano. Consulte el archivo LICENSE para obtener el texto completo de la licencia.

---

## Créditos e Institucionalidad

* **Organismo Promotor:** Centro Nacional de Tecnologías de Información (CNTI) - Oficina de Operaciones Canaima.
* **Institución Académica:** Universidad Nacional Experimental Politécnica de la Fuerza Armada Nacional Bolaivariana (UNEFA) - Núcleo Carabobo / Distrito Capital.
* **Desarrollador / Autor:** Inti Omar Menéndez Sánchez (Ingeniería de Sistemas).
* **Tutor Institucional:** Ing. Ángel Marrufo.
* **Tutora Académica:** Ing. Aryeling Manosalva.
