from app import db

class clientes(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_completo = db.Column(db.String(255), nullable=False)
    identificador = db.Column(db.String(255), nullable=False)

    def __init__(self, nome_completo, identificador):
        self.nome_completo = nome_completo
        self.identificador = identificador