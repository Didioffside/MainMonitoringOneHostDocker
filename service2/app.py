from flask import Flask, jsonify
from prometheus_client import Counter, generate_latest, REGISTRY
import json
app = Flask(__name__)
import requests
import time
import random
import threading
counter = Counter('http_requests_total', 'Total HTTP Requests', ['service'])

@app.route('/')
def hello_world():
    counter.labels(service='service2').inc()
    return "Hello from Service 2!"

@app.route('/metrics')
def metrics():
    return generate_latest(REGISTRY)

@app.route('/get_info', methods=['GET'])
def get_info():
    string = "service2info"
    return jsonify(string)


def collect_data():
    service1_endpoint = "http://service1:5000/get_info"
    response = requests.get(service1_endpoint)
    if response.status_code == 200:

        print("DEU CERTO", flush=True)
        data = response.json()
        print("aqui", data, flush=True)
        return data
    else:
        print(f"Failed to fetch CPU metrics: {response.status_code}", flush=True)
    
def run():
    time.sleep(random.randint(10, 30))
    while True:
        collect_data()
        time.sleep(random.randint(10, 30))
        
background_thread2 = threading.Thread(target=run, daemon=True)
background_thread2.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)