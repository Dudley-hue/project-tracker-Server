from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize db here
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with your actual secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # Initialize the db with the app
    migrate = Migrate(app, db)  # Initialize Flask-Migrate

    from models import User, Role, Project, Cohort, Class, ProjectMember  # Import models after db is initialized
    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
