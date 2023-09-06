from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import timedelta
import mysql.connector
#importa as dependências necessáriass



app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configurações do Banco de Dados local
db = mysql.connector.connect(
    host="localhost",
    user="Ian",
    password="Ilovestanlee121",
    database="users",
    auth_plugin='mysql_native_password'
)

# Configure as configurações do JWT após a criação do objeto app
app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)


# Função para gerar um token JWT para redefinição de senha
def generate_reset_token(user_id):
    reset_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=1))
    return reset_token


# Rota de registro de usuário
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Aqui há uma verificação se o usuário ou email já existem no banco de dados
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users.usuarios WHERE username = %s OR email = %s", (username, email))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"message": "Usuário ou email já existentes"}), 400

    # Aqui a senha fica criptografada usando Bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Código que insere o novo usuário no banco de dados:
    cursor.execute("INSERT INTO users.usuarios (username, email, password) VALUES (%s, %s, %s)",
                   (username, email, hashed_password))
    db.commit()
    cursor.close()

    return jsonify({"message": "Registro bem-sucedido"}), 201


# Rota de login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Verifica as credenciais do usuário
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user[3], password):
        # Crie um token de acesso
        access_token = create_access_token(identity=user[0])  # Usa o ID do usuário como identidade
        return jsonify({"Utilize seu token de acesso, access_token": access_token}), 200
    else:
        return jsonify({"message": "Credenciais inválidas"}), 401


# Rota protegida com JWT
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        verify_jwt_in_request()  # Verifica se o token é válido

        current_user_id = get_jwt_identity()  # Obtem a identidade (ID do usuário) do token JWT

        # Recupera o nome de usuário do usuário autenticado a partir do banco de dados
        cursor = db.cursor()
        cursor.execute("SELECT username FROM usuarios WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if user:
            username = user[0]
            return jsonify({"message": f"Bem-vindo, {username}"}), 200
        else:
            return jsonify({"message": "Usuário não encontrado"}), 404

    except Exception as e:
        return jsonify({"message": "Token JWT inválido ou usuário não autenticado"}), 401


# Rota de solicitação de redefinição de senha
@app.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    email = data.get("email")

    # Verifica se o email existe no banco de dados
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        # Gera um token exclusivo para redefinição de senha
        reset_token = create_access_token(identity=user[0], expires_delta=timedelta(hours=1))

        # Envia um email com o link de redefinição de senha contendo o token (Ainda precisa ser implementada)

        return jsonify({"message": "Um email com instruções de redefinição de senha foi enviado"}), 200
    else:
        return jsonify({"message": "O email fornecido não corresponde a uma conta existente"}), 400

# Rota para apresentar o formulário de redefinição de senha
@app.route('/reset_password/<reset_token>', methods=['GET'])
def reset_password_form(reset_token):
    try:
        verify_jwt_in_request()  # Verifica se o token é válido

        current_user_id = get_jwt_identity()  # Obtem a identidade (ID do usuário) do token JWT

        if current_user_id is not None:
            # Token válido, apresente o formulário de redefinição de senha
            return jsonify({"message": "Apresente o formulário de redefinição de senha"}), 200
        else:
            return jsonify({"message": "Token de redefinição de senha inválido ou expirado"}), 400

    except Exception as e:
        return jsonify({"message": "Token JWT inválido ou usuário não autenticado"}), 401

# Rota para redefinir a senha
@app.route('/reset_password/<reset_token>', methods=['POST'])
def reset_password(reset_token):
    try:
        verify_jwt_in_request()  # Verifica se o token é válido

        current_user_id = get_jwt_identity()  # Obtem a identidade (ID do usuário) do token JWT

        if current_user_id is not None:
            # Token válido, atualize a senha no banco de dados
            data = request.get_json()
            new_password = data.get("new_password")

            # Implemente a lógica para atualizar a senha no banco de dados aqui...
            # Por exemplo, você pode usar o current_user_id para identificar o usuário e atualizar a senha no banco de dados.

            return jsonify({"message": "Senha redefinida com sucesso"}), 200
        else:
            return jsonify({"message": "Token de redefinição de senha inválido ou expirado"}), 400

    except Exception as e:
        return jsonify({"message": "Token JWT inválido ou usuário não autenticado"}), 401

if __name__ == '__main__':
    app.run(debug=True)
