import requests
import time
import csv
import threading
import sys
from datetime import datetime

# --- Configuración ---
# ⚠️ IMPORTANTE: En Windows usá 127.0.0.1 en vez de localhost para evitar
# retrasos de ~2s por intento de conexión IPv6 fallido.
DISPATCHER_URL = "http://127.0.0.1:5000/saldo/123"
REQ_POR_SEGUNDO = 20
INTERVALO = 1.0 / REQ_POR_SEGUNDO
DURACION_SEG = 60
ARCHIVO_SALIDA = "resultados_cliente.csv"

resultados = []
candado = threading.Lock()

def hacer_peticion(request_id):
    t0 = time.perf_counter()
    try:
        # Timeout aumentado a 5s para dar margen si hay latencia de red
        resp = requests.get(DISPATCHER_URL, timeout=5.0)
        t1 = time.perf_counter()
        latencia_ms = round((t1 - t0) * 1000, 2)
        exito = resp.status_code == 200
        status = resp.status_code
        body = resp.text[:100] if exito else resp.text[:200]
    except requests.exceptions.ConnectTimeout:
        t1 = time.perf_counter()
        latencia_ms = round((t1 - t0) * 1000, 2)
        exito = False
        status = "CONNECT_TIMEOUT"
        body = "No pudo conectar al dispatcher"
    except requests.exceptions.ReadTimeout:
        t1 = time.perf_counter()
        latencia_ms = round((t1 - t0) * 1000, 2)
        exito = False
        status = "READ_TIMEOUT"
        body = "Se conectó pero el dispatcher no respondió"
    except Exception as e:
        t1 = time.perf_counter()
        latencia_ms = round((t1 - t0) * 1000, 2)
        exito = False
        status = f"EXCEPCION: {type(e).__name__}"
        body = str(e)

    fila = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "status": status,
        "latencia_ms": latencia_ms,
        "exito": exito,
        "body": body
    }
    with candado:
        resultados.append(fila)

def main():
    print(f"🚀 Cliente de carga iniciado")
    print(f"   URL      : {DISPATCHER_URL}")
    print(f"   Tasa     : {REQ_POR_SEGUNDO} req/s")
    print(f"   Duración : {DURACION_SEG} segundos")
    print(f"   Salida   : {ARCHIVO_SALIDA}\n")

    # Prueba de conectividad previa
    print("🔍 Probando conectividad con el dispatcher...")
    try:
        r = requests.get("http://127.0.0.1:5000/estado", timeout=5)
        print(f"   ✅ Dispatcher responde: {r.text}\n")
    except Exception as e:
        print(f"   ❌ Dispatcher NO responde: {e}")
        print("   → Asegurate de tener runner_windows.py corriendo primero.\n")

    inicio = time.time()
    req_id = 0

    while time.time() - inicio < DURACION_SEG:
        h = threading.Thread(target=hacer_peticion, args=(req_id,))
        h.start()
        req_id += 1
        time.sleep(INTERVALO)

    print("⌛ Esperando que finalicen las peticiones pendientes...")
    time.sleep(5)

    with open(ARCHIVO_SALIDA, "w", newline="", encoding="utf-8") as f:
        campos = ["timestamp", "request_id", "status", "latencia_ms", "exito", "body"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        with candado:
            writer.writerows(resultados)

    total = len(resultados)
    exitosos = sum(1 for r in resultados if r["exito"])
    fallidos = total - exitosos

    # Estadísticas de latencia
    if resultados:
        latencias = [r["latencia_ms"] for r in resultados]
        avg_lat = sum(latencias) / len(latencias)
        min_lat = min(latencias)
        max_lat = max(latencias)
    else:
        avg_lat = min_lat = max_lat = 0

    print(f"\n{'='*60}")
    print(f"✅ Test finalizado")
    print(f"{'='*60}")
    print(f"   Total peticiones : {total}")
    print(f"   Exitosas         : {exitosos} ({round(100*exitosos/total,1)}%)")
    print(f"   Fallidas         : {fallidos} ({round(100*fallidos/total,1)}%)")
    print(f"   Latencia promedio: {round(avg_lat,1)} ms")
    print(f"   Latencia mínima  : {round(min_lat,1)} ms")
    print(f"   Latencia máxima  : {round(max_lat,1)} ms")
    print(f"   Archivo CSV      : {ARCHIVO_SALIDA}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()