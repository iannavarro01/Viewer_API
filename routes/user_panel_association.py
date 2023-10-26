from flask import Blueprint, request, jsonify
from app import db
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from commons import check_profile

#ROTA NÃO UTILIZADA

# Criação do blueprint para as rotas de associação entre usuário e painel
user_panel_association_bp = Blueprint('user_panel_association', __name__)

# Rota para criar uma nova associação entre usuário e painel
@user_panel_association_bp.route('/user_panel_association', methods=['POST'])
@jwt_required()
@check_profile(profile=0)  # Certifique-se de ajustar o perfil apropriado
def create_user_panel_association():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        data = request.get_json()
        user_id = data.get('user_id')
        panel_id = data.get('panel_id')

        # Verifique se o usuário e o painel existem (você pode personalizar isso)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.execute("SELECT * FROM paineis WHERE id = %s", (panel_id,))
        panel = cursor.fetchone()

        if not user or not panel:
            return jsonify({'error': 'Usuário ou painel não encontrado'}), 404

        # Crie uma nova associação com can_view definido como False por padrão
        cursor.execute("INSERT INTO user_panel_association (user_id, panel_id, can_view, adm_can_view) VALUES (%s, %s, %s, %s)",
                       (user_id, panel_id, False, True))  # Defina can_view como False por padrão
        db.commit()

        cursor.close()

        return jsonify({'message': 'Associação criada com sucesso'}), 201

    except Exception as e:
        return jsonify({'error': 'Erro ao criar associação'}), 500

# Rota para atualizar uma associação entre usuário e painel com base nas permissões de admin
@user_panel_association_bp.route('/user_panel_association/<int:id>', methods=['PUT'])
@jwt_required()
@check_profile(profile=0)  # Certifique-se de ajustar o perfil apropriado para admin
def update_user_panel_association(id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        data = request.get_json()
        user_id = data.get('user_id')
        panel_id = data.get('panel_id')
        adm_can_view = data.get('adm_can_view')

        # Verifique se a associação existe
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user_panel_association WHERE id = %s", (id,))
        association = cursor.fetchone()

        if not association:
            return jsonify({'error': 'Associação não encontrada'}), 404

        # Atualize o valor de adm_can_view
        cursor.execute("UPDATE user_panel_association SET user_id = %s, panel_id = %s, adm_can_view = %s WHERE id = %s",
                       (user_id, panel_id, adm_can_view, id))
        db.commit()

        # Verifique o valor de adm_can_view
        if adm_can_view:
            can_view = data.get('can_view', False)  # Padrão é False
        else:
            can_view = False

        # Atualize o valor de can_view com base nas permissões de admin
        cursor.execute("UPDATE user_panel_association SET can_view = %s WHERE id = %s", (can_view, id))
        db.commit()

        cursor.close()

        return jsonify({'message': 'Associação atualizada com base nas permissões de admin'}), 200

    except Exception as e:
        return jsonify({'error': 'Erro ao atualizar associação'}), 500

# Rota para excluir uma associação entre usuário e painel
@user_panel_association_bp.route('/user_panel_association/<int:id>', methods=['DELETE'])
@jwt_required()
@check_profile(profile=0)  # Certifique-se de ajustar o perfil apropriado para admin
def delete_user_panel_association(id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Verifique se a associação existe
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user_panel_association WHERE id = %s", (id,))
        association = cursor.fetchone()

        if not association:
            return jsonify({'error': 'Associação não encontrada'}), 404

        # Exclua a associação
        cursor.execute("DELETE FROM user_panel_association WHERE id = %s", (id,))
        db.commit()

        cursor.close()

        return jsonify({'message': 'Associação excluída com sucesso'}), 200

    except Exception as e:
        return jsonify({'error': 'Erro ao excluir associação'}), 500
