from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import requests
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    user_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'dueDate': self.due_date.isoformat(),
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

def get_user_from_token(auth_header):
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    response = requests.get(
        f"{os.getenv('AUTH_SERVICE_URL')}/validate",
        headers={'Authorization': auth_header}
    )
    
    if response.status_code != 200:
        return None
        
    return response.json()['id']

@app.route('/tasks', methods=['GET'])
def get_tasks():
    user_id = get_user_from_token(request.headers.get('Authorization'))
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks', methods=['POST'])
def create_task():
    user_id = get_user_from_token(request.headers.get('Authorization'))
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    
    try:
        task = Task(
            title=data['title'],
            description=data['description'],
            due_date=datetime.fromisoformat(data['dueDate'].replace('Z', '+00:00')),
            status='pending',
            user_id=user_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    user_id = get_user_from_token(request.headers.get('Authorization'))
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    data = request.json
    
    try:
        if 'status' in data:
            task.status = data['status']
        
        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5003)