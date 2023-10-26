# models/vw_user_panel.py
from app import db

class vw_user_panel(db.Model):
    __tablename__ = 'vw_user_panel'

    id = db.Column(db.Integer, primary_key=True)
    nome_painel = db.Column(db.String(255))
    url_power_bi = db.Column(db.String(255))
    grupo_id = db.Column(db.Integer)
    ordem = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    nomeGrupo = db.Column(db.String(255))
    isDeactivated = db.Column(db.Integer)