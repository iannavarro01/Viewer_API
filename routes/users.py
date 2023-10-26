# Importações necessárias
import logging

from flask import Blueprint, request, jsonify
from app import db, bcrypt
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
from commons import check_profile, check_profiles
from models.usuarios import usuarios
from models.user_panel_association import user_panel_association
from models.user_panel_deactivate import user_panel_deactivate

# CRUD para gerenciar perfis de usuário

# Criação do blueprint para as rotas de perfis de usuário
users_bp = Blueprint('users', __name__)


# Rota para listar todos os perfis de usuário
@users_bp.route('/users', methods=['GET'])
@jwt_required()
@check_profile(profile=0)
def list_users():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Consulta todos os usuários usando SQLAlchemy
        users = usuarios.query.all()

        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'nome': user.nome,
                'username': user.username,
                'email': user.email,
                'cliente_id': user.cliente_id,
                'perfil': user.perfil,
                'status': user.status
            }
            user_list.append(user_data)

        return jsonify({'users': user_list}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para listar elementos de um único usuário
@users_bp.route('/users/<int:user_id>', methods=['GET'])  # OK
@jwt_required()
@check_profile(profile=0)
def get_user_by_id(user_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Consulta o usuário pelo ID usando SQLAlchemy
        user = usuarios.query.get(user_id)

        if not user:
            return jsonify({"message": "Usuário não encontrado"}), 404

        # Consulta para buscar os painel_id's associados a este usuário na tabela user_panel_association
        panel_associations = user_panel_association.query.filter_by(user_id=user_id).all()
        panel_ids = [association.painel_id for association in panel_associations]

        user_data = {
            'id': user.id,
            'nome': user.nome,
            'username': user.username,
            'email': user.email,
            'cliente_id': user.cliente_id,
            'perfil': user.perfil,
            'status': user.status,
            'painel_ids': panel_ids
        }

        return jsonify({'user': user_data}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao buscar usuário"}), 500


@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@check_profile(profile=0)
def update_user(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        # Continuar com a atualização apenas se o perfil do usuário autenticado for administrador (perfil 0)
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': 'Perfil de usuário autenticado não encontrado!'}), 404

        if current_user.perfil != 0:
            return jsonify({"message": "Apenas administradores podem atualizar usuários"}), 403

        # Obtém os dados da solicitação
        updated_username = request.json.get('username')
        updated_email = request.json.get('email')
        updated_nome = request.json.get('nome')
        updated_painel_ids = request.json.get('painel_ids', [])
        updated_password = request.json.get('password')

        # Atualização de senha
        if updated_password:
            hashed_password = bcrypt.generate_password_hash(updated_password).decode('utf-8')
        else:
            hashed_password = None

        # Atualiza os campos
        user_to_update = usuarios.query.get(user_id)

        if updated_username is not None:
            user_to_update.username = updated_username

        if updated_email is not None:
            user_to_update.email = updated_email

        if updated_nome is not None:
            user_to_update.nome = updated_nome

        if hashed_password is not None:
            user_to_update.password = hashed_password

        db.session.commit()

        # Atualiza as associações de painéis
        user_panel_association.query.filter_by(user_id=user_id).delete()
        for painel_id in updated_painel_ids:
            association = user_panel_association(user_id=user_id, painel_id=painel_id)
            db.session.add(association)

        db.session.commit()

        # Retorna os dados atualizados do usuário
        updated_user = usuarios.query.get(user_id)
        user = {
            'id': updated_user.id,
            'nome': updated_user.nome,
            'username': updated_user.username,
            'email': updated_user.email,
            'perfil': updated_user.perfil,
            'cliente_id': updated_user.cliente_id,
            'painel_ids': updated_painel_ids  # Retorna os novos painel_ids
        }

        return jsonify({'user': user}), 200

    except Exception as e:
        print(e)
        # Log de erro
        logging.error(f"Erro ao atualizar o perfil {user_id}: {str(e)}")

        return jsonify({"message": "Erro ao atualizar o usuário"}), 500


# Rota para ativar o STATUS do usuário
@users_bp.route('/users/status', methods=['PATCH']) #Ok
@jwt_required()
@check_profile(profile=0)
def update_user_status():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Verifique se a solicitação inclui o campo 'user_id' e 'status' no JSON
        data = request.get_json()
        user_id = data.get('user_id')
        status = data.get('status')

        if user_id is None or status is None or not isinstance(status, bool):
            return jsonify({
                'error': 'A requisição deve incluir os campos "user_id" e "status" como um booleano (True ou False)'}), 400

        # Atualiza o status do usuário com o valor fornecido
        updated_user = usuarios.query.get(user_id)

        if updated_user is None:
            return jsonify({"message": "Usuário não encontrado"}), 404

        updated_user.status = status
        db.session.commit()

        return jsonify({'user': {
            'id': updated_user.id,
            'nome': updated_user.nome,
            'username': updated_user.username,
            'email': updated_user.email,
            'status': updated_user.status  # Status atualizado
        }}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao atualizar o status do usuário"}), 500


# Rota para remover a visualização de um Painel(FEITA PELO USUÁRIO)
@users_bp.route('/users/paineis/deactivate', methods=['POST']) #OK
@jwt_required()
@check_profiles(profiles=[0, 1])  # Apenas administradores podem acessar esta rota
def deactivate_user_panels():
    try:
        # Verifica se o token é válido
        verify_jwt_in_request()

        # Obtém o ID do usuário autenticado
        current_user_id = get_jwt_identity()

        # Certifique-se de que os dados foram enviados no corpo da solicitação como JSON
        if not request.is_json:
            return jsonify({"message": "Dados devem ser enviados como JSON"}), 400

        # Obtém a lista de IDs dos painéis que o usuário deseja desativar a partir dos dados da solicitação
        panel_ids_to_deactivate = request.json.get("painel_ids", [])

        if not panel_ids_to_deactivate:
            return jsonify({"message": "Nenhum painel foi especificado para desativação"}), 400

        # Remove as entradas existentes na tabela user_panel_deactivate para o usuário atual
        user_panel_deactivate.query.filter_by(user_id=current_user_id).delete()

        # Insere as novas entradas na tabela user_panel_deactivate
        for panel_id in panel_ids_to_deactivate:
            association = user_panel_deactivate(user_id=current_user_id, painel_id=panel_id)
            db.session.add(association)

        db.session.commit()

        return jsonify({"message": "Painéis desativados com sucesso"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao desativar painéis"}), 500


@users_bp.route('/users/paineis/deactivate/<int:user_id>', methods=['GET'])
@jwt_required()
@check_profiles(profiles=[0, 1])
def get_user_panel_deactivations(user_id):
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()

        # Verifica se o usuário autenticado é um cliente (perfil 1)
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': 'Perfil de usuário autenticado não encontrado!'}), 404

        if current_user.perfil == 1:
            if current_user_id != user_id:
                return jsonify({"message": "Você só pode ver suas próprias desativações de painéis"}), 403

        # Consulta o banco de dados para obter as desativações de painéis por user_id
        deactivations = user_panel_deactivate.query.filter_by(user_id=user_id).all()

        if not deactivations:
            return jsonify({"message": "Nenhuma desativação de painel encontrada para o usuário"}), 404

        # Organize os dados da consulta em uma lista de dicionários
        deactivations_list = [{"user_id": deactivation.user_id, "painel_id": deactivation.painel_id} for deactivation in deactivations]

        return jsonify({"deactivations": deactivations_list}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao obter desativações de painéis"}, 500)


# Rota para deletar um perfil de usuário por ID
@users_bp.route('/users/<int:user_id>', methods=['DELETE']) #OK
@jwt_required()
@check_profile(profile=0)
def delete_user(user_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido
        current_user_id = get_jwt_identity()

        # Verifique se o usuário autenticado é um administrador (perfil 0)
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({'error': 'Perfil de usuário autenticado não encontrado!'}), 404

        if current_user.perfil != 0:
            return jsonify({"message": "Apenas administradores podem excluir usuários"}), 403

        # Verifique se o usuário que deseja excluir existe
        user_to_delete = usuarios.query.get(user_id)

        if not user_to_delete:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # Primeiro, exclua as associações do usuário na tabela user_panel_association
        user_panel_association.query.filter_by(user_id=user_id).delete()

        # Em seguida, exclua o usuário na tabela usuarios
        db.session.delete(user_to_delete)
        db.session.commit()

        return jsonify({'message': 'Usuário excluído com sucesso'}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao excluir o usuário"}), 500
