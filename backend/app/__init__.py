from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    
    # Allow requests from your Vercel frontend
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Note: For production, you should restrict the origin to your Vercel URL
    # e.g., CORS(app, resources={r"/*": {"origins": "https://your-frontend-app.vercel.app"}})

    socketio.init_app(app, cors_allowed_origins="*")

    from app import routes, models
    app.register_blueprint(routes.bp)

    return app
