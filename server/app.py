from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from models import User, Project, Cohort, ProjectMember, ProjectCohort
    import routes  # Ensure this import comes after initializing app and db

    # Register Blueprints
    routes.register_blueprints(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
