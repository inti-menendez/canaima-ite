#!/usr/bin/env bash

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BINARY_NAME="main.bin"
LAUNCHER_DIR="$HOME/.local/share/canaima-ite"
LAUNCHER_NAME="canaima-ite.desktop"

echo "===================================================="
echo "Iniciando proceso de compilación con Nuitka"
echo "===================================================="

echo "Limpiando compilaciones anteriores..."
rm -rf "$PROJECT_DIR/main.build" "$PROJECT_DIR/main.dist" "$PROJECT_DIR/main.onefile-build" "$PROJECT_DIR/$BINARY_NAME"


if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "No se detectó el entorno virtual .venv."
    echo "Por favor, crea el entorno e instala las dependencias antes de continuar."
    exit 1
fi

echo "Activando entorno virtual..."
source "$PROJECT_DIR/.venv/bin/activate"

if ! python3 -c "import zstandard" &> /dev/null; then
    echo "'zstandard' no detectado. Instalándolo para activar compresión..."
    pip install zstandard
fi

echo "Compilando con GCC y Nuitka..."
python3 -m nuitka --standalone --onefile --include-data-dir=assets=assets --nofollow-import-to=keyring.backends.macOS --nofollow-import-to=keyring.backends.Windows --nofollow-import-to=keyring.backends.chwallet --nofollow-import-to=pywin32 "$PROJECT_DIR/main.py"

echo "Compilación exitosa. Verificando tamaño final del ejecutable:"
du -sh "$PROJECT_DIR/$BINARY_NAME"

echo "Configurando el icono y acceso directo en el sistema..."
mkdir -p "$LAUNCHER_DIR"

cat <<EOF > "$LAUNCHER_DIR/$LAUNCHER_NAME"
[Desktop Entry]
Version=1.0
Type=Application
Name=Canaima ITE
Comment=Entorno de Terminal integrado con IA
Exec=$PROJECT_DIR/$BINARY_NAME
Icon=$PROJECT_DIR/assets/canaima-logo.png
Terminal=false
Categories=System;TerminalEmulator;
StartupNotify=true
EOF

chmod +x "$LAUNCHER_DIR/$LAUNCHER_NAME"

echo "Removiendo archivos temporales de código fuente en C..."
rm -rf "$PROJECT_DIR/main.build" "$PROJECT_DIR/main.dist"

echo "===================================================="
echo "PROCESO COMPLETADO"
echo "Aplicación disponible en el menú de inicio."
echo "===================================================="