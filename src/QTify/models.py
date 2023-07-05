import random
import time
import math
import datetime


from flask_sqlalchemy import SQLAlchemy


random.seed()

db = SQLAlchemy()


class Rooms(db.Model):
    """Stores information about all activ rooms"""

    pin = db.Column(db.Integer, primary_key=True)
    expires_at = db.Column(db.Integer, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    token_expires_at = db.Column(db.Integer, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)
    queue = db.relationship("Tracks", backref="room", lazy="dynamic")
    queue_length = db.Column(db.Integer, nullable=False)
    position_in_queue = db.Column(db.Integer, nullable=False, default=0)
    skip = db.Column(db.Boolean)

    def __init__(
        self,
        access_token,
        token_expires_at,
        refresh_token,
        lifespan=12,
        pin_length=6,
        skip=False,
    ):
        self.access_token = access_token
        self.token_expires_at = token_expires_at
        self.refresh_token = refresh_token
        self.position_in_queue = 0
        self.queue_length = 0

        self.skip = skip
        self.pin = generate_pin(max(4, pin_length))
        if lifespan == -1:
            self.expires_at = math.inf
        else:
            lifespan = lifespan * 60 * 60  # Convert hours to seconds
            # TODO: replace time.time() with datetime.now()
            self.expires_at = time.time() + lifespan

    def __repr__(self):
        return f"<Rooms '{self.pin}'>"

    def to_dict(self):
        return {
            "pin": self.pin,
            "access_token": self.access_token,
            "token_expires_at": self.token_expires_at,
            "refresh_token": self.refresh_token,
        }


class Tracks(db.Model):
    """List of Tracks in a queue, used for recommendations, caching and shaping of the queue"""

    id = db.Column(db.String(128), primary_key=True)  # The spotify ID
    room_pin = db.Column(db.Integer, db.ForeignKey("rooms.pin"), primary_key=True)

    # At wich position in this queue the song is
    position = db.Column(db.Integer, autoincrement=True, nullable=False)
    time_added = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    name = db.Column(db.String(128))
    artist = db.Column(db.String(128))  # The main artist
    artist_id = db.Column(db.String(128))  # The main artist
    image_url = db.Column(db.String(128))
    color = db.Column(db.String(8))  # in hexadecimal

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        queue_length = Rooms.query.filter_by(pin=self.room_pin).first().queue_length
        self.position = queue_length
        Rooms.query.filter_by(pin=self.room_pin).update(
            {"queue_length": queue_length + 1}
        )

        db.session.commit()

    def __repr__(self):
        return f"<Tracks '{self.name}' at position {self.position}>"


def generate_pin(length):
    while True:
        new_pin = random.randrange(1000, 10**length)
        if not db.session.query(Rooms).filter_by(pin=new_pin).first():
            break
    return new_pin


def delete_old_rows():
    expired_rooms = Rooms.query.where(Rooms.expires_at < time.time())
    for expired_room in expired_rooms:
        Tracks.query.where(Tracks.room_pin == expired_room.pin).delete()
    deleted_rooms = expired_rooms.delete()
    db.session.commit()
    print(f"Deleted {deleted_rooms} expired rooms.")
