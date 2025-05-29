# Aplicación de Envío Automatizado para WhatsApp

## Descripción General
Esta aplicación permite automatizar el envío de mensajes de WhatsApp a múltiples contactos a través de un archivo Excel. Utiliza Selenium para interactuar con WhatsApp Web en un entorno Flask. Está diseñada para ser desplegada en un contenedor LXC en Proxmox VE.

## Características Principales
*   Envío masivo de mensajes de WhatsApp desde un archivo Excel.
*   Interfaz web para subir el archivo de contactos y gestionar el proceso.
*   Autenticación básica para proteger el acceso.
*   Visualización de logs en tiempo real.
*   Tiempos de espera aleatorios entre mensajes para simular comportamiento humano.
*   Pausas programadas durante envíos largos.
*   Límite de mensajes por hora configurable para evitar bloqueos.
*   Persistencia de sesión de WhatsApp Web para minimizar la necesidad de escanear códigos QR repetidamente.
*   Despliegue sencillo mediante script de instalación y servicio systemd.

## Arquitectura y Tecnologías
*   **Backend:** Python 3 + Flask
*   **Frontend:** HTML, CSS, JavaScript (para actualizaciones dinámicas)
*   **Automatización:** Selenium con WebDriver para Firefox (GeckoDriver)
*   **Procesamiento de Datos:** Pandas (para leer archivos Excel)
*   **Entorno de Ejecución:** XVFB (X Virtual FrameBuffer) para ejecutar Firefox en modo headless.
*   **Persistencia de Datos:**
    *   Logs de aplicación: Archivos de texto (`logs/app.log`).
    *   Sesión de Selenium/WhatsApp Web: Archivos en el directorio `sessions/default` para mantener la sesión de WhatsApp Web activa.
    *   Archivos subidos: Almacenados temporalmente en `uploads/`.
*   **Contenedorización (Recomendada):** LXC en Proxmox VE con Ubuntu 22.04.

## Requisitos Previos
*   Proxmox VE instalado y funcionando.
*   Plantilla (template) de Ubuntu 22.04 LXC descargada en Proxmox. (Ej: `ubuntu-22.04-standard_22.04-1_amd64.tar.gz`)
*   Conocimientos básicos de línea de comandos Linux.
*   Un número de teléfono activo para WhatsApp que se usará para enviar los mensajes.
*   Navegador web moderno (Chrome, Firefox) para acceder a la interfaz de la aplicación.

## Instalación Paso a Paso

### Paso 1: Crear el Contenedor LXC en Proxmox
1.  Accede a tu servidor Proxmox VE.
2.  Usa la consola de Proxmox (shell) o SSH para crear el contenedor. Ajusta los parámetros según tus necesidades (ID, nombre de la plantilla, almacenamiento, etc.).
    ```bash
    pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz \
        --hostname whatsapp-sender-lxc \
        --storage local-lvm \
        --cores 2 \
        --memory 2048 \
        --swap 512 \
        --net0 name=eth0,bridge=vmbr0,ip=dhcp \
        --onboot 1 # Opcional: para que inicie con Proxmox
    ```
    *   `100`: ID del contenedor (elige uno disponible).
    *   `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz`: Ruta a tu plantilla de Ubuntu 22.04.
    *   `local-lvm`: Nombre de tu almacenamiento.
    *   Ajusta `cores`, `memory`, `swap` según tus recursos.
    *   `vmbr0`: Tu bridge de red principal en Proxmox. `ip=dhcp` para obtener IP automáticamente.
3.  Una vez creado, inicia el contenedor desde la interfaz de Proxmox o con `pct start 100`.
4.  Obtén la dirección IP del contenedor (puedes verla en la interfaz de Proxmox o usando `pct exec 100 ip a` después de que inicie).
5.  Accede a la consola del contenedor:
    *   Desde la interfaz de Proxmox: Selecciona el LXC > Console.
    *   O usa `pct enter 100` en la shell de Proxmox.

### Paso 2: Configurar el Contenedor LXC
1.  **Ingresa a la consola del LXC.**
2.  **Clona el repositorio del proyecto:**
    Reemplaza `<URL_DEL_REPO>` con la URL real del repositorio Git.
    ```bash
    apt update && apt install -y git # Instalar git si no está
    git clone <URL_DEL_REPO> /opt/whatsapp-sender
    ```
3.  **Navega al directorio del proyecto:**
    ```bash
    cd /opt/whatsapp-sender
    ```
4.  **Ejecuta el script de instalación:**
    Este script (`install.sh`) se encargará de:
    *   Actualizar los paquetes del sistema.
    *   Instalar Python3, pip, `python3-venv`, Firefox (ESR descargado manualmente), XVFB y wget.
    *   Descargar e instalar la última versión de GeckoDriver (el WebDriver para Firefox).
    *   Crear un entorno virtual de Python en `/opt/whatsapp-sender/venv`.
    *   Instalar las dependencias de Python listadas en `requirements.txt` dentro de este entorno virtual.
    *   Crear los directorios necesarios para la aplicación (`app`, `uploads`, `sessions`, `logs`) dentro de `/opt/whatsapp-sender/`.
    ```bash
    sudo bash ./install.sh
    ```

### Paso 3: Configurar la Aplicación
1.  **Credenciales de Autenticación:**
    *   Las credenciales de autenticación básica se encuentran en `/opt/whatsapp-sender/app/app.py`.
    *   Busca las variables `BASIC_AUTH_USERNAME` y `BASIC_AUTH_PASSWORD`.
    *   **Se recomienda encarecidamente cambiar la contraseña por defecto (`changeme`)** por una más segura.
2.  **Variables de Envío de Mensajes:**
    *   En el mismo archivo `/opt/whatsapp-sender/app/app.py`, puedes ajustar las siguientes variables para controlar el comportamiento del envío:
        *   `MIN_WAIT_SECONDS`: Tiempo mínimo de espera (en segundos) entre mensajes.
        *   `MAX_WAIT_SECONDS`: Tiempo máximo de espera (en segundos) entre mensajes.
        *   `MESSAGES_BEFORE_PAUSE`: Número de mensajes a enviar antes de una pausa larga.
        *   `PAUSE_DURATION_SECONDS`: Duración de la pausa larga (en segundos).
        *   `HOURLY_MESSAGE_LIMIT`: Límite máximo de mensajes a enviar por hora.
    *   Ajusta estos valores con precaución para evitar ser marcado como spam por WhatsApp.

### Paso 4: Iniciar la Aplicación
Puedes iniciar la aplicación manualmente para pruebas o configurarla como un servicio systemd para producción y autoarranque.

*   **Manualmente (para pruebas):**
    1.  Asegúrate de estar en el directorio `/opt/whatsapp-sender/`.
    2.  Para ejecutar manualmente, puedes activar el entorno virtual primero o invocar directamente el intérprete de Python del entorno virtual:
        ```bash
        # Opción 1: Activar el entorno virtual (recomendado para desarrollo o pruebas interactivas)
        # source venv/bin/activate
        # xvfb-run -a python3 app/app.py --host 0.0.0.0 --port 5000
        # deactivate # (cuando termines)

        # Opción 2: Invocar directamente el Python del venv (más similar a cómo lo hace systemd)
        sudo xvfb-run -a /opt/whatsapp-sender/venv/bin/python3 app/app.py --host 0.0.0.0 --port 5000
        ```
        *   `xvfb-run -a`: Es necesario porque Selenium usa Firefox, y XVFB (X Virtual FrameBuffer) permite ejecutar aplicaciones gráficas sin una pantalla física (headless).
        *   La aplicación estará disponible en la IP del LXC, puerto 5000.
        *   Los logs se mostrarán en la consola y se guardarán en `logs/app.log`.

*   **Usando Systemd (para producción y autoarranque):**
    1.  **Copia el archivo de servicio:**
        El archivo `whatsapp-sender.service` (incluido en el repositorio) define cómo systemd debe gestionar la aplicación y ya está configurado para usar el intérprete de Python del entorno virtual.
        ```bash
        sudo cp /opt/whatsapp-sender/whatsapp-sender.service /etc/systemd/system/
        ```
    2.  **Recarga la configuración de systemd:**
        ```bash
        sudo systemctl daemon-reload
        ```
    3.  **Habilita el servicio para que inicie en el arranque del sistema:**
        ```bash
        sudo systemctl enable whatsapp-sender.service
        ```
    4.  **Inicia el servicio:**
        ```bash
        sudo systemctl start whatsapp-sender.service
        ```
    5.  **Verifica el estado del servicio:**
        ```bash
        sudo systemctl status whatsapp-sender.service
        ```
        Deberías ver un estado "active (running)".
    6.  **Para ver los logs del servicio en tiempo real:**
        ```bash
        sudo journalctl -u whatsapp-sender.service -f
        ```
        Presiona `Ctrl+C` para salir.

### Paso 5: Acceder a la Aplicación Web
1.  Abre un navegador web en tu computadora (que esté en la misma red que el contenedor LXC).
2.  Navega a `http://<IP-DEL-CONTENEDOR-LXC>:5000`. Reemplaza `<IP-DEL-CONTENEDOR-LXC>` con la dirección IP real de tu contenedor.
3.  Se te pedirá autenticación. Usa las credenciales que configuraste en `app/app.py` (o las por defecto si no las cambiaste).

### Paso 6: Reglas de Firewall (Opcional pero Recomendado)
Si tienes un firewall como `ufw` activo en tu servidor Proxmox o directamente en el contenedor LXC, necesitas permitir el tráfico entrante al puerto 5000/TCP desde tu red local.

*   **Ejemplo con `ufw` (ejecutar en el host Proxmox o en el LXC, donde el firewall esté activo):**
    Reemplaza `<TU_RED_LOCAL_CIDR>` con el rango de tu red local (ej: `192.168.1.0/24`).
    ```bash
    sudo ufw allow from <TU_RED_LOCAL_CIDR> to any port 5000 proto tcp
    ```
    Si `ufw` está en el LXC, un simple `sudo ufw allow 5000/tcp` podría ser suficiente.

## Uso de la Aplicación
1.  **Autenticación:** Ingresa tus credenciales al acceder a la página.
2.  **Subir Archivo Excel:**
    *   Prepara un archivo Excel (`.xls` o `.xlsx`).
    *   El archivo debe tener al menos dos columnas: una llamada `PhoneNumber` (con los números de teléfono) y otra llamada `Message` (con los mensajes a enviar).
    *   Haz clic en "Seleccionar archivo", elige tu archivo Excel y haz clic en "Upload and Preview".
3.  **Previsualización de Contactos:**
    *   Se mostrará una vista previa de los primeros 10 contactos del archivo.
    *   Verifica que los números y mensajes sean correctos.
4.  **Iniciar el Envío de Mensajes:**
    *   Si la vista previa es correcta, haz clic en el botón "Start Sending Messages".
    *   El proceso de envío comenzará en segundo plano en el servidor.
5.  **Monitorear Logs:**
    *   Puedes ver el progreso y posibles errores en la sección "Logs" de la interfaz web. Los logs se actualizan automáticamente.
    *   También puedes revisar el archivo `logs/app.log` directamente en el servidor.
    *   Si usas systemd, `sudo journalctl -u whatsapp-sender.service -f` también te mostrará los logs.
6.  **Importante sobre WhatsApp Web y Código QR:**
    *   **Escaneo Inicial:** La primera vez que la aplicación (a través de Selenium) intente conectarse a WhatsApp Web utilizando un perfil de Firefox nuevo (almacenado en `sessions/default`), o si la sesión de WhatsApp Web ha expirado, se requerirá escanear un código QR.
    *   **Detección de QR:** La aplicación intentará detectar si se necesita un código QR al iniciar el proceso de envío. Si es así, mostrará un mensaje flash en la interfaz web y registrará una advertencia en los logs.
    *   **Proceso de Escaneo:**
        *   Dado que Firefox se ejecuta en modo "headless" (sin interfaz gráfica visible) dentro del contenedor, no verás directamente la ventana del navegador para escanear.
        *   Si la aplicación indica que se necesita un escaneo QR, y es la primera vez o la sesión expiró:
            1.  El proceso de envío se detendrá para permitir el escaneo.
            2.  **Temporalmente**, para poder escanear el QR, podrías necesitar:
                *   Detener el servicio systemd (`sudo systemctl stop whatsapp-sender.service`).
                *   Ejecutar la aplicación manualmente **quitando la opción `-headless`** de la línea `options.add_argument("-headless")` en la función `init_driver` dentro de `app/app.py`.
                *   Configurar X11 forwarding o instalar un entorno de escritorio ligero y VNC en el LXC para ver la instancia de Firefox que Selenium abre. Esto es avanzado y puede ser complejo.
                *   **Alternativa más simple (si el headless no coopera para el QR):** Comentar temporalmente `options.add_argument("-headless")` en `app/app.py`, reiniciar la app (manual o systemd), y luego usar `sudo xvfb-run --server-args="-screen 0 1024x768x24" python3 app/app.py ...`. De esta forma, aunque no veas la UI, el QR podría generarse y persistir en la sesión. Luego, puedes intentar acceder a WhatsApp Web desde un navegador normal en tu PC usando el mismo perfil de Firefox (copiando la carpeta `sessions/default`) para escanear el QR. Esta es una solución muy manual.
            3.  **La forma más directa es asegurar que la sesión se establezca:** Una vez que la aplicación (con Firefox visible si modificaste el modo headless) muestre el QR, escanéalo con la aplicación WhatsApp de tu teléfono.
        *   **Persistencia de Sesión:** Una vez que hayas escaneado el código QR exitosamente, Selenium guardará la información de la sesión en el directorio `sessions/default` dentro de `/opt/whatsapp-sender/`. En los siguientes inicios, la aplicación debería usar esta sesión guardada, evitando la necesidad de escanear el QR nuevamente, a menos que la sesión expire o WhatsApp la invalide.
        *   Si la aplicación sigue pidiendo QR, asegúrate de que los permisos de la carpeta `sessions/default` permitan a Selenium escribir en ella.

## Estructura del Proyecto
*   `app/`: Contiene el código fuente de la aplicación Flask.
    *   `app.py`: Archivo principal de la aplicación Flask (rutas, lógica de negocio).
    *   `templates/`: Contiene las plantillas HTML para la interfaz web.
    *   `static/`: Contiene archivos estáticos (CSS, JavaScript del lado del cliente).
*   `uploads/`: Directorio donde se almacenan temporalmente los archivos Excel subidos.
*   `sessions/`: Directorio utilizado por Selenium para guardar datos de sesión del navegador (ej., `sessions/default` para el perfil de Firefox, ayudando a mantener la sesión de WhatsApp Web).
*   `logs/`: Contiene los archivos de log de la aplicación (ej., `logs/app.log`).
*   `.gitignore`: Especifica los archivos y directorios que Git debe ignorar.
*   `install.sh`: Script para automatizar la instalación de dependencias y configuración inicial en el LXC.
*   `requirements.txt`: Lista las dependencias de Python necesarias para el proyecto.
*   `whatsapp-sender.service`: Archivo de definición del servicio systemd para gestionar la aplicación.
*   `README.md`: Este archivo de documentación.

## Medidas Anti-Baneo (Resumen)
La aplicación incluye varias características para minimizar el riesgo de que WhatsApp bloquee el número utilizado para enviar mensajes:
*   **Tiempos de Espera Aleatorios:** Se introducen pausas de duración variable entre el envío de cada mensaje.
*   **Límite de Mensajes por Hora:** Se puede configurar un número máximo de mensajes a enviar en una hora.
*   **Pausas Programadas Largas:** Después de un cierto número de mensajes enviados, la aplicación realiza una pausa más extensa.
*   **Recomendaciones Adicionales:**
    *   Utiliza un número de teléfono de prueba o uno dedicado para estos envíos masivos, especialmente al principio.
    *   No envíes grandes volúmenes de mensajes a números desconocidos o que no hayan consentido recibirlos.
    *   Aumenta gradualmente el volumen de envío.
    *   Evita enviar el mismo mensaje exacto a todos los contactos; personaliza cuando sea posible (la app actualmente envía el mensaje tal como está en el Excel).
    *   Monitorea la cuenta de WhatsApp asociada para cualquier advertencia.

## Resolución de Problemas Comunes (FAQ Básico)
*   **Error "GeckoDriver executable needs to be in PATH" o similar:**
    *   Asegúrate de que el script `install.sh` se haya ejecutado completamente y sin errores. Este script descarga e instala GeckoDriver en `/usr/local/bin`.
    *   Verifica que `/usr/local/bin` esté en el PATH del usuario que ejecuta la aplicación.
*   **La aplicación no inicia o el servicio systemd falla:**
    *   Revisa los logs del servicio: `sudo journalctl -u whatsapp-sender.service -f`.
    *   Revisa los logs de la aplicación: `/opt/whatsapp-sender/logs/app.log`.
    *   Asegúrate de que todos los comandos en `install.sh` se ejecutaron correctamente y que las dependencias están instaladas.
    *   Verifica que Firefox esté instalado (`firefox --version`).
*   **Problemas con el escaneo del Código QR / Pide QR constantemente:**
    *   **Persistencia de Sesión:** La sesión de WhatsApp Web se guarda en `/opt/whatsapp-sender/sessions/default`. Asegúrate de que este directorio exista y tenga permisos de escritura para el usuario que ejecuta la aplicación Flask/Selenium.
    *   **Sesión Inválida:** La sesión de WhatsApp Web puede expirar o ser invalidada por WhatsApp. Si esto sucede, se requerirá un nuevo escaneo.
    *   **Múltiples Instancias:** No ejecutes múltiples instancias de la aplicación utilizando el mismo directorio de sesión (`sessions/default`) simultáneamente, ya que esto corromper la sesión. Si WhatsApp Web está abierto en otro navegador con el mismo perfil, puede causar conflictos.
    *   **Headless y QR:** Escanear un QR con un navegador headless es problemático. Si tienes problemas persistentes, consulta la sección "Importante sobre WhatsApp Web y Código QR" para obtener consejos sobre cómo manejar el escaneo inicial.

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un "issue" para discutir cambios mayores o envía un "pull request" con tus mejoras.

## Licencia
Este proyecto se distribuye bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles (Nota: Archivo `LICENSE` no incluido aún, se puede añadir si es necesario).