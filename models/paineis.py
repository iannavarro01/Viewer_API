from app import db

class paineis(db.Model):
    __tablename__ = 'paineis'

    id = db.Column(db.Integer, primary_key=True)
    nome_painel = db.Column(db.String(255), nullable=False)
    url_power_bi = db.Column(db.String(255), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos.id'))
    ordem = db.Column(db.Integer)

    def __init__(self, nome_painel, url_power_bi, cliente_id, grupo_id, ordem):
        self.nome_painel = nome_painel
        self.url_power_bi = url_power_bi
        self.cliente_id = cliente_id
        self.grupo_id = grupo_id
        self.ordem = ordem
