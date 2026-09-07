'''
import subprocess
import sys
import time
import os

def start_process(name, script, env_vars):
    """Inicia un script de Python con variables de entorno específicas."""
    env = os.environ.copy()
    env.update(env_vars)
    
    print(f" levantando {name}...")
    # Asegura que se use el mismo python del entorno virtual
    return subprocess.Popen([sys.executable, script], env=env)


if __name__ == '__main__':
    print(" Iniciando...")
    
    procesos = []
    
    try:
        # 1. Levantar Réplicas
        procesos.append(start_process("Réplica A (5001)", "replica.py", {"PORT": "5001", "REPLICA_ID": "A"}))
        procesos.append(start_process("Réplica B (5002)", "replica.py", {"PORT": "5002", "REPLICA_ID": "B"}))
        procesos.append(start_process("Réplica C (5003)", "replica.py", {"PORT": "5003", "REPLICA_ID": "C"}))
        
        # Esperar a que las réplicas levanten
        time.sleep(1)
        
        # 2. Levantar Dispatcher
        procesos.append(start_process(
            "Dispatcher Central (5000)", 
            "dispatcher.py", 
            {"PORT": "5000", "REPLICAS": "http://localhost:5001,http://localhost:5002,http://localhost:5003"}
        ))
        
        print("\n Todo el ecosistema está corriendo...")

        # Mantener el runner vivo esperando a los procesos (o hasta que el usuario presione Ctrl+C)
        for p in procesos:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n Deteniendo todo el ecosistema...")
        for p in procesos:
            p.terminate()
        print(" Apagado completo.")
'''

import subprocess
import sys
import time
import os
import json

PID_FILE = "pids.json"

def start_process(name, script, env_vars):
    """Inicia un script de Python con variables de entorno específicas
       y registra su PID en un archivo JSON compartido."""
    env = os.environ.copy()
    env.update(env_vars)
    print(f"🟢 Levantando {name}...")
    p = subprocess.Popen([sys.executable, script], env=env)

    # Leer o crear el registro de PIDs
    pids = {}
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r", encoding="utf-8") as f:
            pids = json.load(f)

    pids[name] = {
        "pid": p.pid,
        "port": env_vars.get("PORT", "unknown"),
        "script": script
    }

    with open(PID_FILE, "w", encoding="utf-8") as f:
        json.dump(pids, f, indent=2)

    return p

if __name__ == '__main__':
    # Limpiar registro anterior
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    print("🚀 Iniciando ecosistema de Alta Disponibilidad...\n")
    procesos = []

    try:
        # 1. Levantar Réplicas (mínimo 3, en procesos separados)
        procesos.append(start_process("A", "src/replica.py", {"PORT": "5001", "REPLICA_ID": "A"}))
        procesos.append(start_process("B", "src/replica.py", {"PORT": "5002", "REPLICA_ID": "B"}))
        procesos.append(start_process("C", "src/replica.py", {"PORT": "5003", "REPLICA_ID": "C"}))

        time.sleep(1)  # Dar tiempo a que las réplicas arranquen

        # 2. Levantar Dispatcher
        procesos.append(start_process(
            "Dispatcher",
            "src/dispatcher.py",
            {"PORT": "5000", "REPLICAS": "http://localhost:5001,http://localhost:5002,http://localhost:5003"}
        ))

        print("\n✅ Ecosistema corriendo. Presiona Ctrl+C para detener.\n")

        for p in procesos:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo todo el ecosistema...")
        for p in procesos:
            p.terminate()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("🔌 Apagado completo.")
        