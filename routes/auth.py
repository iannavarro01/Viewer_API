# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from app import bcrypt, db
from datetime import timedelta, datetime
import schedule
import re
from models.usuarios import usuarios
from models.login_attempts import login_attempts
from models.user_panel_association import user_panel_association
from commons.decorators import check_profiles, check_profile

# Criação do blueprint para as rotas de autenticação
auth_bp = Blueprint('auth', __name__)

# Definição de constantes para controle de login malsucedido
MAX_LOGIN_ATTEMPTS = 5  #Máximo de tentativas de login
BLOCK_TIME_MINUTES = 2  #Tempo de bloqueio de entrada

def get_failed_login_attempts(username, ip_address):
    cutoff_time = datetime.now() - timedelta(minutes=BLOCK_TIME_MINUTES)
    count = login_attempts.query.filter(login_attempts.username == username,
                                       login_attempts.ip_address == ip_address,
                                       login_attempts.timestamp >= cutoff_time).count()
    return count

# Função para registrar uma tentativa de login malsucedida
def register_failed_login_attempt(username, ip_address):
    new_attempt = login_attempts(ip_address=ip_address, username=username, timestamp=datetime.now())
    db.session.add(new_attempt)
    db.session.commit()

# Função para limpar tentativas de login malsucedidas
def clear_failed_login_attempts(username=None):
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        if username:
            login_attempts.query.filter(login_attempts.username == username,
                                       login_attempts.timestamp <= cutoff_time).delete()
        else:
            login_attempts.query.filter(login_attempts.timestamp <= cutoff_time).delete()

        db.session.commit()
        if username:
            print(f"Tentativas malsucedidas limpas para o usuário {username}")
        else:
            print("Tentativas malsucedidas de todos os usuários foram limpas")
    except Exception as e:
        print(f"Erro ao limpar tentativas malsucedidas: {str(e)}")



# Rota para registro de usuário
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Verifica se todos os campos obrigatórios estão presentes na solicitação
    campos_obrigatórios = ['nome', 'username', 'email', 'password']

    for campo in campos_obrigatórios:
        if campo not in data or not data[campo].strip():
            return jsonify({"message": f"O campo '{campo}' não pode estar vazio"}), 400

    nome = data.get("nome")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Verificação se o usuário ou email já existem no banco de dados
    existing_user = usuarios.query.filter_by(username=username).first() or usuarios.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({"message": "Usuário ou email já existentes"}), 401

    # Verificações individuais para a senha
    error_messages = []

    if len(password) < 8:
        error_messages.append("A senha deve ter no mínimo 8 caracteres")

    if not any(char.isupper() for char in password):
        error_messages.append("A senha deve conter pelo menos uma letra maiúscula")

    if not any(char.isdigit() for char in password):
        error_messages.append("A senha deve conter pelo menos um número")

    if not any(char in '!@#$%^&*(),.?":{}|<>' for char in password):
        error_messages.append("A senha deve conter pelo menos um símbolo")

    if error_messages:
        return jsonify({"message": ", ".join(error_messages)}), 401

    # Criptografia da senha usando Bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Inserção do novo usuário no banco de dados com perfil=1 (cliente) e status='Inativo'
    new_user = usuarios(nome=nome, username=username, email=email, password=hashed_password, perfil=1, status=0)
    db.session.add(new_user)
    db.session.commit()

    # Retorno da mensagem JSON de registro bem-sucedido
    return jsonify({"message": "Registro bem-sucedido"})

@auth_bp.route('/cadastrar', methods=['POST']) #OK
@jwt_required()
@check_profile(profile=0)
def cadastrar():
    try:
        verify_jwt_in_request()
        data = request.get_json()

        nome = data.get("nome")
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        cliente_id = data.get("cliente_id")
        painel_ids = data.get("painel_ids")

        # Verificação se o usuário ou email já existem no banco de dados
        existing_user = usuarios.query.filter((usuarios.username == username) | (usuarios.email == email)).first()

        if existing_user:
            return jsonify({"message": "Usuário ou email já existentes"}), 402

        # Criptografia da senha usando Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Inserção do novo usuário no banco de dados com perfil=1 (cliente) e status='Inativo'
        new_user = usuarios(nome=nome, username=username, email=email, password=hashed_password, cliente_id=cliente_id,
                            perfil=1, status=0)
        db.session.add(new_user)
        db.session.commit()

        # Obtenha o ID do usuário recém-criado
        user_id = new_user.id

        # Associe os painéis ao novo usuário
        if painel_ids:
            if not isinstance(painel_ids, list):
                painel_ids = [painel_ids]  # Transforma em uma lista se não for

            for painel_id in painel_ids:
                association = user_panel_association(user_id=user_id, painel_id=painel_id)
                db.session.add(association)

        db.session.commit()

        # Retorno da mensagem JSON de registro bem-sucedido
        return jsonify({"message": "Cadastro de usuário bem-sucedido"})
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401





# Rota de login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    ip_address = request.remote_addr  # Obtém o endereço IP do cliente

    # Verificação das tentativas de login malsucedidas
    failed_login_attempts = get_failed_login_attempts(username, ip_address)

    if failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
        # Usuário ou endereço IP bloqueado temporariamente(2 minutos)
        return jsonify(
            {"message": "Número máximo de tentativas de login atingido. Tente novamente mais tarde."}), 401

    # Verificação das credenciais do usuário
    user = usuarios.query.filter_by(username=username).first()

    if user:
        # Verifica se o usuário está ativo (status 1)
        if user.status == 0:
            return jsonify({"message": "Usuário aguardando ativação"}), 401

    if user and user.check_password(password):
        # Login bem-sucedido, agora limpe as tentativas malsucedidas apenas para este usuário
        clear_failed_login_attempts(username)
        # Criação de um token de acesso
        userDict = {'id': user.id, 'nome': user.nome, 'username': user.username, 'email': user.email,
                    'cliente_id': user.cliente_id, 'perfil': user.perfil, 'status': user.status}
        access_token = create_access_token(identity=user.id, additional_claims=userDict)  # Usa o ID do usuário como identidade
        return jsonify({"Utilize seu token de acesso": access_token}), 200
    else:
        register_failed_login_attempt(username, ip_address)  # Registra as tentativas de login mal sucedidas
        return jsonify({"message": "Credenciais inválidas"}), 401

@auth_bp.route('/dashboards', methods=['GET'])
@jwt_required()
@check_profiles(profiles=[0, 1])
def protected():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        current_user_id = get_jwt_identity()  # Obtenção da identidade (ID do usuário) do token JWT

        # Recuperação do nome de usuário do usuário autenticado usando SQLAlchemy
        current_user = usuarios.query.get(current_user_id)

        if current_user:
            username = current_user.username
            return jsonify({"message": f"Bem-vindo, {username}"}), 200
        else:
            return jsonify({"message": "Usuário não encontrado"}), 404

    except Exception as e:
        return jsonify({"message": "Usuário não autenticado"}), 401
