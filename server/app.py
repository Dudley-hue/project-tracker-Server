from flask import Flask
from models import db  # Import db from models
from routes import api_bp
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with your actual secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # Initialize the db with the app
    migrate = Migrate(app, db)  # Initialize Flask-Migrate

    # Register the Blueprint after initializing the app and db
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
