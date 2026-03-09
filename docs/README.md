PARCIAL 1 - SISTEMA DE MONITOREO AMBIENTAL

En este documento se encuentran todas las configuraciones principales que se tienen que hacer a los archivos para poder lograr su correcto funcionamiento.

## Conexiones del ESP32

Las conexiones van a estar estructuradas de la siguiente forma:
Pin del módulo -> Pin del ESP32

DHT11:
"+" -> 3V3
DATA -> P4
"-" -> GND

LDR:
VCC -> 3V3
DO -> P34
GND -> GND

RELAY:
VCC -> 5V
GND -> GND
IN -> P26

### Dependencias de Arduino

Antes de empezar a subir el código del ESP32, tenemos que verificar que tengamos las siguientes librerías instaladas en Arduino IDE:

PubSubClient by Nick O'Leary
DHT sensor library by Adafruit (con todo y dependencias)
ArduinoJson by Benoit Blanchon

### Configuración del ESP32

Aquí están los cambios que se tienen que hacer para cada ESP32.
Estos cambios van en el archivo nodo_esp32_adaptado.

#define NODE_ID "nodo1" <-- Cambiar el nombre para cada ESP32, puede tener cualquier nombre, pero tiene que ser uno diferente en caso de que se utilice más de uno
#define WIFI_SSID "WIFI" <-- Este es el nombre del wifi donde se va a probar todo el proyecto
#define WIFI_PASSWORD "Contraseña" <-- Acá va la contraseña del WIFI que se está utilizando
#define MQTT_SERVER "X.X.X.X" <-- Acá va la IP de la raspberry pi, más adelante se explica cómo obtener esta IP
#define MQTT_PORT 1883 <-- Este es el puerto de la raspberry

Luego de hacer esos cambios podemos verificar el código y proceder a subirlo al ESP32.

### Configuración del index

Estos son los cambios que se tienen que hacer al index.

Al inicio del proyecto se encuentra la siguiente línea:

const API_BASE = "http://192.168.100.240:3002";

La parte "192.168.100.240" es la IP de la raspberry pi a utilizar, podemos encontrar esta ip siguiendo los siguientes pasos:

1.Conectar la Raspberry Pi a una computadora a través de un cable Ethernet.
2.Ingresar el siguiente comando: "ping _nombre de la raspberry_ -4". Lo que hace este comando es que la raspberry responda a la computadora mostrando la IP de la computadora usando IPV4, por eso el -4.
El nombre de la raspberry por default es raspberry, entonces si tuvieramos una que no tiene ningún cambio el comando sería el siguiente: "ping raspberrypi -4".

### Configuración de la raspberry

Para empezar a configurar la raspberry tenemos que conectanos a ella, podemos lograr esto a través del cable ethernet que utilizamos para encontrar la ip de la misma.
Luego de tener la ip tenemos que ingresar los siguientes comandos para poder tener acceso a la raspberry:

ssh usuario@ip

El usuario por default es pi, y la ip es la misma que se encontró antes. Luego de ingresar ese comando nos pedirá la contraseña, la cual por default es raspberry.

Luego de hacer esto tenemos que instalar todas las dependencias para que funcione el proyecto:

1.Instalar mosquitto:
Para instalar mosquitto tenemos que ingresar los siguientes comandos:

sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

Y luego tenemos que verificar que ya esté activo, con el comando "sudo systemctl status mosquitto"

2.Instalar otras dependencias:
Para que el gateway pueda funcionar correctamente, tenemos que descargar algunas dependencias con el siguiente comando:

pip3 install flask flask-cors paho-mqtt

Si la raspberry no permite usar pip3, tenemos que usar los siguientes comandos:

sudo apt install python3-pip -y

Esto debe instalar pip para ya poder usar el comando anterior.

3.Creación de carpetas para el proyecto
Para que el proyecto funcione correctamente, tenemos que crear las carpetas para almacenar los scripts de la api y el gateway, como también los datos que van llegando del esp.
En este caso usamos 2 carpetas debido a que la raspberry utilizada es compartida

mkdir equipox
mkdir iot_data

La carpeta equipo 2 va a contener el script de la api y del gateway, y el iot_data va a contener los datos que se vayan guardando de los registros de los ESP32.

3.Pasar los archivos de la api y el gateway a la raspberry:
Para pasar los archivos tenemos que usar los siguientes comandos:

scp "...\gateway.py" pi@X.X.X.X:/home/raspberry/equipox/
scp "...\api.py" pi@X.X.X.X:/home/raspberry/equipox/

La primera sección es la ubicación del script en nuestra computadora, y la segunda parte es el usuario, ip y ubicación de donde queramos que esté el archivo

4.Iniciar los scripts:
Para iniciar los scripts, necesitamos ingresar a la terminal de la raspberry en dos terminales diferentes, y en cada una se tiene que poner uno de los siguientes comandos:

python3 /home/pi/equipox/gateway.py
python3 /home/pi/equipox/api.py

Ya teniendo esto los scripts deberían funcionar y ya podemos ver el proyecto funcional.
