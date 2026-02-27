from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Fixture, Team, MatchEvent
from app.schemas import FixtureGenerateRequest, FixtureUpdate
from app.utils import generate_fixtures, calculate_league_table, get_top_scorers
from pydantic import ValidationError
from datetime import datetime

bp = Blueprint('fixtures', __name__)

@bp.route('/', methods=['GET'])
def get_fixtures():
    """Get all fixtures"""
    team_id = request.args.get('team_id', type=int)
    status = request.args.get('status')
    
    query = Fixture.query
    
    if team_id:
        query = query.filter(
            (Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id)
        )
    
    if status:
        query = query.filter_by(status=status)
    
    fixtures = query.order_by(Fixture.match_date).all()
    return jsonify([f.to_dict() for f in fixtures]), 200

@bp.route('/<int:fixture_id>', methods=['GET'])
def get_fixture(fixture_id):
    """Get a specific fixture"""
    fixture = Fixture.query.get(fixture_id)
    if not fixture:
        return jsonify({'error': 'Fixture not found'}), 404
    return jsonify(fixture.to_dict()), 200

@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_season_fixtures():
    """Generate full season fixtures"""
    try:
        data = FixtureGenerateRequest(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Get all active teams
    teams = Team.query.filter_by(is_active=True).all()
    
    if len(teams) < 2:
        return jsonify({'error': 'Need at least 2 teams to generate fixtures'}), 400
    
    # Check if fixtures exist
    existing = Fixture.query.first()
    if existing:
        # Delete existing fixtures and events
        MatchEvent.query.delete()
        Fixture.query.delete()
        db.session.commit()
    
    # Generate new fixtures
    fixtures = generate_fixtures(teams, data.season_start_date)
    
    if fixtures:
        db.session.add_all(fixtures)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully generated {len(fixtures)} fixtures',
            'count': len(fixtures)
        }), 201
    else:
        return jsonify({'error': 'Failed to generate fixtures'}), 500

@bp.route('/<int:fixture_id>', methods=['PUT'])
@jwt_required()
def update_fixture(fixture_id):
    """Update a fixture"""
    fixture = Fixture.query.get(fixture_id)
    if not fixture:
        return jsonify({'error': 'Fixture not found'}), 404
    
    try:
        data = FixtureUpdate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Update fields
    if data.match_date is not None:
        fixture.match_date = data.match_date
    
    if data.venue is not None:
        fixture.venue = data.venue
    
    if data.status is not None:
        from app.models import FixtureStatus
        fixture.status = FixtureStatus(data.status)
    
    if data.home_score is not None:
        fixture.home_score = data.home_score
    
    if data.away_score is not None:
        fixture.away_score = data.away_score
    
    db.session.commit()
    
    return jsonify({
        'message': 'Fixture updated successfully',
        'fixture': fixture.to_dict()
    }), 200

@bp.route('/table', methods=['GET'])
def league_table():
    """Get current league table"""
    standings = calculate_league_table()
    return jsonify(standings), 200

@bp.route('/top-scorers', methods=['GET'])
def top_scorers():
    """Get top goal scorers"""
    limit = request.args.get('limit', 10, type=int)
    scorers = get_top_scorers(limit)
    return jsonify(scorers), 200