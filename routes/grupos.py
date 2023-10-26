# Importações necessárias
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from app import db
from commons import check_profile
from models.grupos import grupos

# CRUD para gerenciamento dos grupos de painéis

# Criação do blueprint para as rotas de grupos
grupos_bp = Blueprint('grupos', __name__)

# Rota para criar um grupo de painéis
@grupos_bp.route('/grupos', methods=['POST'])
@jwt_required()
@check_profile(profile=0)
def criar_grupo():
    try:
        verify_jwt_in_request()
        data = request.get_json()
        nome = data.get("nome")

        if not nome:
            return jsonify({"message": "O campo 'nome' é obrigatório"}), 400

        # Verifica se o grupo com o mesmo nome já existe
        existing_group = grupos.query.filter_by(nome=nome).first()

        if existing_group:
            return jsonify({"message": "Um grupo com o mesmo nome já existe"}), 400

        # Crie um novo grupo de painel
        novo_grupo = grupos(nome=nome)
        db.session.add(novo_grupo)
        db.session.commit()

        return jsonify({"message": "Grupo de painel criado com sucesso"}), 201
    except Exception as e:
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para listar todos os grupos de painéis
@grupos_bp.route('/grupos', methods=['GET']) #ok
@jwt_required()
@check_profile(profile=0)
def listar_grupos():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Consulta todos os grupos usando SQLAlchemy
        grupos_list = grupos.query.all()

        grupos_info = [{"id": grupo.id, "nome": grupo.nome} for grupo in grupos_list]

        return jsonify({"grupos": grupos_info})
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para visualizar um grupo específico por grupo_id
@grupos_bp.route('/grupos/<int:grupo_id>', methods=['GET']) #OK
@jwt_required()
@check_profile(profile=0)
def visualizar_grupo(grupo_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Consulta o grupo pelo ID usando SQLAlchemy
        grupo = grupos.query.get(grupo_id)

        if not grupo:
            return jsonify({"message": "Grupo não encontrado"}), 404

        grupo_info = {"id": grupo.id, "nome": grupo.nome}

        return jsonify({"grupo": grupo_info}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao visualizar o grupo"}), 500

# Rota para atualizar um grupo de painel por ID
@grupos_bp.route('/grupos/<int:id>', methods=['PUT']) #ok
@jwt_required()
@check_profile(profile=0)
def atualizar_grupo(id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido
        data = request.get_json()
        novo_nome = data.get("nome")

        if not novo_nome:
            return jsonify({"message": "O campo 'nome' é obrigatório"}), 400

        # Consulta o grupo a ser atualizado usando SQLAlchemy
        grupo = grupos.query.get(id)

        if not grupo:
            return jsonify({'message': 'Grupo não encontrado!'}), 404

        # Atualiza o nome do grupo
        grupo.nome = novo_nome
        db.session.commit()

        return jsonify({"message": "Grupo atualizado com sucesso"})
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401

# Rota para deletar um grupo de painel por ID
@grupos_bp.route('/grupos/<int:id>', methods=['DELETE']) #OK
@jwt_required()
@check_profile(profile=0)
def deletar_grupo(id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Verifica se o painel com o ID especificado existe
        grupo = grupos.query.get(id)

        if not grupo:
            return jsonify({'message': 'Grupo de painéis não encontrado!'}), 404

        # Exclui o painel
        db.session.delete(grupo)
        db.session.commit()

        return jsonify({'message': 'Grupo de painéis excluído com sucesso'})

    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401





