from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from app.models import User
from app.schemas import LoginRequest
from pydantic import ValidationError

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = LoginRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Find user
    user = User.query.filter_by(username=data.username).first()
    
    if not user or not check_password_hash(user.password_hash, data.password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Create access token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'is_admin': user.is_admin}
    )
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    }), 200