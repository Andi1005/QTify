import random

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Rooms(db.Model):
    pin = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.String(128), nullable=False)
    refresh_token = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(16), default=None)
    tracks_in_queue = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, access_token, expires_at, refresh_token):
        self.pin = random.randrange(1000, 9999) # Not unique!
        self.access_token = access_token
        self.expires_at = expires_at
        self.refresh_token = refresh_token

    def to_dict(self):
        return {
            "pin": self.pin,
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "refresh_token": self.refresh_token
        }