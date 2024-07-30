from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

app = Flask(_name_)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

from models import User, Project, Cohort, ProjectMember, ProjectCohort
import routes  # Ensure this import comes after initializing app and db

# Register Blueprints
routes.register_blueprints(app)

if _name_ == "_main_":
    app.run(debug=True)