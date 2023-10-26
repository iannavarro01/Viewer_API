from app import db

class grupos(db.Model):
    __tablename__ = 'grupos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)

    def __init__(self, nome):
        self.nome = nome