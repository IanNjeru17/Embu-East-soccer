from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate ()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    

    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.__init__(app, db)
    

    from app import auth, teams, players, fixtures, matches
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(teams.bp, url_prefix='/api/teams')
    app.register_blueprint(players.bp, url_prefix='/api/players')
    app.register_blueprint(fixtures.bp, url_prefix='/api/fixtures')
    app.register_blueprint(matches.bp, url_prefix='/api/matches')
    
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'message': 'Local League API is running'
        })
    
    # Create tables
    with app.app_context():
                
        # Create default admin user (for testing)
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(' Default admin created: username=admin, password=admin123')
    
    return app