import os

HEADER = (
    '"""\nCanaima ITE - Entorno Integrado de Terminal\n'
    'Copyright (C) 2026 Inti Omar Menéndez Sánchez <intimenendez2004@gmail.com>\n"""\n\n'
)


def agregar_cabecera_a_archivos(directorio_objetivo):
    if not os.path.exists(directorio_objetivo):
        print(f"Error: La ruta '{directorio_objetivo}' no existe.")
        return

    contador_modificados = 0
    contador_omitidos = 0

    for raiz, carpetas, archivos in os.walk(directorio_objetivo):
        carpetas[:] = [d for d in carpetas if d not in (".venv", "__pycache__")]

        for archivo in archivos:
            if archivo.endswith(".py"):
                if archivo == os.path.basename(__file__):
                    continue

                ruta_completa = os.path.join(raiz, archivo)

                try:
                    with open(ruta_completa, "r", encoding="utf-8") as f:
                        contenido_original = f.read()
                    if (
                        "Canaima ITE - Entorno Integrado de Terminal"
                        in contenido_original
                    ):
                        print(f"[Omitido] Ya tiene cabecera: {ruta_completa}")
                        contador_omitidos += 1
                        continue

                    with open(ruta_completa, "w", encoding="utf-8") as f:
                        f.write(HEADER + contenido_original)

                    print(f"[Modificado] Cabecera añadida a: {ruta_completa}")
                    contador_modificados += 1

                except Exception as e:
                    print(f"[Error] No se pudo procesar {ruta_completa}: {e}")

    print("\n--- Resumen del proceso ---")
    print(f"Archivos modificados: {contador_modificados}")
    print(f"Archivos omitidos: {contador_omitidos}")


if __name__ == "__main__":
    carpeta_a_procesar = "."

    agregar_cabecera_a_archivos(carpeta_a_procesar)
