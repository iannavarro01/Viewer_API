from functools import wraps
from flask import request, abort
from flask_jwt_extended import get_jwt_identity
from models.usuarios import usuarios  # Importe o modelo de usuários (com "u" minúsculo)
from app import db


# Decorador para verificar a permissão de ADMIN da rota
def check_profile(profile):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()

            user = db.session.query(usuarios).get(user_id)

            if not user:
                abort(403, "Perfil do usuário não encontrado")

            if user.perfil != profile:
                abort(403, "Acesso negado")

            return func(*args, **kwargs)

        return wrapper

    return decorator

# Decorador para verificar o perfil de Cliente
def check_profiles(profiles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()

            user = db.session.query(usuarios).get(user_id)

            if not user:
                abort(403, "Perfil do usuário não encontrado")

            if user.perfil not in profiles:
                abort(403, "Acesso negado")

            return func(*args, **kwargs)

        return wrapper

    return decorator
