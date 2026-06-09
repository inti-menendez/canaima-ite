#!/bin/bash
# ==============================================================================
# Script de Despliegue Local Automático de la SPA de Documentación
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
PUERTO=8080

if [ ! -d "${DOCS_DIR}" ]; then
    echo "ERROR: No se encuentra la carpeta 'docs' en ${DOCS_DIR}"
    exit 1
fi

cd "${DOCS_DIR}"

echo "Iniciando servidor local de documentación offline..."

python3 -m http.server ${PUERTO} > /dev/null 2>&1 &
SERVIDOR_PID=$!

proc_exit() {
    echo -e "\nApagando servidor de documentación (PID: ${SERVIDOR_PID})..."
    kill ${SERVIDOR_PID} 2>/dev/null
    exit 0
}
trap proc_exit SIGINT SIGTERM

sleep 1

echo "Abriendo el navegador web en http://localhost:${PUERTO}..."
xdg-open "http://localhost:${PUERTO}"

echo "------------------------------------------------------------------------"
echo "Servidor activo ejecutándose en segundo plano."
echo "Presione [Ctrl + C] en esta terminal para detener el servicio."
echo "------------------------------------------------------------------------"

wait ${SERVIDOR_PID}