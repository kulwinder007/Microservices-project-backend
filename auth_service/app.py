from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import bcrypt
import os
import requests

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_DURATION'] = timedelta(minutes=5)

db = SQLAlchemy(app)

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_session(user_id):
    Session.query.filter_by(user_id=user_id).delete()
    
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + app.config['SESSION_DURATION']
    
    session = Session(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.session.add(session)
    db.session.commit()
    
    return token

def validate_session(token):
    if not token:
        return None
        
    session = Session.query.filter_by(token=token).first()
    if not session or session.expires_at < datetime.utcnow():
        if session:
            db.session.delete(session)
            db.session.commit()
        return None
        
    return session.user_id

@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    
    try:
        # Make request to user service to verify credentials
        response = requests.post(
            f"{os.getenv('USER_SERVICE_URL')}/users/verify",
            json=data
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        user_data = response.json()
        token = create_session(user_data['id'])
        
        return jsonify({
            'user': user_data,
            'token': token
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/validate', methods=['GET'])
def validate():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid token'}), 401
        
    token = auth_header.split(' ')[1]
    user_id = validate_session(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid or expired session'}), 401
        
    # Get user details from user service
    response = requests.get(f"{os.getenv('USER_SERVICE_URL')}/users/{user_id}")
    if response.status_code != 200:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify(response.json())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002)