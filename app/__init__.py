import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Garante que a pasta instance existe
    os.makedirs(app.instance_path, exist_ok=True)

    # Banco de dados local em instance/arashi.db
    default_db_path = os.path.join(app.instance_path, "arashi.db")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "arashi_super_secret_key_2026"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    # Inicialização das extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."

    # Loader de usuário
    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # Registro de rotas
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app