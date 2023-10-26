from app import db

class login_attempts(db.Model):
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(255), db.ForeignKey('usuarios.username'), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, ip_address, username, timestamp):
        self.ip_address = ip_address
        self.username = username
        self.timestamp = timestamp
