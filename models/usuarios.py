from app import db
from app import bcrypt

class usuarios(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    perfil = db.Column(db.Integer, default=0)
    status = db.Column(db.Boolean, default=False)

    # Função para criptografar a senha
    def hash_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Função para verificar a senha
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __init__(self, nome, username, email, password, cliente_id=None, perfil=0, status=False):
        self.nome = nome
        self.username = username
        self.email = email
        self.password = password
        self.cliente_id = cliente_id
        self.perfil = perfil
        self.status = status


