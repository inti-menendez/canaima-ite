# Guía Técnica de Desarrollo - Canaima ITE

## 1. Introducción y Contexto Institucional

### 1.1. Propósito del Documento

Este documento técnico describe los fundamentos arquitectónicos, la lógica de componentes y los flujos de control que componen el Entorno Integrado de Terminal Canaima ITE. Su propósito es servir como una guía para la auditoría, mantenimiento, optimización y extensión del software por parte de cualquier interesado.

### 1.2. Marco del Proyecto: CNTI y UNEFA

Canaima ITE nace como un proyecto de práctica profesional desarrollado dentro de la Oficina de Operaciones Canaima del CNTI, para la Universidad Nacional Experimental Politécnica de la Fuerza Armada Nacional Bolivariana (UNEFA). El sistema responde a las directrices de la República Bolivariana de Venezuela en materia de apropiación del conocimiento y construcción de herramientas nativas de código abierto.

### 1.3. Enfoque Pedagógico y Soberanía Tecnológica

A diferencia de los entornos de terminal comerciales o herramientas basadas en agentes autónomos, Canaima ITE se rige bajo un **paradigma pedagógico de asistencia**. El sistema no lee el historial de comandos de forma encubierta, no altera variables de entorno ni interactúa autónomamente con el sistema operativo. El asistente de Inteligencia Artificial (IA) opera como un consultor teórico interactivo aislado en su propio hilo de interfaz.

Este diseño técnico invita al usuario a formular sus dudas, analizar las respuestas explicativas del asistente y ejecutar manualmente los comandos en la pestaña de la terminal, garantizando un proceso de aprendizaje activo.

---

## 2. Arquitectura General del Sistema

### 2.1. Paradigma de Diseño Orientado a Componentes

El software rechaza el acoplamiento directo entre elementos visuales. La interfaz se construye de forma modular; la ventana principal actúa como el contenedor del bucle de eventos general y delega la responsabilidad visual a dos áreas autónomas principales:

1. **El Espacio de Trabajo de Terminal:** Instancias dinámicas de pestañas de emulación basadas en la biblioteca Vte.
2. **El Panel Lateral (`side_panel.py`):** Un contenedor apilable que gestiona los subcomponentes de control, historial, atajos y el chat de asistencia de forma independiente.

### 2.2. Patrón de Desacoplamiento mediante Bus de Eventos

Para permitir que los componentes respondan a cambios globales de configuración o estados sin referenciarse directamente entre sí, se implementa una arquitectura dirigida por eventos. Cuando un usuario altera un parámetro en el panel de preferencias, el cambio no altera directamente al chatbot o a la terminal; en su lugar, se despacha una señal al Bus de Eventos centralizado, el cual notifica exclusivamente a los componentes que se hayan suscrito a dicho tópico.

### 2.3. Ciclo de Vida de la Aplicación y Main Loop de GTK 3

Canaima ITE se ejecuta sobre el hilo principal del bucle de eventos de GTK 3. Este ciclo maneja la renderización de la interfaz, la captura de atajos de teclado y la actualización de los buffers de la terminal Vte. Cualquier bloqueo de este hilo por una operación pesada puede congelar la aplicación.

### 2.4. Gestión de Concurrencia y Hilos (Threading)

Dado que las peticiones a modelos de lenguaje (locales mediante Ollama o remotas mediante APIs de terceros) conllevan latencia física de red o procesamiento, el subsistema de IA se ejecuta estrictamente en hilos de trabajo independientes (`threading.Thread`). Las respuestas parciales recibidas en streaming se introducen de vuelta al hilo principal de GTK de forma segura utilizando `GLib.idle_add()`, previniendo colisiones de memoria en el renderizado de la interfaz gráfica.

---

## 3. Arquitectura del Núcleo (Core Engines)

### 3.1. Bus de Eventos (`event_bus.py`)

El componente `EventBus` es una instancia singleton que actúa como un despachador central de señales en memoria utilizando un diccionario de devoluciones de llamada (callbacks).

Para manejar esta interacción simplemente se hace un pub/sub
el publicador en algun punto de la app donde le interese
```python
bus.publish("nombre_evento", datos_asociados)
```
quien se subscribe y actua cuando se publica
```python
bus.subscribe("nombre_evento", callback)
```
donde callback es una funcion o metodo que recibe los datos asociados y decide que hacer


### 3.2. Motor de Configuración (`config_engine.py`, `app_storage.py`)

Implementado bajo el patrón **Singleton**, estas instancias centralizan la lectura y escritura del archivo de configuración JSON de la aplicación. Al inicializarse, carga los valores por defecto del sistema y exponen métodos seguros para actualizar los parámetros de los proveedores de IA y configuraciones visuales.

### 3.3. Motor de Atajos de Teclado (`keybinding_engine.py`)

Este motor intercepta las señales de teclado de la ventana principal de GTK. Administra un mapa dinámico de combinaciones de teclas que el usuario puede reconfigurar en caliente. Al capturar un evento de teclado válido, verifica si coincide con alguna acción registrada (como abrir pestañas o alternar el panel lateral) y ejecuta la acción asociada, impidiendo que el evento interfiera con los comandos nativos heredados por la terminal interna Vte.

---

## 4. Subsistema de Inteligencia Artificial

### 4.1. Abstracción del Cliente de IA (`ia_client.py`)

El módulo `ia_client.py` encapsula las llamadas a los modelos de lenguaje a través de una interfaz unificada. Utiliza la biblioteca oficial de OpenAI para Python debido a su compatibilidad generalizada con múltiples proveedores del mercado. Esta clase se encarga de:

* Instanciar el cliente con la clave de API (`api_key`) y la dirección base del servidor (`base_url`) correspondientes.
* Configurar los parámetros de generación recuperados dinámicamente desde el `AppStorage`.
* Capturar y manejar excepciones de red o de autenticación sin propagar fallos catastróficos a la interfaz de usuario.

### 4.2. Orquestación de Modelos (`ia_model_manager.py`)

El `IAModelManager` funciona como el cerebro lógico del subsistema de IA. Su tarea principal es actuar como un conmutador basado en la configuración activa. Cuando el panel lateral solicita una consulta, el gestor evalúa si el usuario seleccionó un entorno local o remoto:

1. **Entorno Local (Ollama):** Redirige el tráfico hacia el socket local (normalmente `http://localhost:11434/v1`), omitiendo la validación de claves remotas.
2. **Entorno Online (Proveedores en la Nube):** Mapea los endpoints específicos de Groq, OpenRouter o Cerebras utilizando las credenciales almacenadas de manera segura en el wallet del sistema operativo.

### 4.3. Integración con el Estándar de la API de OpenAI

Para garantizar la extensibilidad y evitar el bloqueo de proveedores (vendor lock-in), el gestor de IA se comunica bajo el estándar de Completaciones de Chat de OpenAI (`v1/chat/completions`). Cualquier API de terceros o servidor local propio implementado en el futuro por los usuarios podrá integrarse de forma inmediata, siempre que cumpla con dicha especificación.

### 4.4. Manejo de Respuestas por Streaming y Evitación de Bloqueos en la GUI

Para ofrecer una experiencia interactiva fluida, las respuestas se solicitan activando el parámetro `stream=True`. Esto devuelve un generador que entrega tokens (fragmentos de texto) de forma progresiva.

Como este bucle de lectura es una operación síncrona bloqueante, se ejecuta dentro de un hilo secundario (`threading.Thread`). Para actualizar la interfaz gráfica (`Gtk.TextView` dentro de `chat_bot.py`) con cada token recibido sin corromper la memoria del hilo principal de GTK, se utiliza la función `GLib.idle_add()`, la cual agenda la inserción de texto de manera segura en el ciclo del Main Loop.

> **Nota de Diseño de Seguridad y Aislamiento:** El flujo de datos dentro de este subsistema es estrictamente unidireccional y reactivo. El payload enviado al modelo se compone única y exclusivamente del texto que el usuario introduce manualmente en el campo de entrada del chat. El sistema no inyecta variables de entorno, no lee los buffers de las terminales activas ni examina archivos del sistema de forma automática. Esto mitiga vulnerabilidades por inyección de comandos indirectos (Prompt Injection) y preserva la privacidad del usuario.

---

## 5. Componentes de la Interfaz Gráfica (GTK 3 + Vte)

### 5.1. Inicialización y Gestión de Ventanas (`main.py, window.py` )

El archivo `main.py` constituye el punto de entrada de la aplicación. Configura el entorno global de GObject, inicializa las bibliotecas GTK y Vte, y construye la ventana de la aplicación  (`window.py, Gtk.ApplicationWindow`). Coordina el tamaño inicial y registra los callbacks globales para el cierre limpio de procesos hijos de la terminal antes de destruir la ventana.

### 5.2. Emulación de Terminal y Manejo de Pestañas mediante la Biblioteca Vte

La emulación de terminal se delega a `Vte.Terminal()`. Cada pestaña creada en la interfaz es un contenedor intermedio (`Gtk.Box`) que aloja una instancia de Vte, Estas boxes se alojan dentro del widget Gtk.Notebook para la gestion de pestañas. Esta biblioteca se encarga de invocar de forma nativa el shell del sistema (por defecto `/bin/bash` o `/bin/zsh` en Canaima GNU/Linux), manejar el renderizado de secuencias de escape ANSI, colores, fuentes y administrar las señales POSIX de los subprocesos en ejecución.

### 5.3. Contenedor del Panel Lateral (`side_panel.py`)

El `SidePanel` implementa un contenedor de tipo `Gtk.Stack` acompañado de un `Gtk.StackSwitcher` o barra de iconos lateral. Este diseño optimiza el uso de la memoria RAM del sistema, ya que todos los paneles secundarios se instancian durante el arranque pero solo el componente seleccionado visualmente consume recursos de renderizado activos en el servidor gráfico.

### 5.4. Componentes Modulares de Panel

#### 5.4.1. Asistente de IA (`side_chatbot.py`)

Contiene la interfaz de conversación (chat en formato de texto enriquecido y campo de entrada de texto). Al recibir una respuesta del hilo de IA, procesa las etiquetas de Markdown de forma básica para resaltar bloques de código, facilitando el copiado manual por parte del usuario. Su enfoque es estrictamente pedagógico: actúa como un tutor explicativo.

#### 5.4.2. Explorador de Archivos Contextual (`side_explorer.py`)

Un componente basado en un árbol visual (`Gtk.TreeView`) acoplado a un modelo de almacenamiento de datos (`Gtk.TreeStore`). Permite navegar de forma gráfica por los directorios del usuario, proporcionando una referencia visual rápida para que el usuario localice rutas y archivos sin necesidad de abandonar la terminal, es reactivo y tiene relacion bidireccional directa con la terminal.

#### 5.4.3. Buscador e Historial de Comandos (`side_history.py`)

Este panel integra un buscador reactivo que examina el historial local de comandos ejecutados en la aplicación. Permite filtrar rápidamente estructuras de comandos anteriores mediante un widget de entrada de texto (`Gtk.SearchEntry`), promoviendo la reutilización de código y comandos complejos estudiados con anterioridad.

#### 5.4.4. Configuración Interactiva de Atajos (`side_keybindings.py`)

Interfaz visual que lista las funciones del sistema y sus atajos asociados. Permite capturar eventos de teclas (`key-press-event`) para remapear dinámicamente las combinaciones guardadas en el `KeybindingEngine` sin requerir que el usuario edite archivos de configuración en modo texto.

#### 5.4.5. Panel de Preferencias Generales (`side_preferences.py`)

Interfaz visual intuitiva para la personalización del programa, permite cambiar la paleta de colores de la terminal, el tamaño y fuente del texto, la disposición del panel lateral entre otros.

---

## 6. Entorno de Desarrollo e Instalación

### 6.1. Requisitos del Sistema y Dependencias Base

Para configurar el entorno de desarrollo de Canaima ITE sobre la distribución nacional Canaima GNU/Linux (versión 8 "Kavanayén" o superior), es mandatorio instalar las bibliotecas nativas de desarrollo del ecosistema GNOME y los enlaces de introspección de GObject para Python:

* **Intérprete Core:** Python 3, aprovechando su recolector de basura por conteo de referencias y optimización de llamadas de entrada/salida.
* **Emulación de Terminal:** `libvte-2.91-dev`, paquete que provee las cabeceras nativas en C y los archivos de tipado para gestionar terminales compatibles con el estándar POSIX.
* **Interfaz Gráfica:** `python3-gi` y `python3-gi-cairo`, necesarios para la inyección y manipulación de los widgets de GTK 3 mediante PyGObject.
* **Compilación:** Conjunto de herramientas GCC (GNU Compiler Collection) junto al paquete `patchelf`, indispensables para el enlazado estático de bibliotecas compartidas durante la fase de optimización con Nuitka.

ver la [guia del entorno dev](guides/dev-guide.md) para mas información

### 6.2. Estructura de Directorios del Proyecto

El código fuente de la aplicación se organiza de forma modular y desacoplada, separando estrictamente los motores lógicos de los contenedores gráficos de la interfaz de usuario:

```
canaima-ite/
├── assets
│   └── canaima-logo.png
├── core
│   ├── app_storage.py
│   ├── config_engine.py
│   ├── config.py
│   ├── event_bus.py
│   ├── ia_client.py
│   ├── ia_model_manager.py
│   ├── __init__.py
│   ├── keybindings_engine.py
│   ├── keybindings.py
│   ├── system_instructions.py
│   └── terminal_palettes.py
├── docs
│   ├── guides
│   │   ├── build-guide.md
│   │   ├── dev-guide.md
│   │   └── get-apikey-guide.md
│   ├── lib
│   │   ├── docsify-copy-code.min.js
│   │   ├── docsify.min.js
│   │   ├── index.min.js
│   │   └── style.min.css
│   ├── DEVELOPER_GUIDE.md
│   ├── index.html
│   ├── README.md
│   ├── _sidebar.md
│   └── USER_MANUAL.md
├── scripts
│   ├── add.py
│   ├── build.sh
│   └── zshrc
├── src
│   ├── components
│   │   ├── activity_bar.py
│   │   ├── command_detail.py
│   │   ├── footer.py
│   │   ├── header_bar.py
│   │   ├── ia_settings_window.py
│   │   ├── __init__.py
│   │   ├── left_container.py
│   │   ├── main_box.py
│   │   ├── side_chatbot.py
│   │   ├── side_explorer.py
│   │   ├── side_history.py
│   │   ├── side_keybindings.py
│   │   ├── side_panel.py
│   │   ├── side_preferences.py
│   │   └── terminal_box.py
│   ├── __init__.py
│   └── window.py
├── LICENSE
├── main.bin
├── main.py
├── README.md
├── requirements.txt
└── TODO
```

### 6.3. Cumplimiento del Estándar XDG Base Directory

Canaima ITE rechaza la polución del directorio raíz del usuario (`~`) mediante archivos ocultos propietarios. El sistema se alinea estrictamente con las especificaciones de del estándar XDG para garantizar la portabilidad y auditoría de datos:

* **Datos e Historial Ampliado:** La persistencia estructurada del archivo `history.json` (que almacena marcas de tiempo, comandos ejecutados y rutas de trabajo) se ubica en `~/.local/share/canaima-ite/`.
* **Configuraciones y Preferencias:** los esquemas de color de la terminal (Dracula, Monokai, Nord, Canaima) y el mapa dinámico de atajos de teclado se almacenan en `~/.config/canaima-ite/`.

---

## 7. Compilación Avanzada y Despliegue con Nuitka

### 7.1. Traducción de Árboles de Sintaxis Abstracta (AST) a C/C++

Para resolver el aislamiento de dependencias en entornos de producción y omitir el sobrecosto de interpretación en tiempo de ejecución, el despliegue no se realiza en formato de script puro. Se utiliza el compilador avanzado Nuitka, el cual procesa el código fuente Python, analiza sus árboles de sintaxis abstracta (AST) y lo traduce directamente a código fuente de bajo nivel C/C++, que posteriormente es compilado en un ejecutable nativo por GCC.

El comando de producción implementado para la generación del binario se puede ver en el script `build.sh`:
para mas informacion leer la [guia de compilacion](guides/build-guide.md)


### 7.2. Optimización LTO (Link Time Optimization) y Compresión Zstandard

El proceso de construcción inyecta dos técnicas críticas de optimización de ingeniería de software:

1. **Link Time Optimization (LTO):** Al activar `--lto=yes`, el compilador realiza mejoras globales y optimizaciones intermodulares en todo el binario durante la fase final de enlazado, reduciendo código muerto y acelerando la velocidad de renderizado de la interfaz gráfica.
2. **Compresión Zstandard (`zstd`):** Integrada para empaquetar de forma monolítica las bibliotecas compartidas dentro del formato ejecutable único. `zstd` provee una tasa de compresión sustancialmente superior a los algoritmos tradicionales como `gzip`, asegurando que el binario se descomprima en memoria de manera casi instantánea al invocarse en la terminal, mejorando drásticamente los tiempos de arranque percibidos por el usuario.

### 7.3. Reducción del Peso del Binario ELF

Durante las fases iniciales de desarrollo del proyecto, el uso de empaquetadores convencionales basados en la recolección de entornos virtuales interpretados generaba un archivo ejecutable redundante que alcanzaba los 120 megabytes de peso. La adopción final de la compilación nativa estática con Nuitka redujo el tamaño final del binario ejecutable único en formato ELF a unos 33mb aproximadamente, logrando un ahorro de almacenamiento superior y garantizando una distribución sumamente liviana en los repositorios oficiales de Canaima GNU/Linux.
para mas informacion sobre las alternativas de empaquetamiento leer la [guia de compilacion](guides/build-guide.md)

---

## 8. Optimización y Métricas de Rendimiento

### 8.1. Análisis de Consumo de Recursos (CPU y Memoria RAM)

Con el propósito de validar la viabilidad técnica y ligereza del entorno integrado en estaciones de trabajo institucionales y computadoras con especificaciones de hardware limitadas, se realizaron auditorías empíricas utilizando la herramienta de diagnóstico de bajo nivel `htop`.

Tomando como entorno de pruebas una estación de trabajo estándar del CNTI con una capacidad total de memoria física RAM de 7.6 GB (7782.4 MB), se contrastó el desempeño en frío (reposo operativo) de Canaima ITE frente a la consola base del sistema operativo, XFCE Terminal:

* **Línea Base (XFCE Terminal):** Registró un consumo porcentual del 0.6 % de la memoria física disponible, equivalente a un impacto neto de **46.69 megabytes**.

$$\text{RAM}_{xfce} = 7782.4\,\text{MB} \times 0.006 = 46.69\,\text{MB}$$


* **Entorno Integrado (Canaima ITE):** Registró un consumo de entre el 2.2 % y el 2.6 % de la memoria RAM del sistema, traduciéndose en un impacto neto de **171.21 a 202.34 megabytes** según la carga inicial de componentes gráficos.

$$\text{RAM}_{ite} = 7782.4\,\text{MB} \times 0.026 = 202.34\,\text{MB}$$



### 8.2. Justificación de la Carga de Memoria y Sostenibilidad

El incremento neto observado de aproximadamente **155.65 megabytes** se encuentra plenamente justificado desde la perspectiva de la ingeniería de software. Este margen representa el costo en memoria de cargar simultáneamente el entorno de hilos concurrentes de Python, las estructuras del árbol de datos para el explorador visual, la persistencia indexada del historial y el búfer de texto enriquecido del chat del asistente de IA. 

Considerando que esta integración compacta disminuye la necesidad de mantener abiertos navegadores web comerciales o gestores de archivos gráficos independientes, Canaima ITE demuestra una eficiencia operativa excepcional, disminuyendo el costo cognitivo y optimizando los recursos del hardware anfitrión de forma sustentable.

