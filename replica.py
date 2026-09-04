import os
from flask import Flask, jsonify

app = Flask(__name__)

# Recuperar configuración desde variables de entorno
REPLICA_ID = os.environ.get('REPLICA_ID', 'DESCONOCIDO')
PORT = int(os.environ.get('PORT', 5000))

@app.route('/ping', methods=['GET'])
def ping():
    # Retorna el ID de la réplica en el menor tiempo posible.
    return jsonify({"replica_id": REPLICA_ID}), 200

@app.route('/saldo/<idTarjeta>', methods=['GET'])
def obtener_saldo(idTarjeta):
    # Retorna un saldo estático y el ID de la réplica que atendió la petición.
    return jsonify({
        "replica_id": REPLICA_ID,
        "saldo": 15000
    }), 200

@app.route('/chaos/crash', methods=['POST'])
def crash():
    # Simula una falla de hardware terminando abruptamente el proceso.
    print(f"¡La Réplica {REPLICA_ID} se está cayendo ahora!")
    os._exit(0)

if __name__ == '__main__':
    # Ejecuta la aplicación Flask
    # host='0.0.0.0' permite conexiones desde otros contenedores o máquinas
    print(f"Iniciando Réplica {REPLICA_ID} en el puerto {PORT}...")
    app.run(host='0.0.0.0', port=PORT)
