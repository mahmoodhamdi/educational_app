from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import User
from app.auth import client_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@client_required
def get_user(user_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    target_user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': target_user.id,
        'name': target_user.name,
        'email': target_user.email,
        'role': target_user.role,
        'picture': target_user.picture
    }), 200

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@client_required
def update_user(user_id):
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(current_user_id)
    if user.role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'Access denied'}), 403
    
    target_user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    target_user.name = data.get('name', target_user.name)
    target_user.picture = data.get('picture', target_user.picture)
    
    if user.role == 'admin':
        target_user.role = data.get('role', target_user.role)
    
    db.session.commit()
    
    return jsonify({
        'id': target_user.id,
        'name': target_user.name,
        'email': target_user.email,
        'role': target_user.role,
        'picture': target_user.picture
    }), 200