import os

class Config:
    # Secret key for session management, CSRF protection, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    
    # Database URI - defaulting to SQLite if DATABASE_URL is not set in the environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # Disables Flask-SQLAlchemy’s event system to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for JSON Web Token (JWT) authentication
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your_jwt_secret_key'
