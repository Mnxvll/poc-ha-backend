import os
import time
import threading
import requests
import concurrent.futures
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# --- Configuración ---
# Ejemplo: http://localhost:5001,http://localhost:5002,http://localhost:5003
REPLICAS_ENV = os.environ.get('REPLICAS', 'http://localhost:5001')
REPLICAS = [url.strip() for url in REPLICAS_ENV.split(',') if url.strip()]

PORT = int(os.environ.get('PORT', 5000))

T = float(os.environ.get('T', 1.0))    # Intervalo de sondeo en segundos
t = float(os.environ.get('t', 0.3))    # Tiempo de espera (timeout) en segundos (300ms)
k = int(os.environ.get('k', 2))        # Fallos consecutivos para marcar como CAIDA
m = int(os.environ.get('m', 2))        # Éxitos consecutivos para marcar como VIVA

# --- Estado Global ---
# Estructura: { url: {"estado": "VIVA", "fallos": 0, "exitos": 0} }
estado_replicas = {}
for url in REPLICAS:
    estado_replicas[url] = {"estado": "VIVA", "fallos": 0, "exitos": 0}

# Candado (Lock) para hilos y evitar condiciones de carrera (race conditions)
candado_estado = threading.Lock()

def obtener_marca_de_tiempo():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def hacer_ping_a_replica(url):
    """Envía un ping a una réplica específica y retorna True si es exitoso."""
    try:
        response = requests.get(f"{url}/ping", timeout=t)
        if response.status_code == 200:
            return True
    except requests.RequestException:
        pass
    return False

def bucle_monitor():
    """Hilo en segundo plano que sondea continuamente a las réplicas."""
    while True:
        for url in REPLICAS:
            esta_viva = hacer_ping_a_replica(url)
            
            with candado_estado:
                estado_actual = estado_replicas[url]
                
                if esta_viva:
                    estado_actual["exitos"] += 1
                    estado_actual["fallos"] = 0
                    
                    if estado_actual["estado"] == "CAIDA" and estado_actual["exitos"] >= m:
                        estado_actual["estado"] = "VIVA"
                        print(f"[{obtener_marca_de_tiempo()}] REPLICA {url} CAIDA -> VIVA", flush=True)
                else:
                    estado_actual["fallos"] += 1
                    estado_actual["exitos"] = 0
                    
                    if estado_actual["estado"] == "VIVA" and estado_actual["fallos"] >= k:
                        estado_actual["estado"] = "CAIDA"
                        print(f"[{obtener_marca_de_tiempo()}] REPLICA {url} VIVA -> CAIDA", flush=True)
                        
        time.sleep(T)

# Iniciar el hilo del monitor en segundo plano
hilo_monitor = threading.Thread(target=bucle_monitor, daemon=True)
hilo_monitor.start()


# --- Puntos de Enlace (Endpoints) ---

@app.route('/estado', methods=['GET'])
def obtener_estado():
    """Retorna el estado actual de todas las réplicas."""
    with candado_estado:
        estado_actual = {url: datos["estado"] for url, datos in estado_replicas.items()}
    return jsonify(estado_actual), 200

def consultar_saldo_en_replica(url, id_tarjeta):
    """Consulta el saldo en una réplica específica."""
    response = requests.get(f"{url}/saldo/{id_tarjeta}", timeout=2.0)
    response.raise_for_status()
    return response.json()

@app.route('/saldo/<idTarjeta>', methods=['GET'])
def obtener_saldo(idTarjeta):
    """Redundancia activa: Consulta a todas las réplicas VIVAS y retorna la primera respuesta válida."""
    with candado_estado:
        replicas_vivas = [url for url, datos in estado_replicas.items() if datos["estado"] == "VIVA"]
        
    if not replicas_vivas:
        return jsonify({"error": "No hay replicas VIVA disponibles"}), 503

    # Usamos ThreadPoolExecutor para enviar peticiones en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(replicas_vivas)) as ejecutor:
        # Enviar todas las tareas
        futuro_por_url = {ejecutor.submit(consultar_saldo_en_replica, url, idTarjeta): url for url in replicas_vivas}
        
        # as_completed entrega los futuros a medida que se completan
        for futuro in concurrent.futures.as_completed(futuro_por_url):
            try:
                datos = futuro.result()
                # Retornar la primera respuesta exitosa inmediatamente
                return jsonify(datos), 200
            except Exception as e:
                # Si esta réplica falló, simplemente la ignoramos y esperamos la siguiente
                url = futuro_por_url[futuro]
                print(f"[{obtener_marca_de_tiempo()}] La peticion a {url} fallo: {e}", flush=True)
                
    # Si salimos del bucle, todas las réplicas fallaron
    return jsonify({"error": "Todas las replicas fallaron al responder"}), 502

if __name__ == '__main__':
    print(f"Iniciando Dispatcher en el puerto {PORT}...", flush=True)
    print(f"Monitoreando replicas: {REPLICAS}", flush=True)
    # Usando threaded=True para que Flask maneje peticiones entrantes concurrentemente
    app.run(host='0.0.0.0', port=PORT, threaded=True)
