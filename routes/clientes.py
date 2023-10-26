from flask import Blueprint, request, jsonify
from app import db
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from commons import check_profile
from models.clientes import clientes
from sqlalchemy import asc, desc

# Criação do blueprint para as rotas de clientes
clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/clientes', methods=['POST'])
@jwt_required()
@check_profile(profile=0)
def criar_cliente():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        data = request.get_json()

        # Verifica se o campo "nome_completo" está presente no JSON
        if 'nome_completo' not in data:
            return jsonify({"message": "O campo 'nome_completo' é obrigatório"}), 400

        # Verifica se o valor do campo "nome_completo" é uma string
        if not isinstance(data['nome_completo'], str):
            return jsonify({"message": "O campo 'nome_completo' deve ser uma string"}), 400

        nome_completo = data['nome_completo']

        # Verifica se já existe um cliente com o mesmo nome completo usando SQLAlchemy
        existing_client = clientes.query.filter_by(nome_completo=nome_completo).first()

        if existing_client:
            return jsonify({"message": "Um cliente com o mesmo nome já existe"}), 400

        # Se não existe, insira o novo cliente no banco de dados usando SQLAlchemy
        identificador = data.get('identificador', '')  # Pode ser uma string vazia se não for fornecida
        new_client = clientes(nome_completo=nome_completo, identificador=identificador)
        db.session.add(new_client)
        db.session.commit()

        return jsonify({"message": "Cliente criado com sucesso"}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para listar todos os clientes
@clientes_bp.route('/clientes', methods=['GET'])  #OK admin
@jwt_required()
@check_profile(profile=0)
def listar_clientes():
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Obtenha o parâmetro 'order' da consulta, padrão para 'asc'
        order = request.args.get('order', 'asc')

        # Construa a consulta SQLAlchemy com base na direção da ordenação
        if order == 'asc':
            clientes_list = db.session.query(clientes).order_by(asc(clientes.nome_completo)).all()
        else:
            clientes_list = db.session.query(clientes).order_by(desc(clientes.nome_completo)).all()

        # Crie uma lista de dicionários com os dados dos clientes
        clientes_data = [
            {
                'id': cliente.id,
                'nome_completo': cliente.nome_completo,
                'identificador': cliente.identificador,
            }
            for cliente in clientes_list
        ]

        return jsonify({'clientes': clientes_data}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


@clientes_bp.route('/clientes/<int:cliente_id>', methods=['GET']) #OK
@jwt_required()
@check_profile(profile=0)
def mostrar_cliente(cliente_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Use SQLAlchemy para buscar o cliente por ID
        cliente = clientes.query.get(cliente_id)

        if cliente:
            cliente_data = {
                'id': cliente.id,
                'nome_completo': cliente.nome_completo,
                'identificador': cliente.identificador,
            }
            return jsonify({'cliente': cliente_data}), 200
        else:
            return jsonify({"message": "Cliente não encontrado"}), 404
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


@clientes_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])  #ok
@jwt_required()
@check_profile(profile=0)
def atualizar_cliente(cliente_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        data = request.get_json()

        # Use SQLAlchemy para buscar o cliente por ID
        cliente = clientes.query.get(cliente_id)

        if not cliente:
            return jsonify({'message': 'Cliente não encontrado!'}), 404

        if 'nome_completo' in data:
            cliente.nome_completo = data['nome_completo']

        if 'identificador' in data:
            cliente.identificador = data['identificador']

        # Commit as alterações no banco de dados
        db.session.commit()

        return jsonify({"message": "Cliente atualizado com sucesso"}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401


# Rota para excluir um cliente por ID
@clientes_bp.route('/clientes/<int:cliente_id>', methods=['DELETE']) #OK
@jwt_required()
@check_profile(profile=0)
def deletar_cliente(cliente_id):
    try:
        verify_jwt_in_request()  # Verificação se o token é válido

        # Verifica se o painel com o ID especificado existe
        cliente = clientes.query.get(cliente_id)

        if not cliente:
            return jsonify({'message': 'Cliente não encontrado!'}), 404

        # Exclui o painel
        db.session.delete(cliente)
        db.session.commit()

        return jsonify({'message': 'Cliente excluído com sucesso'})

    except Exception as e:
        print(e)
        return jsonify({"message": "Usuário não autenticado"}), 401
