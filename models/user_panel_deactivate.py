from app import db
from sqlalchemy import BigInteger, Column

class user_panel_deactivate(db.Model):
    __tablename__ = 'user_panel_deactivate'

    id = Column(BigInteger, primary_key=True, autoincrement=True, info={'unsigned': True})
    user_id = db.Column(db.Integer, nullable=True)
    painel_id = db.Column(db.Integer, nullable=True)

    def __init__(self, user_id, painel_id):
        self.user_id = user_id
        self.painel_id = painel_id
