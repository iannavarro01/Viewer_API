# app.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from config import Config
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
#import mysql.connector
from flask_cors import CORS
from flask_swagger import swagger

app = Flask(__name__)
app.config.from_object(Config)
jwt = JWTManager(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
CORS(app, resources={r"*": {"origins": "*"}})
db = SQLAlchemy(app)

# Configurações do banco de dados
#db = mysql.connector.connect(**Config.DB_CONFIG)


@app.route("/")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "My API"
    return jsonify(swag)


# Função para criar e configurar a aplicação Flask
def create_app():
    app.config.from_object('config.Config')

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.reset_password import reset_password_bp
    from routes.users import users_bp
    from routes.auth2fa import auth2fa_bp
    from routes.paineis import paineis_bp
    from routes.clientes import clientes_bp
    from routes.grupos import grupos_bp
    from routes.user_panel_association import user_panel_association_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reset_password_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth2fa_bp)
    app.register_blueprint(paineis_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(user_panel_association_bp)

    return app
