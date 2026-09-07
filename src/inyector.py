import json
import os
import sys
import signal
import time
from datetime import datetime

PID_FILE = "pids.json"
LOG_FILE = "inyector_log.txt"

def cargar_pids():
    if not os.path.exists(PID_FILE):
        print(f"❌ No se encontró {PID_FILE}. Ejecuta primero runner.py.")
        sys.exit(1)
    with open(PID_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def listar_replicas(pids):
    print("\n📋 Réplicas detectadas:")
    print("-" * 50)
    for nombre, info in pids.items():
        # Saltar el dispatcher si está en el archivo
        if os.path.basename(info.get("script", "")) == "dispatcher.py":
            continue
        print(f"   [{nombre}]  PID {info['pid']}  →  Puerto {info['port']}")
    print("-" * 50)

def main():
    pids = cargar_pids()
    listar_replicas(pids)

    nombre = input("\n💥 ¿Qué réplica deseas matar? (A / B / C): ").strip().upper()

    if nombre not in pids:
        print("❌ Réplica no válida.")
        sys.exit(1)

    info = pids[nombre]
    pid = info["pid"]
    puerto = info["port"]

    # Timestamp exacto del impacto
    ts = datetime.now().isoformat()

    print(f"\n⚡ [{ts}] Impactando réplica {nombre} (PID {pid}, puerto {puerto})...")

    try:
        # SIGTERM primero; si quieres más abrupto cambia a signal.SIGKILL
        os.kill(pid, signal.SIGTERM)
        print(f"✅ Proceso {pid} terminado.")
    except ProcessLookupError:
        print(f"⚠️  El proceso {pid} ya no existía.")
    except PermissionError:
        print(f"❌ Sin permisos para matar el proceso {pid}.")
        sys.exit(1)

    # Documentar el impacto
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | CRASH | Réplica {nombre} | PID {pid} | Puerto {puerto}\n")

    print(f"📝 Impacto documentado en {LOG_FILE}")

if __name__ == "__main__":
    main()