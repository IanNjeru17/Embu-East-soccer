from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Player, Team
from app.schemas import PlayerCreate, PlayerUpdate
from pydantic import ValidationError

bp = Blueprint('players', __name__)

@bp.route('/', methods=['GET'])
def get_players():
    """Get all active players"""
    team_id = request.args.get('team_id', type=int)
    
    query = Player.query.filter_by(is_active=True)
    if team_id:
        query = query.filter_by(team_id=team_id)
    
    players = query.order_by(Player.full_name).all()
    return jsonify([p.to_dict() for p in players]), 200

@bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """Get a specific player"""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(player.to_dict()), 200

@bp.route('/', methods=['POST'])
@jwt_required()
def create_player():
    """Register a new player"""
    try:
        data = PlayerCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Check if team exists
    team = Team.query.get(data.team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    # Check if ID number exists
    existing = Player.query.filter_by(id_number=data.id_number).first()
    if existing:
        return jsonify({
            'error': f'Player with ID {data.id_number} already exists',
            'existing_player': existing.to_dict()
        }), 400
    
    player = Player(
        full_name=data.full_name,
        id_number=data.id_number,
        id_type=data.id_type,
        team_id=data.team_id,
        position=data.position,
        jersey_number=data.jersey_number
    )
    
    db.session.add(player)
    db.session.commit()
    
    return jsonify({
        'message': 'Player registered successfully',
        'player': player.to_dict()
    }), 201

@bp.route('/<int:player_id>', methods=['PUT'])
@jwt_required()
def update_player(player_id):
    """Update a player"""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        data = PlayerUpdate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Update fields
    if data.full_name is not None:
        player.full_name = data.full_name
    
    if data.team_id is not None:
        team = Team.query.get(data.team_id)
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        player.team_id = data.team_id
    
    if data.position is not None:
        player.position = data.position
    
    if data.jersey_number is not None:
        player.jersey_number = data.jersey_number
    
    if data.is_active is not None:
        player.is_active = data.is_active
    
    db.session.commit()
    
    return jsonify({
        'message': 'Player updated successfully',
        'player': player.to_dict()
    }), 200