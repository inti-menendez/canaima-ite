# Manual de usuario para la obtencion de api keys
Esta guía detalla el procedimiento paso a paso para la obtención de las claves de API (API Keys) de los tres proveedores en la nube soportados de forma nativa por Canaima ITE.

---

## 1. Guía para OpenRouter

OpenRouter actúa como un agregador de modelos que permite acceder a una gran variedad de arquitecturas de código abierto (como Llama 3, Mistral o Qwen) mediante un único punto de acceso.

* **URL Oficial:** [https://openrouter.ai/](https://openrouter.ai/)

### Paso a paso:

1. Ingrese a la plataforma oficial y haga clic en **Sign In** (Iniciar sesión) en la esquina superior derecha. Puede registrarse usando una cuenta de Google, GitHub o mediante un correo electrónico convencional.
2. Una vez dentro de la interfaz, haga clic en el icono de su perfil o directamente acceda al panel de control de claves desde el menú lateral seleccionando **Keys** (Claves), o ingrese directamente a `https://openrouter.ai/keys`.
3. Haga clic en el botón **new Key** (Crear clave).
4. El sistema le solicitará asignarle un nombre identificativo a la clave (por ejemplo: `Canaima-ITE`). Opcionalmente, puede definir un límite de presupuesto para esa clave para evitar consumos imprevistos.
5. Haga clic en **Create**. La plataforma desplegará la clave generada en una ventana emergente.
6. Copie la clave inmediatamente y resguárdela. Por razones de seguridad, OpenRouter no volverá a mostrar esta cadena de texto.

> nota: este proveedor tiene la genialidad del "modelo" **openrouter/free** que estrictamente hablando no es un modelo, pero ofrece una puerta a modelos puramente gratuitos automaticamente, y es el usado por defecto por Canaima ITE.

---

## 2. Guía para Groq

Groq destaca por su arquitectura de hardware especializada (LPU), la cual ofrece velocidades de inferencia extremadamente altas para modelos de código abierto optimizados.

* **URL Oficial:** [https://console.groq.com/](https://console.groq.com/)

### Paso a paso:

1. Ingrese a la consola de Groq. Si no posee una cuenta, haga clic en **Sign Up** para registrarse.
2. Al iniciar sesión, el sistema lo redirigirá de forma automática al panel de control principal (Groq Console).
3. En el menú de navegación superior, localice y haga clic sobre la opción **API Keys**.
4. En el panel central, presione el botón **Create API Key**.
5. Introduzca un nombre descriptivo para la credencial y haga clic en **Submit** o **Create**.
6. Aparecerá un cuadro de diálogo con la llave generada (comienza habitualmente con el prefijo `gsk_`). Copie el texto completo utilizando el botón de copiado rápido y guárdelo de forma segura antes de cerrar la ventana.

---

## 3. Guía para Cerebras

Cerebras proporciona acceso de ultra-baja latencia a modelos de la serie Llama utilizando su arquitectura de chip a escala de oblea (WSE), ideal para respuestas en streaming casi instantáneas.

* **URL Oficial:** [https://cloud.cerebras.ai/](https://cloud.cerebras.ai/)

### Paso a paso:

1. Diríjase a la plataforma de Cerebras Cloud. Si es su primera visita, cree una cuenta haciendo clic en **Sign Up** y complete el proceso de verificación de correo electrónico.
2. Inicie sesión para acceder a la consola de desarrollador de Cerebras.
3. En la barra de herramientas lateral, busque la sección etiquetada como **API Keys** (también accesible desde el menú de configuración de su espacio de trabajo).
4. Haga clic en el botón **Generate api Key** (o **Create New Secret Key**).
5. Asigne una etiqueta a la credencial para llevar un control de auditoría interno.
6. El sistema generará la clave única. Haga clic en el botón de copiar. Asegúrese de almacenarla en su configuración local de inmediato, ya que el portal bloqueará la visualización del texto tras salir de esa sección.

---

> ### Nota Crítica de Seguridad para el Usuario
> 
> 
> Las claves de API son equivalentes a contraseñas de acceso directo a recursos de cómputo. No las comparta en repositorios públicos de código fuente (como GitHub o GitLab), no las exponga en capturas de pantalla de sus informes técnicos ni las comparta por canales de mensajería no cifrados. Canaima ITE almacena estas cadenas localmente de forma exclusiva en el wallet de credenciales nativo del sistema operativo y solo las utiliza para levantar el flujo de streaming solicitado por el componente del chatbot.