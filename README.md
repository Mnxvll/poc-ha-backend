# RECAUDO-T - Arquitectura de Alta Disponibilidad

Este repositorio contiene la implementacion del sistema RECAUDO-T, aplicando tacticas de disponibilidad como Ping/Echo y Redundancia Activa.

## Ejecucion

Para ejecutar el sistema completo con un solo comando, es necesario utilizar un entorno virtual de Python.

1. Activar el entorno virtual:
   source .venv/bin/activate.fish

2. Instalar las dependencias (solo la primera vez):
   pip install -r requirements.txt

3. Ejecutar el orquestador:
   python runner.py

El script runner.py se encargara de levantar tres instancias independientes de replica.py (puertos 5001, 5002, 5003) y el proceso central dispatcher.py (puerto 5000). Para detener todo, simplemente presionar Ctrl+C.

## Endpoints Principales

### Dispatcher (Puerto 5000)

- **GET `/saldo/<idTarjeta>`**
  Ruta principal de consulta. Redirige la peticion en paralelo a todas las replicas marcadas como "VIVA" y retorna la respuesta mas veloz.
  Ejemplo: `curl http://localhost:5000/saldo/123`

- **GET `/estado`**
  Ruta de monitoreo para verificar el estado de salud interno de las replicas, actualizado en segundo plano por el monitor Ping/Echo.
  Ejemplo: `curl http://localhost:5000/estado`

### Replicas (Puertos 5001, 5002, 5003)

- **GET `/ping`**
  Utilizada exclusivamente por el monitor del Dispatcher para verificar disponibilidad.

- **POST `/chaos/crash`**
  Ruta para simulacion de desastres. Al consumirla, apaga inmediatamente el proceso de la replica.
  Ejemplo: `curl -X POST http://localhost:5001/chaos/crash`
