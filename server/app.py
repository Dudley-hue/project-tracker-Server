from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

from models import Role, User, Project, ProjectMember, Cohort, ProjectCohort

@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the Project Tracking System'})

if __name__ == '_main_':
    app.run(debug=True)