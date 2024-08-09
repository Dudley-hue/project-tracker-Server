from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    Talisman(app, force_https=False)
    CORS(app)

    # Import and register the blueprint
    from routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
