#!/usr/bin/env python3

"""Gateway IoT - Raspberry Pi Zero W - Proyecto Parcial 1"""

import paho.mqtt.client as mqtt
import json, os, time, statistics
from datetime import datetime
from collections import defaultdict

# CONFIGURACIÓN
MQTT_BROKER     = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT       = 1883
MQTT_TOPIC  = "iot/ambiente/#"  
MQTT_KEEPALIVE  = 60
DATA_FILE       = os.environ.get("DATA_FILE", "/home/marco/iot_data/sensor_data_eq2.json") # os.environ.get("DATA_FILE", "/data/sensor_data.json") para el docker
MAX_REGISTROS   = 1000

#Esto es para crear el json en la ubicación si es que no existe
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f: json.dump([], f)

buffer_dispositivos = defaultdict(list)
estadisticas = {'mensajes_recibidos': 0, 'inicio': time.time()}

# Esta parte es nada más para cargar y guardar el json
def cargarJSON():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except:
        return []

def guardarJSON(datos): #Como el nombre lo dice, esto es para guardar el json, y solo mantiene los últimos 1000 registros para no saturar la memoria
    if len(datos) > MAX_REGISTROS:
        datos = datos[-MAX_REGISTROS:]
    with open(DATA_FILE, "w") as f: #Esto es nada más para que se pueda leer bien en caso de que quieran abrir el json, que lo dudo
        json.dump(datos, f, indent=2)

# MQTT CALLBACKS
# Parte para recibir los datos del esp y que se guarden en el json, para luego imprimirlos
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Conectado a {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Suscrito a: {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Error de conexión. Status: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Desconectado")

#Esta parte es para cada vez que llega un mensaje.
def on_message(client, userdata, msg):
    try:
        print(f"[MQTT] Mensaje recibido en {msg.topic}")

        #Esto es para poder leer el json
        datos = json.loads(msg.payload.decode("utf-8"))

        # Acá se checa que todos los campos estén en el json que pasaron
        campos_requeridos = ["nodo", "temperatura", "humedad", "luz"]
        for campo in campos_requeridos:
            if campo not in datos:
                print(f"[MQTT] No están todos los campos. Falta: '{campo}'")
                return

        #Esto es para poder guardar los datos que pasaron en el json de los datos
        lectura = {
            'nodo':        datos["nodo"],
            'temperatura': round(float(datos["temperatura"]), 1),
            'humedad':     round(float(datos["humedad"]), 1),
            'luz':         round(float(datos["luz"]), 0),
            'relay':       int(datos.get("relay", 0)),
            'timestamp':   datetime.now().isoformat()
        }

        # Esto es para guardar los datos en el json
        guardados = cargarJSON()
        guardados.append(lectura)
        guardarJSON(guardados)

        #Añade 1 al counter de los mensajes recibidos, y pasa los datos que recibió con todo y la hora (porque el proyecto pide la hora exacta)
        estadisticas['mensajes_recibidos'] += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {lectura['nodo']}: "
              f"T={lectura['temperatura']}°C  "
              f"H={lectura['humedad']}%  "
              f"L={lectura['luz']}%")

    except Exception as e:
        print(f"[Error] No se pudo procesar el mensaje: {e}")

#Esto es para imprimir los datos en la terminal
if __name__ == '__main__':
    print("=" * 70)
    print("  Gateway IoT - Raspberry Pi Zero W")
    print("=" * 70)
    print(f"  Broker:  {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Topic:   {MQTT_TOPIC}")
    print(f"  Archivo: {DATA_FILE}")
    print("=" * 70)

    # Acá se crea el cliente y qué hace en cada caso
    client = mqtt.Client(client_id="gateway_rpi")
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    #Esto es para que reintente volverse a conectar en caso de que se desconecte
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            client.loop_forever()  #Esto es para que siempre que esté conectado se mantenga la conexión
        except Exception as e:
            print(f"[Error] {e} - reintentando en 5 segundos")
            time.sleep(5)
