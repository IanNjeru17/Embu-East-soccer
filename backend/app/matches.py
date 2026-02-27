from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Fixture, MatchEvent, Player, EventType
from app.schemas import ResultCreate, GoalCreate
from pydantic import ValidationError
from datetime import datetime

bp = Blueprint('matches', __name__)

@bp.route('/<int:fixture_id>/result', methods=['POST'])
@jwt_required()
def set_result(fixture_id):
    """Set match result"""
    fixture = Fixture.query.get(fixture_id)
    if not fixture:
        return jsonify({'error': 'Fixture not found'}), 404
    
    try:
        data = ResultCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Update fixture
    fixture.home_score = data.home_score
    fixture.away_score = data.away_score
    fixture.status = 'completed'
    
    db.session.commit()
    
    return jsonify({
        'message': 'Result recorded successfully',
        'fixture': fixture.to_dict()
    }), 200

@bp.route('/<int:fixture_id>/goals', methods=['POST'])
@jwt_required()
def add_goal(fixture_id):
    """Add a goal to a match"""
    fixture = Fixture.query.get(fixture_id)
    if not fixture:
        return jsonify({'error': 'Fixture not found'}), 404
    
    try:
        data = GoalCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({'error': e.errors()}), 400
    
    # Get player
    player = Player.query.get(data.player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Check if player is from either team
    if player.team_id not in [fixture.home_team_id, fixture.away_team_id]:
        return jsonify({'error': 'Player is not from either team'}), 400
    
    # Create goal event
    goal = MatchEvent(
        fixture_id=fixture_id,
        event_type=EventType.GOAL,
        player_id=data.player_id,
        team_id=player.team_id,
        minute=data.minute
    )
    
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({
        'message': 'Goal recorded successfully',
        'goal': goal.to_dict()
    }), 201

@bp.route('/<int:fixture_id>/goals', methods=['GET'])
def get_goals(fixture_id):
    """Get all goals for a match"""
    goals = MatchEvent.query.filter_by(
        fixture_id=fixture_id,
        event_type=EventType.GOAL
    ).order_by(MatchEvent.minute).all()
    
    return jsonify([g.to_dict() for g in goals]), 200

@bp.route('/today', methods=['GET'])
def todays_matches():
    """Get today's matches"""
    today = datetime.utcnow().date()
    fixtures = Fixture.query.filter(
        db.func.date(Fixture.match_date) == today
    ).all()
    
    return jsonify([f.to_dict() for f in fixtures]), 200

@bp.route('/upcoming', methods=['GET'])
def upcoming_matches():
    """Get upcoming matches"""
    now = datetime.utcnow()
    limit = request.args.get('limit', 10, type=int)
    
    fixtures = Fixture.query.filter(
        Fixture.status == 'scheduled',
        Fixture.match_date >= now
    ).order_by(Fixture.match_date).limit(limit).all()
    
    return jsonify([f.to_dict() for f in fixtures]), 200

@bp.route('/recent', methods=['GET'])
def recent_results():
    """Get recent results"""
    limit = request.args.get('limit', 10, type=int)
    
    fixtures = Fixture.query.filter_by(
        status='completed'
    ).order_by(Fixture.match_date.desc()).limit(limit).all()
    
    return jsonify([f.to_dict() for f in fixtures]), 200