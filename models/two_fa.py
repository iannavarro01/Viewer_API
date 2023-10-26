from app import db


class two_fa(db.Model):
    __tablename__ = '2fa'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(255), nullable=True)
    code = db.Column(db.String(6), nullable=True)
    request_time = db.Column(db.TIMESTAMP, nullable=True)

    def __init__(self, user_id, username, code, request_time):
        self.user_id = user_id
        self.username = username
        self.code = code
        self.request_time = request_time
