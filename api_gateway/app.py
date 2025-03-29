from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user_service:5001')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth_service:5002')
TASK_SERVICE_URL = os.getenv('TASK_SERVICE_URL', 'http://task_service:5003')

def forward_request(service_url, path, method='GET', data=None, headers=None):
    url = f"{service_url}{path}"
    return requests.request(
        method=method,
        url=url,
        json=data,
        headers=headers
    )

@app.route('/users', methods=['POST'])
def create_user():
    response = forward_request(
        USER_SERVICE_URL,
        '/users',
        method='POST',
        data=request.json
    )
    return jsonify(response.json()), response.status_code

@app.route('/auth/signin', methods=['POST'])
def signin():
    response = forward_request(
        AUTH_SERVICE_URL,
        '/signin',
        method='POST',
        data=request.json
    )
    return jsonify(response.json()), response.status_code

@app.route('/auth/validate', methods=['GET'])
def validate():
    auth_header = request.headers.get('Authorization')
    response = forward_request(
        AUTH_SERVICE_URL,
        '/validate',
        headers={'Authorization': auth_header}
    )
    return jsonify(response.json()), response.status_code

@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    auth_header = request.headers.get('Authorization')
    if request.method == 'GET':
        response = forward_request(
            TASK_SERVICE_URL,
            '/tasks',
            headers={'Authorization': auth_header}
        )
    else:
        response = forward_request(
            TASK_SERVICE_URL,
            '/tasks',
            method='POST',
            data=request.json,
            headers={'Authorization': auth_header}
        )
    return jsonify(response.json()), response.status_code

@app.route('/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    auth_header = request.headers.get('Authorization')
    response = forward_request(
        TASK_SERVICE_URL,
        f'/tasks/{task_id}',
        method='PATCH',
        data=request.json,
        headers={'Authorization': auth_header}
    )
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)