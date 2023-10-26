# Importações necessárias
from flask import Blueprint, request, jsonify
from config import Config
from app import mail, db
from flask_mail import Message
from datetime import timedelta, datetime
import logging
import string
import random
from models.two_fa import two_fa
from models.usuarios import usuarios


# ROTA AINDA NÃO UTILIZADA


# Criação do blueprint para as rotas de autenticação de dois fatores (2FA)
auth2fa_bp = Blueprint('auth2fa', __name__)

logging.basicConfig(level=logging.DEBUG)

''' # Função para iniciar o agendamento da limpeza da tabela 2FA a cada 24 horas
def start_scheduler():
    schedule.every(24).hours.do(reset_2fa_table)
    while True:
        schedule.run_pending()
        time.sleep(1)
        


def start_scheduler_thread():  # Inicia o agendador em uma thread separada, para ser executada em segundo plano
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()
    '''



# Função para gerar uma senha de 2FA com 6 dígitos
def generate_password():
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choice(characters) for i in range(6))
    return code

# Função para redefinir a tabela 2FA
def reset_2fa_table():
    try:
        two_fa.query.delete()  # Use a função delete para excluir todos os registros
        db.session.commit()
        print("Tabela 2FA foi resetada")
    except Exception as e:
        print(f"Erro ao resetar a tabela 2FA: {str(e)}")

# Rota para solicitar um código 2FA
@auth2fa_bp.route('/auth2fa_request', methods=['POST'])
def auth2fa_request():
    data = request.get_json()
    email = data.get("email")

    user = usuarios.query.filter_by(email=email).first()

    if user:
        # Gera um código 2FA exclusivo para o usuário
        code = generate_password()

        # Insere o código 2FA na tabela 2fa
        try:
            new_2fa = two_fa(user_id=user.id, username=user.username, code=code, request_time=datetime.now())
            db.session.add(new_2fa)
            db.session.commit()
        except Exception as e:
            logging.error(f"Erro ao inserir código 2FA no banco de dados: {str(e)}")
            return jsonify({"message": "Erro interno ao processar a solicitação"}), 500

        msg = Message('Autenticação de 2 Fatores', sender=Config.MAIL_USERNAME, recipients=[email])
        msg.body = f'Aqui está o código de autenticação de 2 fatores, se não houver solicitado, favor ignorar a mensagem: {code}'

        try:
            mail.send(msg)
            return jsonify({
                "message": "O código foi enviado para o email, verifique sua caixa de entrada!"}), 200
        except Exception as e:
            logging.error(f"Erro ao enviar o email: {str(e)}")
            return jsonify({"message": "Erro ao enviar o email"}), 500
    else:
        logging.warning(f"O email {email} não corresponde a uma conta existente")
        return jsonify({"message": "O email fornecido não corresponde a uma conta existente"}), 400


# Rota para autenticar com código 2FA
@auth2fa_bp.route('/auth2fa_login', methods=['POST'])
def auth2fa_login():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    user = usuarios.query.filter_by(email=email).first()

    if user:
        # Verifica se existe um código 2FA válido na tabela 2fa
        latest_2fa = two_fa.query.filter_by(user_id=user.id).order_by(two_fa.request_time.desc()).first()

        if latest_2fa and latest_2fa.code == code:
            # Verifica o tempo entre o horário de requisição e o tempo atual
            request_time = latest_2fa.request_time
            current_time = datetime.now()
            time_difference = current_time - request_time

            # Define o limite de tempo (10 minutos)
            time_limit = timedelta(minutes=10)

            if time_difference <= time_limit:
                # O código 2FA está correto e dentro do limite de tempo
                db.session.delete(latest_2fa)  # Remove a entrada 2FA do usuário após autenticação
                db.session.commit()
                return jsonify({"message": "Login bem-sucedido"}), 200
            else:
                logging.warning("Tempo limite para o código 2FA excedido")
                return jsonify({"message": "Tempo limite para o código 2FA excedido"}), 401
        else:
            logging.warning("Código 2FA inválido")
            return jsonify({"message": "Código 2FA inválido"}), 401
    else:
        logging.warning(f"O email {email} não corresponde a uma conta existente")
        return jsonify({"message": "O email fornecido não corresponde a uma conta existente"}), 400


# Função para limpar a tabela 2FA de um usuário
def clear_2fa_table(user_id):
    try:
        two_fa.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        print(f"Entrada 2FA do usuário {user_id} foi removida após 1 hora")
    except Exception as e:
        print(f"Erro ao remover a entrada 2FA do usuário {user_id}: {str(e)}")

