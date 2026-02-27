from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Team
from app.schemas import TeamCreate, TeamUpdate
from pydantic import ValidationError

bp = Blueprint('teams', __name__)

@bp.route('/', methods=['GET'])
def get_teams():
    """Get all active teams"""
    teams = Team.query.filter_by(is_active=True).all()
    return jsonify([team.to_dict() for team in teams]), 200

@bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_teams():
    """Get all teams (including inactive) - Admin only"""
    teams = Team.query.all()
    return jsonify([team.to_dict() for team in teams]), 200

@bp.route('/<int:team_id>', methods=['GET'])
def get_team(team_id):
    """Get a specific team"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(team.to_dict()), 200

@bp.route('/', methods=['POST'])
@jwt_required()
def create_team():
    """Create a new team"""
    try:
        data = TeamCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    existing = Team.query.filter_by(name=data.name).first()
    if existing:
        return jsonify({'error': f'Team "{data.name}" already exists'}), 400
    
    team = Team(
        name=data.name,
        home_venue=data.home_venue
    )
    
    db.session.add(team)
    db.session.commit()
    
    return jsonify({
        'message': 'Team created successfully',
        'team': team.to_dict()
    }), 201

@bp.route('/<int:team_id>', methods=['PUT'])
@jwt_required()
def update_team(team_id):
    """Update a team"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    try:
        data = TeamUpdate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Update fields
    if data.name is not None:
        existing = Team.query.filter(Team.name == data.name, Team.id != team_id).first()
        if existing:
            return jsonify({'error': f'Team "{data.name}" already exists'}), 400
        team.name = data.name
    
    if data.home_venue is not None:
        team.home_venue = data.home_venue
    
    if data.is_active is not None:
        team.is_active = data.is_active
    
    db.session.commit()
    
    return jsonify({
        'message': 'Team updated successfully',
        'team': team.to_dict()
    }), 200

@bp.route('/<int:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    """Delete a team (soft delete)"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    team.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Team deactivated successfully'}), 200