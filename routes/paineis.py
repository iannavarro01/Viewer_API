from flask import Blueprint, request, jsonify, current_app
from app import db
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity # Importações necessárias
import logging
from commons.decorators import check_profile, check_profiles
from models.paineis import paineis
from models.clientes import clientes
from models.usuarios import usuarios
from models.grupos import grupos
from models.vw_user_panel import vw_user_panel
from sqlalchemy.orm import joinedload


# Criação do blueprint para as rotas de painéis
paineis_bp = Blueprint('paineis', __name__)


# Rota para criar um novo painel
@paineis_bp.route('/paineis', methods=['POST']) #OK
@jwt_required()
@check_profile(profile=0)
def criar_painel():
    try:
        verify_jwt_in_request()
        data = request.get_json()

        campos_obrigatórios = ['nome_painel', 'url_power_bi', 'cliente_id', 'grupo_id']
        for campo in campos_obrigatórios:
            if campo not in data:
                return jsonify({"message": f"O campo '{campo}' é obrigatório"}), 401

        if not isinstance(data['cliente_id'], int):
            return jsonify({"message": "O campo 'cliente_id' deve ser um número inteiro"}), 400

        nome_painel = data['nome_painel']
        url_power_bi = data['url_power_bi']
        cliente_id = data['cliente_id']
        grupo_id = data['grupo_id']

        # Verificar se já existe um painel com o mesmo nome para o cliente/grupo específicos
        painel_existente = paineis.query.filter_by(nome_painel=nome_painel, cliente_id=cliente_id, grupo_id=grupo_id).first()

        if painel_existente:
            return jsonify({"message": "Já existe um painel com o mesmo nome para este cliente/grupo"}), 400

        # Consultar o valor máximo atual da coluna "ordem" para o cliente/grupo específico
        max_ordem = paineis.query.filter_by(cliente_id=cliente_id, grupo_id=grupo_id).with_entities(paineis.ordem).order_by(paineis.ordem.desc()).first()
        if max_ordem:
            max_ordem = max_ordem[0]
        else:
            max_ordem = 0

        # Incrementar o valor máximo em 1 para obter a próxima ordem
        nova_ordem = max_ordem + 1

        cliente = clientes.query.get(cliente_id)

        if not cliente:
            # Log para verificar se o cliente não foi encontrado
            current_app.logger.warning(f"Cliente com o ID {cliente_id} não encontrado")
            return jsonify({"message": "Cliente com o ID fornecido não encontrado"}), 404

        novo_painel = paineis(nome_painel=nome_painel, url_power_bi=url_power_bi, cliente_id=cliente_id, grupo_id=grupo_id, ordem=nova_ordem)
        db.session.add(novo_painel)
        db.session.commit()

        return jsonify({"message": "Painel criado com sucesso"}), 201

    except Exception as e:
        # Log para verificar exceções
        current_app.logger.error(f"Erro ao criar painel: {str(e)}")
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para listar os painéis
@paineis_bp.route('/paineis', methods=['GET']) #OK
@jwt_required()
@check_profile(profile=0)
def listar_paineis():
    try:
        verify_jwt_in_request()

        # Consultar o banco de dados para obter a lista de painéis usando o modelo paineis
        paineis_list = paineis.query.all()

        # Transformar os resultados em um formato de dicionário
        paineis_dict = [
            {
                'id': painel.id,
                'nome_painel': painel.nome_painel,
                'url_power_bi': painel.url_power_bi,
                'cliente_id': painel.cliente_id,
                'grupo_id': painel.grupo_id,
                'ordem': painel.ordem
            }
            for painel in paineis_list
        ]

        return jsonify({'paineis': paineis_dict}), 200

    except Exception as e:
        # Log de erro
        current_app.logger.error(f"Erro ao listar painéis: {str(e)}")
        return jsonify({"message": "Erro ao listar painéis"}), 500


# ROTA PARA VISUALIZAR UM PAINEL POR ID DO PAINEL
@paineis_bp.route('/paineis/<int:painel_id>', methods=['GET'])
@jwt_required()
@check_profiles(profiles=[0, 1])  # Apenas admins (perfil 0) e clientes (perfil 1) podem acessar esta rota
def visualizar_painel(painel_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        current_user_id = get_jwt_identity()

        # Obtem o cliente_id e o perfil do usuário autenticado com base no token
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "Usuário autenticado não encontrado"}), 404

        current_user_cliente_id = current_user.cliente_id
        current_user_perfil = current_user.perfil

        # Consultar o banco de dados para obter as informações do painel com o ID fornecido
        painel = paineis.query.get(painel_id)

        if not painel:
            return jsonify({"message": "Painel não encontrado"}), 404

        painel_cliente_id = painel.cliente_id

        # Verifica se o perfil do usuário autenticado é 0 (admin) ou se o cliente_id corresponde ao cliente do painel
        if current_user_perfil == 0 or current_user_cliente_id == painel_cliente_id:
            painel_info = {
                'id': painel.id,
                'nome_painel': painel.nome_painel,
                'url_power_bi': painel.url_power_bi,
                'cliente_id': painel_cliente_id,
                'grupo_id': painel.grupo_id,
                'ordem': painel.ordem
            }
            return jsonify({'painel': painel_info}), 200

        return jsonify({"message": "Você não tem permissão para acessar este painel"}), 403

    except Exception as e:
        # Log de erro
        current_app.logger.error(f"Erro ao visualizar o painel {painel_id}: {str(e)}")
        return jsonify({"message": "Erro ao visualizar o painel"}), 500


# ROTA PARA VISUALIZAÇÃO DE PAINÉIS DOS USUÁRIOS  #OK
@paineis_bp.route('/users/paineis/<int:user_id>', methods=['GET'])
@jwt_required()
@check_profiles(profiles=[0, 1])  # ADMINS têm acesso à visualização dos painéis disponíveis para qualquer user_id
def listar_paineis_por_usuario(user_id):
    try:
        current_user_id = get_jwt_identity()

        # Obter o cliente_id e o perfil do usuário autenticado com base no token
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "Usuário autenticado não encontrado"}), 404

        current_user_cliente_id = current_user.cliente_id
        current_user_perfil = current_user.perfil

        # Se o perfil do usuário autenticado for 0 (admin), não é necessário verificar user_id
        if current_user_perfil != 0:
            # Verifica se o user_id da URL é igual ao user_id do usuário autenticado
            if current_user_id != user_id:
                return jsonify({"message": "Você não tem permissão para acessar esta rota"}), 403

        # Consulta para selecionar os painéis associados ao cliente com base no user_id, com ordenação
        order = request.args.get('order', 'asc')  # Obtém o parâmetro 'order' da consulta, padrão para 'asc'
        paineis = (
            vw_user_panel.query
            .filter(vw_user_panel.user_id == user_id)
            .order_by(db.desc(vw_user_panel.ordem) if order == 'desc' else vw_user_panel.ordem)
            .all()
        )

        paineis_por_usuario = []
        grupo_atual = None
        grupoNome_atual = ""
        paineis_do_grupo = []

        for painel in paineis:
            if painel.grupo_id != grupo_atual:
                if grupo_atual is not None:
                    grupo_info = {
                        'grupo_id': grupo_atual,
                        'nomeGrupo': grupoNome_atual,
                        'paineis': paineis_do_grupo
                    }
                    paineis_por_usuario.append(grupo_info)
                grupo_atual = painel.grupo_id
                grupoNome_atual = painel.nomeGrupo
                paineis_do_grupo = []

            painel_info = {
                'id': painel.id,
                'nome_painel': painel.nome_painel,
                'url_power_bi': painel.url_power_bi,
                'ordem': painel.ordem,
                'isDeactivated': painel.isDeactivated
            }
            paineis_do_grupo.append(painel_info)

        if grupo_atual is not None:
            grupo_info = {
                'grupo_id': grupo_atual,
                'nomeGrupo': grupoNome_atual,
                'paineis': paineis_do_grupo
            }
            paineis_por_usuario.append(grupo_info)

        return jsonify(paineis_por_usuario)

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao listar os painéis de usuário"}), 500

#VISUALIZAR OS PAINÉIS ASSOCIADOS AO CLIENTE #OK
@paineis_bp.route('/clientes/paineis/<int:cliente_id>', methods=['GET'])
@jwt_required()
@check_profiles(profiles=[0, 1])
def listar_paineis_por_cliente(cliente_id):
    try:
        current_user_id = get_jwt_identity()

        # Obter o cliente_id e o perfil do usuário autenticado com base no token
        current_user = usuarios.query.get(current_user_id)

        if not current_user:
            return jsonify({"message": "Usuário autenticado não encontrado"}), 404

        current_user_cliente_id = current_user.cliente_id
        current_user_perfil = current_user.perfil

        # Se o perfil do usuário autenticado for 0 (admin), não é necessário verificar user_id
        if current_user_perfil != 0:
            if current_user_cliente_id != cliente_id:
                return jsonify({"message": "Você não tem permissão para acessar esta rota"}), 403

        order = request.args.get('order', 'asc')  # Obtém o parâmetro 'order' da consulta, padrão para 'asc'

        # Consulta para selecionar os painéis associados ao cliente com base no cliente_id, com ordenação
        paineis_result = (
            db.session.query(paineis, grupos.nome)
            .join(grupos, paineis.grupo_id == grupos.id)
            .filter(paineis.cliente_id == cliente_id)
            .order_by(db.asc(grupos.nome), db.desc(paineis.ordem) if order == 'desc' else db.asc(paineis.ordem))
            .all()
        )

        paineis_por_usuario = []
        grupo_atual = None
        paineis_do_grupo = []

        for painel, nome_grupo in paineis_result:
            if nome_grupo != grupo_atual:
                if grupo_atual is not None:
                    grupo_info = {
                        'grupo_nome': grupo_atual,
                        'paineis': paineis_do_grupo
                    }
                    paineis_por_usuario.append(grupo_info)
                grupo_atual = nome_grupo
                paineis_do_grupo = []

            painel_info = {
                'id': painel.id,
                'nome_painel': painel.nome_painel,
                'url_power_bi': painel.url_power_bi,
                'ordem': painel.ordem
            }
            paineis_do_grupo.append(painel_info)

        if grupo_atual is not None:
            grupo_info = {
                'grupo_nome': grupo_atual,
                'paineis': paineis_do_grupo
            }
            paineis_por_usuario.append(grupo_info)

        return jsonify(paineis_por_usuario)

    except Exception as e:
        print(e)
        return jsonify({"message": "Erro ao listar os painéis de usuário"}), 500



# Rota para atualizar um painel por ID
@paineis_bp.route('/paineis/<int:painel_id>', methods=['PUT']) #OK
@jwt_required()
@check_profile(profile=0)
def atualizar_painel(painel_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido
        data = request.get_json()

        # Verifica se o painel com o ID especificado existe
        painel = paineis.query.get(painel_id)

        if not painel:
            return jsonify({'message': 'Painel não encontrado!'}), 404

        # Atualiza apenas os campos especificados no corpo da solicitação
        for key, value in data.items():
            if hasattr(painel, key):
                setattr(painel, key, value)

        db.session.commit()

        return jsonify({'message': 'Painel atualizado com sucesso'})

    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


@paineis_bp.route('/paineis/<int:painel_id>', methods=['DELETE']) #OK
@jwt_required()
@check_profile(profile=0)
def deletar_painel(painel_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Verifica se o painel com o ID especificado existe
        painel = paineis.query.get(painel_id)

        if not painel:
            return jsonify({'message': 'Painel não encontrado!'}), 404

        # Exclui o painel
        db.session.delete(painel)
        db.session.commit()

        return jsonify({'message': 'Painel excluído com sucesso'})

    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


