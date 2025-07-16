from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User
from app.auth import authenticate_user, create_user_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        role=data.get('role', 'client'),
        picture=data.get('picture', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    token = create_user_token(user)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'picture': user.picture,
        'token': token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = create_user_token(user)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'picture': user.picture,
        'token': token
    }), 200