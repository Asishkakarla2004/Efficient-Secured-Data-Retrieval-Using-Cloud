import os
from datetime import timedelta

from flask import Flask
from dotenv import load_dotenv

from .admin.routes import admin_bp
from .authentication.routes import auth_bp
from .cloud_storage.routes import files_bp
from .database.extensions import csrf, db, login_manager, migrate
from .main.routes import main_bp
from .models import Admin, User


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__, instance_relative_config=False)

    database_url = os.getenv("DATABASE_URL", "")
    database_url = database_url.strip().strip('"').strip("'")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        elif database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///secure_cloud_data_access.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    app.config["IMAGE_AUTH_IMAGES"] = [
        "auth-1.svg",
        "auth-2.svg",
        "auth-3.svg",
        "auth-4.svg",
        "auth-5.svg",
        "auth-6.svg",
        "auth-7.svg",
        "auth-8.svg",
    ]
    app.config["IMAGE_AUTH_MIN"] = 3
    app.config["IMAGE_AUTH_MAX"] = 5

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id:
            return None
        if user_id.startswith("user-"):
            return User.query.get(int(user_id.split("-", 1)[1]))
        if user_id.startswith("admin-"):
            return Admin.query.get(int(user_id.split("-", 1)[1]))
        return User.query.get(int(user_id))

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(files_bp, url_prefix="/files")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()

    return app
