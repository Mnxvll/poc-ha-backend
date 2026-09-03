import os
from flask import Flask, jsonify

app = Flask(__name__)

# Retrieve configuration from environment variables
REPLICA_ID = os.environ.get('REPLICA_ID', 'UNKNOWN')
PORT = int(os.environ.get('PORT', 5000))

@app.route('/ping', methods=['GET'])
def ping():
    
    # Returns the replica ID in the shortest time possible.
    return jsonify({"replica_id": REPLICA_ID}), 200


@app.route('/balance/<card_id>', methods=['GET'])
def get_balance(card_id):
        
     #Returns a balance and the replica ID that served the request.
    return jsonify({
        "replica_id": REPLICA_ID,
        "balance": 15000
    }), 200


@app.route('/chaos/crash', methods=['POST'])
def crash():
    
    # Simulates a hardware failure by abruptly terminating the process.
    print(f"Replica {REPLICA_ID} is crashing down now!")
    os._exit(0)



if __name__ == '__main__':
    # Run the Flask application
    # host='0.0.0.0' allows connections from other containers/machines if needed

    print(f"Starting Replica {REPLICA_ID} on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT)
