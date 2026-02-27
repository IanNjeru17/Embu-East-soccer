from app import db
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
import enum



class IDType(enum.Enum):
    NATIONAL_ID = "national_id"
    BIRTH_CERTIFICATE = "birth_certificate"

class PositionType(enum.Enum):
    GK = "gk"
    DEF = "def"
    MID = "mid"
    FWD = "fwd"

class FixtureStatus(enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"

class EventType(enum.Enum):
    GOAL = "goal"



class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    serialize_only = ('id', 'username', 'is_admin', 'created_at')

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin   = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Team(db.Model, SerializerMixin):
    __tablename__ = 'teams'

    serialize_rules = ('players_count', '-home_fixtures', '-away_fixtures', '-players.team', '-players.goals')

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    home_venue = db.Column(db.String(200), nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    home_fixtures = db.relationship('Fixture', foreign_keys='Fixture.home_team_id', back_populates='home_team')
    away_fixtures = db.relationship('Fixture', foreign_keys='Fixture.away_team_id', back_populates='away_team')
    players       = db.relationship('Player', back_populates='team', cascade='all, delete-orphan')

    @property
    def players_count(self):
        return len(self.players)


class Player(db.Model, SerializerMixin):
    __tablename__ = 'players'

    serialize_rules = ('masked_id', 'goal_count', '-id_number', '-team.players', '-team.home_fixtures', '-team.away_fixtures', '-goals.player', '-goals.fixture.events', '-goals.team.players')

    id             = db.Column(db.Integer, primary_key=True)
    full_name      = db.Column(db.String(200), nullable=False)
    id_number      = db.Column(db.String(50), nullable=False, unique=True)
    id_type        = db.Column(db.Enum(IDType), nullable=False)
    team_id        = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    position       = db.Column(db.Enum(PositionType), nullable=True)
    jersey_number  = db.Column(db.Integer, nullable=True)
    is_active      = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team  = db.relationship('Team', back_populates='players')
    goals = db.relationship('MatchEvent', back_populates='player')

    @property
    def masked_id(self):
        """Return masked ID number for privacy"""
        return f"****{self.id_number[-4:]}" if self.id_number else None

    @property
    def goal_count(self):
        return MatchEvent.query.filter_by(
            player_id=self.id,
            event_type=EventType.GOAL
        ).count()




class Fixture(db.Model, SerializerMixin):
    __tablename__ = 'fixtures'

    serialize_rules = ('-home_team.home_fixtures', '-home_team.away_fixtures', '-home_team.players', '-away_team.home_fixtures', '-away_team.away_fixtures', '-away_team.players', '-events.fixture', '-events.player.goals', '-events.team.home_fixtures', '-events.team.away_fixtures', '-events.team.players')

    id           = db.Column(db.Integer, primary_key=True)
    match_number = db.Column(db.Integer, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    match_date   = db.Column(db.DateTime, nullable=False)
    venue        = db.Column(db.String(200), nullable=False)
    status       = db.Column(db.Enum(FixtureStatus), default=FixtureStatus.SCHEDULED)
    home_score   = db.Column(db.Integer, nullable=True)
    away_score   = db.Column(db.Integer, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    home_team = db.relationship('Team', foreign_keys=[home_team_id], back_populates='home_fixtures')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], back_populates='away_fixtures')
    events    = db.relationship('MatchEvent', back_populates='fixture', cascade='all, delete-orphan')



class MatchEvent(db.Model, SerializerMixin):
    __tablename__ = 'match_events'

    serialize_rules = ('-fixture.events', '-fixture.home_team.home_fixtures', '-fixture.home_team.away_fixtures', '-fixture.away_team.home_fixtures', '-fixture.away_team.away_fixtures', '-player.goals', '-player.team.players', '-team.home_fixtures', '-team.away_fixtures', '-team.players')

    id         = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixtures.id'), nullable=False)
    event_type = db.Column(db.Enum(EventType), nullable=False)
    player_id  = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team_id    = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    minute     = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    fixture = db.relationship('Fixture', back_populates='events')
    player  = db.relationship('Player', back_populates='goals')
    team    = db.relationship('Team')