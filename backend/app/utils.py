from datetime import datetime, timedelta
from app.models import Fixture, Team, Player, MatchEvent, EventType, FixtureStatus
from app import db

def generate_fixtures(teams, start_date):
   
    fixtures = []
    team_list = list(teams)
    team_count = len(team_list)
    
    if team_count < 2:
        return []
    
    # If odd number of teams, add None for bye weeks
    if team_count % 2 != 0:
        team_list.append(None)
        team_count += 1
    
    # Number of matchdays
    matchdays = (team_count - 1) * 2
    match_number = 1
    
    # Create fixtures
    for round_num in range(matchdays):
        round_fixtures = []
        
        for i in range(team_count // 2):
            home_idx = i
            away_idx = team_count - 1 - i
            
            home_team = team_list[home_idx]
            away_team = team_list[away_idx]
            
            # Skip if either team is None (bye week)
            if home_team and away_team:
                # Alternate home/away for return legs
                if round_num >= (team_count - 1):
                    home_team, away_team = away_team, home_team
                
                # Calculate match date (Sunday)
                match_date = datetime.combine(
                    start_date + timedelta(days=7 * round_num),
                    datetime.min.time()
                )
                
                fixture = Fixture(
                    match_number=match_number,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date,
                    venue=home_team.home_venue,
                    status=FixtureStatus.SCHEDULED
                )
                round_fixtures.append(fixture)
                match_number += 1
        
        fixtures.extend(round_fixtures)
        
        # Rotate teams (keep first team fixed)
        if len(team_list) > 2:
            team_list = [team_list[0]] + [team_list[-1]] + team_list[1:-1]
    
    return fixtures

def calculate_league_table():
    #Calculate current standings
    teams = Team.query.filter_by(is_active=True).all()
    standings = []
    
    for team in teams:
        # Get all completed matches
        home_matches = Fixture.query.filter_by(
            home_team_id=team.id,
            status='completed'
        ).all()
        
        away_matches = Fixture.query.filter_by(
            away_team_id=team.id,
            status='completed'
        ).all()
        
        played = len(home_matches) + len(away_matches)
        wins = draws = losses = 0
        gf = ga = 0
        
        # Process home matches
        for m in home_matches:
            gf += m.home_score or 0
            ga += m.away_score or 0
            if m.home_score > m.away_score:
                wins += 1
            elif m.home_score == m.away_score:
                draws += 1
            else:
                losses += 1
        
        # Process away matches
        for m in away_matches:
            gf += m.away_score or 0
            ga += m.home_score or 0
            if m.away_score > m.home_score:
                wins += 1
            elif m.away_score == m.home_score:
                draws += 1
            else:
                losses += 1
        
        points = (wins * 3) + draws
        gd = gf - ga
        
        standings.append({
            'team_id': team.id,
            'team_name': team.name,
            'played': played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': gf,
            'goals_against': ga,
            'goal_difference': gd,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
            'points': points
        })
    
    # Sort by points, GD, GF
    standings.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))
    
    return standings

def get_top_scorers(limit=10):
    """Get top goal scorers"""
    from sqlalchemy import func
    
    results = db.session.query(
        Player,
        func.count(MatchEvent.id).label('goal_count')
    ).join(MatchEvent, MatchEvent.player_id == Player.id).filter(
        MatchEvent.event_type == EventType.GOAL
    ).group_by(Player.id).order_by(
        func.count(MatchEvent.id).desc()
    ).limit(limit).all()
    
    return [{
        'player_id': p.id,
        'player_name': p.full_name,
        'team_name': p.team.name if p.team else None,
        'goals': count
    } for p, count in results]