# Importações necessárias
import re

from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from flask_mail import Message
from app import db, mail, bcrypt
import jwt
from datetime import datetime, timedelta
import logging
from models.usuarios import usuarios

from commons import check_profiles
from config import Config

# Criação do blueprint para as rotas de redefinição de senha
reset_password_bp = Blueprint('reset_password', __name__)
JWT_SECRET_KEY = Config.JWT_SECRET_KEY

# Configuração de sistema de logs
logging.basicConfig(level=logging.DEBUG)  # Usado para mostrar todos os logs em nível DEBUG


# Função para atualizar a senha do usuário no banco de dados
# Função para atualizar a senha do usuário no banco de dados
def update_password(user_id, new_password):
    try:
        user = usuarios.query.get(user_id)
        user.password = new_password
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False

# Função para gerar um Token JWT
def generate_token(email):
    try:
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(minutes=30)  # Tempo de expiração do token (30 minutos)
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        return token  # Retorna o token
    except Exception as e:
        print(e)
        return None

# Função para verificar o Token JWT
def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("expirado")
        return None  # Token expirado
    except jwt.InvalidTokenError:
        print("invalido")
        return None  # Token inválido

@reset_password_bp.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    try:
        data = request.get_json()
        email = data.get("email")

        user = usuarios.query.filter_by(email=email).first()

        if user:
            token = generate_token(email)
            logging.debug(f"Token gerado: {token}")

            reset_link = f"https://painel.alcifmais.com.br/recovery/{token}?email={email}"
            logging.debug(f"Link de redefinição gerado: {reset_link}")

            msg = Message('Recuperação de Senha', sender=Config.MAIL_USERNAME, recipients=[email])
            msg.body = f'Clique no link a seguir para redefinir sua senha. Se você não solicitou a redefinição de senha, favor ignorar a mensagem: {reset_link}'

            try:
                mail.send(msg)
                return jsonify({"message": "Um email com instruções foi enviado, verifique sua caixa de entrada!", "token": token}), 200
            except Exception as e:
                logging.error(f"Erro ao enviar o email: {str(e)}")
                return jsonify({"message": "Erro ao enviar o email"}), 500
        else:
            return jsonify({"message": "O email fornecido não corresponde a uma conta existente"}), 400
    except Exception as e:
        return jsonify({"message": "Erro ao solicitar redefinição de senha"}), 500




# Rota para redefinir a senha com base no token
@reset_password_bp.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        new_password = request.json.get('new_password')
        confirm_password = request.json.get('confirm_password')
        reset_token = request.json.get('reset_token')

        # Verifica se as senhas coincidem
        if new_password == confirm_password:
            # Verifica se o token JWT é válido
            decoded_token = verify_token(reset_token)

            if decoded_token and 'email' in decoded_token:
                email = decoded_token['email']
                # Verificações individuais para a senha
                error_messages = []

                if len(new_password) < 8:
                    error_messages.append("A senha deve ter no mínimo 8 caracteres")

                if not any(char.isupper() for char in new_password):
                    error_messages.append("A senha deve conter pelo menos uma letra maiúscula")

                if not any(char.isdigit() for char in new_password):
                    error_messages.append("A senha deve conter pelo menos um número")

                if not any(char in '!@#$%^&*(),.?":{}|<>' for char in new_password):
                    error_messages.append("A senha deve conter pelo menos um símbolo")

                if error_messages:
                    return jsonify({"error": ", ".join(error_messages)}), 400
                else:
                    user = usuarios.query.filter_by(email=email).first()

                    if user:
                        user_id = user.id
                        hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

                        if update_password(user_id, hashed_new_password):
                            return jsonify({"message": "Senha redefinida com sucesso"}), 200
                        else:
                            return jsonify({"error": "Erro ao atualizar a senha"}), 500
                    else:
                        return jsonify({"error": "O email fornecido não corresponde a uma conta existente"}), 400
            else:
                return jsonify({"error": "Token inválido ou não corresponde ao email"}), 401
        else:
            return jsonify({"error": "As senhas não coincidem"}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": "Erro ao redefinir a senha"}), 500
