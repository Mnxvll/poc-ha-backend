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
