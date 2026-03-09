#!/usr/bin/env python3
"""API REST - Proyecto Parcial 1"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from collections import defaultdict
import time, json, os, statistics
import paho.mqtt.client as mqtt

app = Flask(__name__)
CORS(app)

DATA_FILE    = os.environ.get("DATA_FILE", "/home/marco/iot_data/sensor_data_eq2.json") #os.environ.get("DATA_FILE", "/data/sensor_data.json") para el docker
MQTT_BROKER  = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT_N  = 1883
API_PORT     = 3002  # 3001 para el Docker

device_data = defaultdict(list)
MAX_READINGS = 100

stats_global = {
    'total_requests': 0,
    'requests_by_device': defaultdict(int),
    'api_start_time': time.time()
}

def obtenerTimestamp(): #Devuelve la fecha y hora para tener el registro en el dashboard
    return datetime.now().isoformat()

def cargarJSON(): #Solo lee el json que pasa el gateway
    try:
        if not os.path.exists(DATA_FILE): return []
        with open(DATA_FILE, "r") as f: return json.load(f)
    except Exception as e:
        print(f"[Error] No se pudo leer {DATA_FILE}: {e}")
        return []

#Esto es para calcular el mínimo, máximo, el promedio y la desv. estándar de la temperatura, para que se vea en el dashboard
def calcularEstadisticasDispositivo(lecturas): 
    temperaturas = [r['temperatura'] for r in lecturas if 'temperatura' in r]
    if not temperaturas: return None
    return {
        'count': len(temperaturas),
        'avg':   round(statistics.mean(temperaturas), 2),
        'min':   round(min(temperaturas), 2),
        'max':   round(max(temperaturas), 2),
        'std':   round(statistics.stdev(temperaturas), 2) if len(temperaturas) > 1 else 0
    }

# Endpoints para pasar los datos al dashboard

@app.route('/api/latest', methods=['GET'])
def api_ultima_lectura(): #Manda la última vez que se leyeron los datos del esp
    data = cargarJSON()
    if not data:
        return jsonify({'error': 'Sin datos disponibles'}), 404

    ultima_por_nodo = {}
    for lectura in reversed(data):  #Pasa del último dato enviado al primero (al revés)
        nodo = lectura.get('nodo')
        if nodo and nodo not in ultima_por_nodo:
            ultima_por_nodo[nodo] = lectura

    return jsonify({
        'status':    'ok',
        'timestamp': obtenerTimestamp(),
        'nodos':     ultima_por_nodo
    }), 200


@app.route('/api/history', methods=['GET'])
def api_historial(): #Es todo el historial de los datos que se han recabado
    try:
        limite = max(1, min(int(request.args.get('limit', 50)), 500))
    except ValueError:
        limite = 50

    data = cargarJSON()
    if not data:
        return jsonify({'error': 'Sin datos disponibles'}), 404

    return jsonify({
        'status':   'ok',
        'count':    len(data[-limite:]),
        'limit':    limite,
        'history':  data[-limite:]
    }), 200


@app.route('/api/stats', methods=['GET'])
def api_estadisticas(): #Manda el mínimo, máximo y el promedio de la temperatura, también da la humedad y luz.
    try:
        limite = int(request.args.get('limit', 100))
    except ValueError:
        limite = 100

    data = cargarJSON()
    nodos = list({r['nodo'] for r in data if 'nodo' in r})
    resultado = {}

    for nodo in nodos:
        data_nodo = [r for r in data if r.get('nodo') == nodo][-limite:]
        if not data_nodo: continue

        def calcular(campo):
            valores = [r[campo] for r in data_nodo if campo in r]
            if not valores: return {}
            return {
                'min':      round(min(valores), 1),
                'max':      round(max(valores), 1),
                'promedio': round(statistics.mean(valores), 1)
            }

        resultado[nodo] = {
            'total_lecturas': len(data_nodo),
            'temperatura':    calcular('temperatura'),
            'humedad':        calcular('humedad'),
            'luz':            calcular('luz'),
            'ultima_lectura': data_nodo[-1].get('timestamp')
        }

    return jsonify({'status': 'ok', 'stats': resultado}), 200


@app.route('/api/control', methods=['POST'])
def api_control(): #Aquí se controla el relay del esp, hace que se encienda o apague.
    body = request.get_json()
    if not body:
        return jsonify({'error': 'Se requiere body JSON'}), 400

    nodo   = body.get('nodo')
    estado = body.get('estado')

    if not nodo:
        return jsonify({'error': 'Campo nodo requerido'}), 400
    if estado not in [0, 1, '0', '1']:
        return jsonify({'error': 'Estado debe ser 0 o 1'}), 400

    estado = int(estado)
    try:
        #Esta parte es para que cree un cliente, haga la publicación del cambio en el relay y se desconecte
        c = mqtt.Client(client_id="api_control")
        c.connect(MQTT_BROKER, MQTT_PORT_N, 10)
        c.publish(f"iot/control/{nodo}", str(estado), qos=1)
        c.disconnect()

        accion = "encendido" if estado == 1 else "apagado"
        print(f"Relevador de {nodo} {accion}")

        return jsonify({
            'status':  'ok',
            'nodo':    nodo,
            'estado':  estado,
            'mensaje': f"Relevador de {nodo} {accion}"
        }), 200

    except Exception as e:
        print(f"Error MQTT: {e}")
        return jsonify({'error': f'Error MQTT: {str(e)}'}), 500


@app.route('/api/nodes', methods=['GET'])
def api_nodos(): #Esto es para devolver los esp que han mandado datos
    """Retorna la lista de nodos que han enviado data."""
    data = cargarJSON()
    nodos = list({r['nodo'] for r in data if 'nodo' in r})
    return jsonify({'status': 'ok', 'nodos': nodos, 'total': len(nodos)}), 200

if __name__ == '__main__':
    print("=" * 70)
    print("  API REST IoT - Proyecto Integrador")
    print(f"  Puerto:          {API_PORT}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=API_PORT, debug=False)
