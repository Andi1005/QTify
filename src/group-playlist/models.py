import random, time, math 

from flask_sqlalchemy import SQLAlchemy


random.seed()

db = SQLAlchemy()


class Rooms(db.Model):
    pin = db.Column(db.Integer, primary_key=True)
    expires_at = db.Column(db.Integer, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    token_expires_at = db.Column(db.Integer, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)
    queue = db.relationship("Tracks", backref="room")
    skip = db.Column(db.Boolean)

    def __init__(self, access_token, token_expires_at, refresh_token, lifespan=12, pin_length=6, skip=False):
        self.access_token = access_token
        self.token_expires_at = token_expires_at
        self.refresh_token = refresh_token

        self.skip = skip
        self.pin = generate_pin(max(4, pin_length))
        if lifespan == -1:
            self.expires_at = math.inf
        else:
            lifespan = lifespan * 60 * 60 # Convert hours to seconds
            self.expires_at = time.time() + lifespan

    def to_dict(self):
        return {
            "pin": self.pin,
            "access_token": self.access_token,
            "token_expires_at": self.token_expires_at,
            "refresh_token": self.refresh_token
        }


class Tracks(db.Model):
    id = db.Column(db.String(128), primary_key=True) # The spotify ID
    room_pin = db.Column(db.Integer, db.ForeignKey("rooms.pin"))
    name = db.Column(db.String(128))
    artist = db.Column(db.String(128)) # The main artist
    artist_id = db.Column(db.String(128)) # The main artist 
    order = db.Column(db.Integer, autoincrement=True)

    def __repr__(self):
        return f"<Tracks '{self.name}'>"
    

def generate_pin(length):
    while True:
        new_pin = random.randrange(1000, 10**length)
        if not db.session.query(Rooms).filter_by(pin=new_pin).first():
            break
    return new_pin


def delete_old_rows():
    deleted_rooms = Rooms.query.where(Rooms.expires_at < time.time()).delete()
    deleted_tracks = Tracks.query.delete()
    db.session.commit()
    print(f"Deleted {deleted_rooms} expired rooms and {deleted_tracks} tracks")
