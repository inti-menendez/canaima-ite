# Guía de Compilación de Canaima ITE Paso a Paso

Este documento explica cómo preparar el entorno de desarrollo y compilar el proyecto usando nuitka paso a paso

### Requisitos Previos del Sistema (Linux)

Antes de tocar Python, el sistema operativo necesita herramientas de compilación de C y las librerías de desarrollo de GTK y VTE. En sistemas basados en Debian/Ubuntu (y derivados como Canaima), se instalan ejecutando:

```zsh
sudo apt update
sudo apt install build-essential gcc ccache python3-full libgirepository-2.0-dev gobject-introspection libcairo2-dev libvte-2.91-dev pkg-config patchelf

```

> **Nota técnica 1:** `libgirepository-2.0-dev` es **crítico**. Las versiones antiguas del sistema usaban `libgirepository1.0-dev`, pero en distros modernas (como Canaima Kavanayen) viene vacío y romperá la instalación de `pygobject` si no pones la versión 2.0.
> **Nota técnica 2:** `ccache` es opcional pero altamente recomendado; actúa como una caché para el compilador de C (`gcc`), haciendo que las futuras compilaciones con Nuitka sean hasta 10 veces más rápidas.

### Paso 1: crear un entorno virtual

dentro de la raiz de este proyecto preferiblemente vamos a crear un entorno virtual como parte de las buenas practicas para no ensuciar el sistema operativo y terminar con un ejecutable mucho mas limpio

```zsh
python3 -m venv .venv

```

inmediatamente despues de que se haya creado el entorno virtual lo activamos

```zsh
source .venv/bin/activate

```

para corroborar que estes dentro del .venv deberia salir en la linea de comandos, antes del nombre del usuario del @ y del nombre de la maquina algo como "(.venv)" esto indica que estamos dentro del entorno virtual y una vez alli podemos proceder

nos aseguramos de tener pip instalado (deberia estar si o si al haber instalado python-full) puedes probar el comando

```zsh
pip --version

```

### paso 2: instalar dependencias para poder usar gi sin problemas en el entorno

una vez seguros, actualizamos las herramientas críticas de empaquetado e instalamos las dependencias necesarias para compilar el puente hacia las librerías nativas de C de GNOME (GTK, VTE, etc.):

```zsh
pip install --upgrade pip wheel setuptools
pip install pycairo
pip install pygobject

```

> **OJO:** Si `pip install pygobject` te llega a dar un error de `girepository-2.0 not found`, asegúrate de que hiciste el `sudo apt install libgirepository-2.0-dev` del inicio. Si el error persiste, limpia la caché de pip corriendo: `pip install --no-cache-dir pygobject`.

### paso 3: instalar otras dependencias

entonces instalamos las dependencias que estan en requirements.txt, que son librerias que usaremos para el manejo de la ia, solicitudes, estandares de organizacion de ficheros, etc.

podemos hacerlo asi

```zsh
pip install -r requirements.txt

```

o asi

```zsh
pip install ollama openai platformdirs requests keyring

```

### paso 4: instalar compilador y algoritmo de compresion

una vez hecho esto instalamos nuitka que

**es un potente compilador de código Python a código C y C++**

usaremos nuitka en lugar de pyinstaller por lo que ofrece, pero tambien puedes usar pyinstaller para hacer pruebas rapidas, ya que nuitka es bastante lento.

entonces

```zsh
pip install nuitka

```

luego instalamos el algoritmo de compresion zstandard

```zsh
pip install zstandard

```

> **NOTA:** Si compilas con Nuitka usando únicamente la bandera `--onefile`, el compilador empaquetará los binarios en crudo. Para forzar la compresión del ejecutable final, el entorno virtual **debe contar obligatoriamente** con la librería `zstandard` (por eso la instalamos).

OJO si queremos hacerlo con pyinstaller entonces

```zsh
pip install pyinstaller

```

### paso 5: empaquetamos con nuitka o con pyinstaller

si seguimos el camino con nuitka, entonces ejecutamos el comando con optimización máxima en tiempo de enlazado (`--lto=yes`):

```zsh
python3 -m nuitka --standalone --onefile --include-data-dir=assets=assets --lto=yes main.py

```

explicacion de flags:

1. `--standalone`: Aísla las dependencias del sistema de archivos global.
2. `--onefile`: Unifica todo en un binario ELF ejecutable único.
3. `--include-data-dir=assets=assets`: Mapea e inyecta la carpeta de recursos estáticos en la raíz interna del binario.
4. `--lto=yes`: Habilita *Link Time Optimization*. El compilador le dice a `gcc` que optimice todo el código C generado como un bloque monolítico, reduciendo drásticamente el peso de las librerías de OpenAI y Ollama.

(este proceso tarda bastante pero gracias a `zstandard` y `lto` nos entrega un ejecutable de menos de 30mb)

Al terminar, se crearán carpetas temporales en la raíz del proyecto que podemos borrar sin problemas para recuperar gigas de espacio:

```zsh
rm -rf main.build main.dist main.onefile-build

```

Además va a crear el binario final en la raíz: `main.bin` -> ¡y listo!

con pyinstaller seria:

```zsh
pyinstaller --onefile --clean --add-data "assets:assets" main.py

```

y luego buscamos en la carpeta creada dist/ el archivo main y listo
(tarda mucho menos que nuitka pero nos entrega un ejecutable de 90-120mb)
este crea 2 carpetas en la raiz:
`build` (lo podemos borrar), y `dist`.
dentro de dist esta el ejecutable main. También crea el archivo `main.spec` en la raíz, el cual también se puede borrar sin dilema.

### paso 6: ejecutar

el hecho con nuitka
simplemente escribimos en la terminal (estando en la raíz del proyecto):

```zsh
./main.bin
```

y el hecho con pyinstaller:

```zsh
./dist/main
```