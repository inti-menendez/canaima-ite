# Guía del Desarrollador (Developer Guide)

Bienvenido a la guía de desarrollo del proyecto. Este documento está diseñado para ayudarte a configurar tu entorno de desarrollo local, comprender la arquitectura de dependencias, y dominar las herramientas necesarias para contribuir al código de manera eficiente.

---

## 1. Requisitos del Sistema y Herramientas de Compilación

Para adentrarte en el desarrollo del proyecto en sistemas Linux (especialmente distribuciones basadas en Debian/Ubuntu como Canaima), necesitas instalar componentes esenciales que compilan extensiones nativas y proveen bindings de desarrollo para la interfaz gráfica.

Ejecuta el siguiente comando en tu terminal para preparar el sistema:


```zsh
sudo apt update
sudo apt install build-essential gcc ccache python3-full libgirepository-2.0-dev gobject-introspection libcairo2-dev libvte-2.91-dev pkg-config patchelf
```

### Notas de Arquitectura del Sistema

* **libgirepository-2.0-dev:** Es una dependencia crítica para la introspección de GNOME. En distribuciones modernas (como Canaima Kavanayen), el paquete heredado `libgirepository1.0-dev` viene vacío o descontinuado, lo que interrumpe la instalación de `pygobject`. Asegúrate de usar la versión 2.0.
* **ccache:** Esta herramienta actúa como un almacenamiento en caché para el compilador de C (`gcc`). Aunque es opcional, su presencia reduce radicalmente los tiempos de compilación sucesivos al reutilizar código que no ha cambiado.

---

## 2. Aislamiento del Entorno de Desarrollo

El desarrollo se debe realizar estrictamente dentro de un entorno virtual aislado para prevenir conflictos con los paquetes globales de la distribución y asegurar la consistencia del software.

### Creación y Activación del Entorno

Navega a la raíz del repositorio y ejecuta:

```zsh
python3 -m venv .venv
source .venv/bin/activate

```

Una vez activado, el prompt de tu terminal mostrará el prefijo `(.venv)`, indicando que cualquier comando de Python o Pip se ejecutará dentro de este espacio aislado.

Verifica que el gestor de paquetes esté listo:

```zsh
pip --version

```

---

## 3. Instalación de Dependencias de Desarrollo

El proceso de instalación de dependencias se divide en tres fases para mitigar errores de enlazado con las librerías del sistema operativo.

### Fase 1: Actualización de Core Tools y Bindings Gráficos

Primero, se actualizan las herramientas base de empaquetado y se construyen los puentes hacia las librerías nativas de C de GNOME (GTK, VTE, Cairo):

```zsh
pip install --upgrade pip wheel setuptools
pip install pycairo
pip install pygobject

```

> **Estrategia ante errores:** Si `pygobject` falla reportando que no encuentra `girepository-2.0`, reasigna la instalación del sistema operativo o fuerza una compilación limpia evadiendo la caché del gestor de paquetes:
> ```zsh
> pip install --no-cache-dir pygobject
> ``` 

### Fase 2: Librerías de la Aplicación (Ecosistema y Servicios)

Instala los paquetes necesarios para la lógica del negocio, que incluyen conectores de Inteligencia Artificial, peticiones de red, gestión de almacenamiento seguro de credenciales y directorios estándares del sistema:

```zsh
pip install -r requirements.txt

```
En caso de que prefieras realizar un seguimiento modular o una instalación manual, las librerías corresponden a:

```zsh
pip install ollama openai platformdirs requests keyring

```

### Fase 3: Tooling de Compilación y Distribución

Para generar los artefactos de distribución y ejecutables portables, se incorporan Nuitka, PyInstaller y el algoritmo de compresión nativa:

```zsh
pip install nuitka zstandard pyinstaller
```
> nota: pyinstaller no es necesario para empaquetar con nuitka, si deseas empaquetar con pyinstaller, obviamente si, de resto, no es necesario instalarlo, puedes ver mas sobre esto en el archivo guides/build-guide.md.

* **zstandard:** Es obligatorio en el entorno virtual si utilizas Nuitka. Sin esta librería, el compilador empaquetará los binarios en crudo sin aplicar el algoritmo de compresión final, lo que resultaría en un ejecutable de gran tamaño.

---

## 4. Flujo de Trabajo para Compilación y Pruebas

Como desarrollador, dispones de dos rutas para validar el empaquetado del software según la fase del ciclo de vida del desarrollo en la que te encuentres.

```
                  [Código Fuente (main.py)]
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
       [Ruta de Pruebas]            [Ruta de Producción]
         PyInstaller                      Nuitka
              │                             │
     • Compilación rápida          • Compilación estricta a C/C++
     • Binario más pesado          • Optimización LTO extrema
     • Ideal para iterar           • Ejecutable ultra-comprimido
              │                             │
              ▼                             ▼
         (./dist/main)                 (./main.bin)

```

### Ruta A: Iteración Rápida (Entorno de Pruebas con PyInstaller)

Recomendado durante la fase de desarrollo activo. La compilación toma pocos segundos a costa de generar un binario de mayor peso (entre 90MB y 120MB).

```zsh
pyinstaller --onefile --clean --add-data "assets:assets" main.py

```

* **Ejecución:** `./dist/main`
* **Limpieza de residuos:** Puedes eliminar la carpeta intermedia `build` y el archivo de configuración `main.spec` sin afectar al ejecutable dentro de `dist`.

### Ruta B: Compilación para Producción (Optimización Máxima con Nuitka)

Recomendado para la generación de releases oficiales. Nuitka traduce el código Python a C/C++ y lo compila a código de máquina nativo. Este proceso es demandante en tiempo y CPU, pero reduce el ejecutable final gracias al enlazado monolítico.

```zsh
python3 -m nuitka --standalone --onefile --include-data-dir=assets=assets --lto=yes main.py
```

#### Análisis de Parámetros de Compilación:

1. `--standalone`: Desvincula el binario de las librerías dinámicas globales del sistema de archivos, autoconteniendo sus dependencias.
2. `--onefile`: Compacta todo el ecosistema y dependencias internas en un único archivo binario ejecutable ELF.
3. `--include-data-dir=assets=assets`: Embebe de forma recursiva los recursos estáticos (imágenes, configuraciones, estilos) en la raíz del entorno virtual interno del binario.
4. `--lto=yes` (*Link Time Optimization*): Instruye al compilador `gcc` para optimizar todo el código generado como un único bloque monolítico, lo que permite descartar código muerto y optimizar drásticamente las dependencias pesadas de OpenAI y Ollama.

* **Ejecución:** `./main.bin`
* **Limpieza de espacio en desarrollo:** Al finalizar, el compilador deja huellas de compilación intermedias que ocupan gigabytes de espacio. Elimínalas con:
```zsh
rm -rf main.build main.dist main.onefile-build
```
para mas informacion leer la [guia de compilacion](guides/build-guide.md)

---

## 5. Lista de Verificación para Contribuciones (Checklist)

Antes de enviar un cambio o dar por finalizada una sesión de desarrollo, asegúrate de cumplir con los siguientes puntos:

* El código se ejecuta correctamente de manera local dentro del entorno virtual.
* No se han añadido nuevas dependencias a los módulos sin registrar el cambio correspondiente en el archivo `requirements.txt`.
* El directorio `assets/` se mantiene organizado y todos los recursos estáticos invocados en el código están ubicados en su interior.
* En caso de modificar configuraciones críticas del sistema operativo o dependencias de interfaz, se ha verificado que la compatibilidad con `libgirepository-2.0` no se vea comprometida.
