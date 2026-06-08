# Manual de Usuario e Instalación - Canaima ITE

## 1. Introducción a Canaima ITE
   1.1. ¿Qué es Canaima ITE?
   1.2. Beneficios del asistente de IA
   1.3. Filosofía de Privacidad y Operación Local

## 2. Requisitos y Compatibilidad
   2.1. Plataformas Soportadas (Canaima GNU/Linux 8+, Debian GNU/Linux y Derivados)
   2.2. Requisitos de Hardware Mínimos y Recomendados (Hardware para Modelos Locales)

## 3. Guía de Instalación del Sistema y sus Entornos de IA
   3.1. Ejecución del Binario ELF Standalone
   3.2. Configuración de la Asistencia Local (Ollama)
        3.2.1. Instalación del Servicio Ollama mediante Script Oficial
        3.2.2. Gestión del Servicio del Sistema (Systemd)
        3.2.3. Descarga de Modelos de Lenguaje (Llama, Mistral, etc.)
   3.3. Configuración de Proveedores Remotos
        3.3.1. Obtención de Credenciales (Groq, OpenRouter, Cerebras)

## 4. Configuración Inicial de la Aplicación
   4.1. Primer Inicio de Canaima ITE
   4.2. Uso del Panel de Preferencias
   4.3. Vinculación de API Keys y Endpoints Personalizados bajo Estándar OpenAI

## 5. Manual de Operación de la Interfaz
   5.1. Gestión Avanzada de Terminales (Creación, Cierre y Navegación de Pestañas)
   5.2. Interacción con el Asistente de IA (Módulo Chat Bot)
   5.3. Navegación por el Sistema de Archivos desde el Panel Lateral
   5.4. Uso del Historial Centralizado y Búsqueda de Comandos
   5.5. Personalización Práctica de Atajos de Teclado

## 6. Flujos de Trabajo Avanzados y Casos de Uso
   6.1. Automatización de Comandos Complejos mediante Asistencia de IA
   6.2. Diagnóstico y Explicación Contextual de Errores en Terminal
   6.3. Configuración de Proveedores de IA Propios en Servidores Dedicados

## 7. Resolución de Problemas (Troubleshooting)
   7.1. El Servicio de Ollama no Responde (Validación de Sockets y Puertos)
   7.2. Fallos de Conectividad con Proveedores Online (Validación de API Keys)
   7.3. Conflictos con Atajos de Teclado Globales del Entorno de Escritorio

---

# Manual de Usuario e Instalación - Canaima ITE

## 1. Introducción a Canaima ITE

### 1.1. ¿Qué es Canaima Entorno Integrado de Terminal?

Canaima Entorno Integrado de Terminal (Canaima ITE) es una aplicación avanzada diseñada para transformar la experiencia de interactuar con la línea de comandos en sistemas operativos basados en Linux, con especial optimización para la distribución nacional Canaima GNU/Linux. Esta herramienta combina una consola multinivel de alto rendimiento con un ecosistema de paneles laterales orientados a simplificar el flujo de trabajo técnico y acelerar la curva de aprendizaje de sus usuarios.

### 1.2. Filosofía de Aislamiento y Enfoque Pedagógico

A diferencia de otras herramientas del mercado que automatizan acciones sin supervisión o actúan como agentes autónomos, Canaima ITE se fundamenta bajo un estricto principio pedagógico y de resguardo del sistema operativo:

* **Operación puramente reactiva:** El asistente de Inteligencia Artificial (IA) incorporado no tiene autonomía. No ejecuta comandos en segundo plano, no examina sus archivos de forma oculta ni monitorea las terminales abiertas de manera automatizada.
* **Tutoría conceptual:** El chatbot funciona exclusivamente como un panel de consulta teórica. Ante una duda introducida por el usuario, la IA responde explicando la lógica del comando, los parámetros necesarios y las mejores prácticas.
* **Aprendizaje activo:** Para aplicar cualquier solución propuesta por el asistente, usted deberá analizar la respuesta y escribir o pegar manualmente el comando en la terminal activa. Este flujo garantiza que el operador comprenda exactamente qué está haciendo en su sistema de archivos, promoviendo la soberanía cognitiva y la seguridad informática.

---

## 2. Requisitos y Compatibilidad

### 2.1. Plataformas Soportadas

* **Objetivo principal:** Canaima GNU/Linux 8 ("Kavanayén") o superior.
* **Compatibilidad genérica:** Distribuciones basadas en Debian GNU/Linux Stable (64 bits).

### 2.2. Requisitos de Hardware según el tipo de Asistencia

Canaima ITE es sumamente liviano en su núcleo operativo, requiriendo menos de 210 MB de memoria RAM para su ejecución gráfica completa. Sin embargo, el hardware anfitrión variará según el tipo de asistencia de lenguaje que decida utilizar:

| Componente | Uso con IA en la Nube (Remota) | Uso con IA Local (Ollama) |
| --- | --- | --- |
| **Procesador (CPU)** | Intel Core i3 / AMD Ryzen 3 o superior | Intel Core i5 / AMD Ryzen 5 (4 núcleos o más) |
| **Memoria RAM** | 4 GB mínimos disponibles | 8 GB mínimos (16 GB recomendados para modelos de 8B parámetros) |
| **Almacenamiento** | 50 MB de espacio libre en disco | 10 GB a 40 GB libres (según los modelos descargados) |
| **Conexión a Red** | Conexión constante a Internet | Completamente opcional (solo para descarga inicial) |

---

## 3. Guía de Instalación del Sistema y sus Entornos de IA

### 3.1. Ejecución de Canaima ITE

Canaima ITE se distribuye como un archivo binario único precompilado en formato ELF (de aproximadamente 27.9 MB), lo que elimina la necesidad de compilar código fuente o resolver dependencias complejas.

Para ejecutarlo por primera vez:

1. Otorgue permisos de ejecución al archivo binario desde la terminal:
```bash
chmod +x canaima-ite

```


2. Inicie la aplicación de forma gráfica o mediante la consola:
```bash
./canaima-ite

```



### 3.2. Configuración de la Asistencia Local (Ollama)

Si su objetivo es trabajar de forma 100 % privada, desconectado de internet o dentro de una red institucional restringida, debe aprovisionar el motor Ollama en su equipo local.

#### Paso 1: Instalación de Ollama

Abra una terminal tradicional y ejecute el instalador oficial para entornos Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh

```

#### Paso 2: Verificación del Servicio

Ollama se integra automáticamente como un servicio del sistema a través de Systemd. Verifique que esté operando en el puerto estándar (11434):

```bash
systemctl status ollama

```

#### Paso 3: Descarga de un Modelo Pedagógico

Debe descargar al menos un modelo de lenguaje para que el panel de Canaima ITE pueda recibir consultas. Se recomiendan modelos optimizados para codificación y comandos breves, como `llama3` o `mistral`:

```bash
ollama pull llama3

```

### 3.3. Configuración de Proveedores Remotos

Si su equipo cuenta con recursos limitados de hardware, puede optar por la asistencia online. Canaima ITE incluye soporte nativo preconfigurado para tres proveedores de alta velocidad: **Groq**, **OpenRouter** y **Cerebras**.

* Acceda a las plataformas oficiales del proveedor de su preferencia.
* Genere una llave de API (`API Key`) desde su panel de control de desarrollador.
* Copie la llave para su posterior introducción en Canaima ITE.

---

## 4. Configuración Inicial de la Aplicación

Al abrir Canaima ITE, diríjase al extremo inferior del Panel Lateral y haga clic en la pestaña de **Preferencias** (o presione el atajo de teclado asignado).

```text
+--------------------------------------------------------------+
| Preferencias de IA                                           |
|                                                              |
| Proveedor Activo: [ Ollama (Local) v ]                       |
| Modelo Seleccionado: [ llama3      v ]                       |
|                                                              |
| Clave de API (Online): [ ********************************* ] |
| Endpoint Personalizado: [ http://localhost:11434/v1        ] |
+--------------------------------------------------------------+

```

### 4.1. Activación de Ollama (Local)

1. En el menú desplegable "Proveedor Activo", seleccione **Ollama**.
2. En el campo "Modelo Seleccionado", asegúrese de escribir exactamente el nombre del modelo que descargó en su terminal (ej. `llama3` o `mistral`).
3. Guarde los cambios. El sistema apuntará directamente al socket de su máquina.

### 4.2. Activación de Proveedores Online

1. Seleccione **Groq**, **OpenRouter** o **Cerebras** en el menú desplegable.
2. Pegue la llave correspondiente en el campo "Clave de API".
3. Guarde las preferencias. A partir de ese momento, el chat interactivo se comunicará con las APIs remotas utilizando cifrado TLS estándar.

### 4.3. Servidores Propios y Endpoints Personalizados

Si en su institución educativa o de investigación disponen de un servidor centralizado con tarjetas gráficas dedicadas ejecutando modelos de IA, puede seleccionar la opción **Personalizado**. Introduzca la URL raíz de su servidor en el campo "Endpoint Personalizado", asegurándose de que cumpla con el estándar de peticiones de OpenAI.

---

## 5. Manual de Operación de la Interfaz

### 5.1. Gestión de Terminales y Pestañas

El área central de la aplicación es su espacio de trabajo de consola.

* **Nueva Pestaña:** Abre una sesión de shell completamente limpia e independiente. Cada pestaña hereda el entorno y los permisos del usuario que ejecutó el binario.
* **Cierre Seguro:** Al cerrar una pestaña, el sistema envía una señal de terminación limpia (`SIGTERM`) a todos los subprocesos que se estuvieran ejecutando dentro de esa sesión específica para evitar procesos huérfanos.

### 5.2. Uso del Chat Bot de Asistencia Técnica

El panel del Chat Bot es el único lugar donde interactúa la Inteligencia Artificial. Su uso es estrictamente interactivo:

1. Escriba su duda de forma natural en el cuadro de texto inferior (ej. *¿Cómo puedo buscar un archivo de texto modificado en las últimas 24 horas dentro de mi carpeta personal?*).
2. Presione Enviar. El asistente procesará la consulta y generará una respuesta didáctica en tiempo real.
3. El panel formateará los fragmentos de comandos dentro de bloques resaltados. Puede revisar la explicación teórica, copiar el comando sugerido e introducirlo en la terminal central para verificar su funcionamiento.

### 5.3. Navegación Visual y Gestión de Historial

* **Explorador Lateral:** Muestra un árbol gráfico del sistema de archivos. Permite hacer un seguimiento visual de las rutas donde está trabajando en la consola.
* **Historial de Sesión:** Centraliza y clasifica los comandos ejecutados por el usuario. Cuenta con un cuadro de búsqueda rápida para localizar rápidamente combinaciones de comandos complejas que se hayan utilizado con anterioridad, reduciendo la necesidad de memorizar largas sintaxis de parámetros.

---

## 6. Flujos de Trabajo Avanzados y Casos de Uso

### 6.1. Estudio y Desglose de Comandos Complejos mediante Asistencia de IA

El panel del Chat Bot está diseñado para actuar como un tutor de sintaxis interactivo. Cuando se enfrente a tuberías (pipelines) complejas o scripts de administración avanzados, puede utilizar el asistente para desglosar la lógica antes de ejecutarla en su terminal.

* **Caso de uso:** Comprensión de comandos de administración de discos y sistemas de archivos.
* **Flujo recomendado:**
1. El usuario introduce en el chat: *¿Qué hace exactamente el comando `find /var/log -type f -name "*.log" -mtime +30 -exec rm -f {} \;`?*
2. El asistente de IA responderá de forma didáctica desglosando cada argumento de la instrucción:
* `find /var/log`: Punto de inicio de la búsqueda.
* `-type f`: Filtra únicamente archivos regulares.
* `-name "*.log"`: Patrón de coincidencia para extensiones de registro.
* `-mtime +30`: Condición temporal (archivos modificados hace más de 30 días).
* `-exec rm -f {} \;`: Acción selectiva de depuración segura.


3. Tras comprender el riesgo y la utilidad de la instrucción, el usuario transcribe o adapta el comando en la pestaña activa de la terminal Vte.



### 6.2. Diagnóstico Didáctico de Errores de Consola

Canaima ITE promueve que el usuario entienda los fallos del sistema en lugar de ignorarlos. Dado que el sistema no captura de forma automática las salidas de la consola por razones de seguridad y aislamiento, el operador puede emplear el portapapeles como puente pedagógico.

* **Caso de uso:** Error de compilación o denegación de permisos en la ejecución de scripts.
* **Flujo recomendado:**
1. Si al ejecutar un comando en la terminal Vte se obtiene un volcado de error (como `stderr: Permission denied` o `pip: Command Not Found`), el usuario selecciona el texto del error y lo copia.
2. En el panel lateral del Chat Bot, introduce el texto acompañado de una petición de guía: *Obtuve este error en mi consola, ¿a qué se debe textualmente y cómo se soluciona conceptualmente?*
3. El asistente analizará el texto de forma reactiva y responderá explicando la causa raíz (ej. falta de privilegios en el espacio de usuario o ausencia de una variable en el PATH) y sugerirá la estructura correctiva correspondiente para que el usuario la aplique manualmente.



### 6.3. Despliegue de Modelos Educativos en Servidores Dedicados

Para entornos escolares, laboratorios universitarios de la UNEFA o dependencias del CNTI donde las estaciones de trabajo no dispongan de tarjetas gráficas dedicadas para procesar Ollama localmente, Canaima ITE permite centralizar la inteligencia.

* **Caso de uso:** Compartir un único modelo potente en una red local (LAN).
* **Flujo recomendado:**
1. El administrador del laboratorio instala Ollama en un servidor centralizado y configura la variable de entorno `OLLAMA_HOST=0.0.0.0` para escuchar peticiones en la red de la institución.
2. En las estaciones de trabajo de los estudiantes, se abre el panel de **Preferencias** de Canaima ITE.
3. Se selecciona el modo de proveedor **Personalizado** y en el campo "Endpoint" se apunta a la dirección IP del servidor central (ej. `http://192.168.1.50:11434/v1`).
4. Los estudiantes dispondrán de asistencia interactiva inmediata sin consumir ciclos de CPU ni memoria RAM local de sus estaciones de trabajo.

---

## 7. Resolución de Problemas (Troubleshooting)

### 7.1. El Servicio de Ollama no Responde (Validación de Sockets)

* **Síntoma:** El Chat Bot muestra un mensaje de error crítico indicando que no puede establecer conexión con el host local o el puerto 11434.
* **Causa:** El demonio de Ollama no se ha inicializado correctamente a través del gestor de servicios del sistema operativo.
* **Procedimiento de corrección:**
1. En una pestaña de terminal de Canaima ITE, invoque el estado del servicio:
```bash
systemctl status ollama

```


2. Si el servicio se encuentra en estado `inactive` o `failed`, reinícielo utilizando privilegios de administrador:
```bash
sudo systemctl restart ollama

```


3. Verifique manualmente la escucha del puerto local mediante el uso de `curl`:
```bash
curl http://localhost:11434

```


La consola debe retornar textualmente la cadena: *Ollama is running*.



### 7.2. Fallos de Autenticación y Límites de Tasa con Proveedores Online

* **Síntoma:** El asistente no genera texto y el panel lateral refleja códigos de error HTTP 401 (Unauthorized) o 429 (Too Many Requests).
* **Causa:** La clave de API ingresada en el panel de preferencias posee caracteres incorrectos, ha sido revocada desde el panel del proveedor, o se ha excedido la cuota gratuita de tokens asignada a su cuenta.
* **Procedimiento de corrección:**
1. Ingrese a la consola web del proveedor seleccionado (Groq, OpenRouter o Cerebras).
2. Revoque la llave anterior y genere una cadena de credenciales completamente nueva.
3. Acceda al panel de **Preferencias** de Canaima ITE, limpie el campo de texto anterior y pegue la nueva llave.
4. Asegúrese de hacer clic en **Guardar Cambios** para forzar al motor `ConfigEngine` a refrescar las variables de entorno en memoria.



### 7.3. Conflictos con Atajos de Teclado Globales del Entorno de Escritorio

* **Síntoma:** Al presionar una combinación de teclas configurada en Canaima ITE para alternar paneles o abrir pestañas, la aplicación no reacciona y en su lugar se ejecuta una acción del sistema operativo (como ocultar ventanas o abrir el menú de Canaima).
* **Causa:** Los entornos de escritorio (XFCE, MATE o GNOME) poseen mapas de teclado globales con mayor jerarquía de captura que las ventanas de usuario de GTK 3.
* **Procedimiento de corrección:**
1. Identifique cuál es el atajo en conflicto.
2. Diríjase al panel lateral de **Atajos de Teclado** de Canaima ITE.
3. Haga clic sobre la acción que desea remapear y presione una nueva combinación que incluya modificadores secundarios (como `Ctrl + Shift` o `Ctrl + Alt`).
4. Alternativamente, puede acceder a la configuración de teclado nativa de su entorno de escritorio y deshabilitar el atajo global que interfiere con la aplicación técnica.

---