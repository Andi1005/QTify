import json, functools, time
import asyncio

import requests
from flask import Blueprint
from flask import request, session, redirect, render_template, url_for, g, abort
from werkzeug.exceptions import HTTPException

from .models import db, Rooms, Tracks
from . import auth
from . import spotify_api as api


views = Blueprint("views", __name__)


def pin_required(func):
    """Wraps every view function, wich requires a room pin.
    This function checks if the provided pin is valid and if so,
    adds the pin and the corresponding room to g in the application context.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pin = request.args.get("pin", kwargs.get("pin"))
        if pin is None:
            abort(400)  # No pin in request

        room = db.session.query(Rooms).filter_by(pin=pin).first()
        if room is None:
            abort(404)  # Room not found in database

        if room.expires_at < time.time():
            Rooms.query.filter_by(pin=pin).delete()
            db.session.commit()
            abort(410)  # Room is expired

        g.pin = pin
        g.room = room

        return func(*args, **kwargs)

    return wrapper


@views.get("/")
def index():
    is_host = "host_of" in session
    return render_template("index.html", is_host=is_host)


@views.route("/create", methods=("GET", "POST"))
def create_room():
    if request.method == "POST":
        # Room settings will be temporarily saved in the session and retrieved when the user has completed the authorization process.
        # Validation is done in the redirect view, because in the meantime these settings could be changed.
        session["pin_length"] = request.form.get("pin_length")
        session["room_lifespan"] = request.form.get("lifespan")
        session["users_can_skip"] = request.form.get("skip")

        request_url = auth.request_user_authorization()
        return redirect(request_url)

    return render_template("create.html")


@views.get("/redirect")
def redirect_page():
    code = request.args.get("code")
    if code is None:
        abort(403)  # Inappropriate answer from accounts.spotify.com

    spotify_auth_data = auth.request_access_token(code)
    if not spotify_auth_data:
        abort(403)  # Inappropriate answer from accounts.spotify.com

    try:
        # Needs to be at least 4 digits long
        pin_length = max(int(session.pop("pin_length")), 4)
        room_lifespan = int(session.pop("room_lifespan"))
        users_can_skip = bool(session.pop("users_can_skip"))
    except:
        abort(400)  # Needed inforations are not in session or in wrong format

    room = Rooms(
        **spotify_auth_data,
        pin_length=pin_length,
        lifespan=room_lifespan,
        skip=users_can_skip
    )
    db.session.add(room)
    db.session.commit()

    session["host_of"] = room.pin

    return redirect(url_for("views.room", pin=room.pin))


@views.route("/host", methods=("GET", "POST"))
def host():
    if request.method == "GET":
        # Create a new room if you are not the owner of one
        if not "host_of" in session:
            return redirect(url_for("views.create_room"))

        pin = session["host_of"]
        found_room = Rooms.query.filter_by(pin=pin)
        if not found_room:
            session.pop("host_of")
            abort(404)

        return redirect(url_for("views.room", pin=pin))


@views.route("/sign-out", methods=("GET", "PUT"))
def sign_out():
    pin = session["host_of"]
    Rooms.query.filter_by(pin=pin).delete()
    db.session.commit()
    session.pop("host_of")

    if request.method == "GET":
        return redirect(url_for("views.index"))
    else:
        return "OK", 200


@views.route("/join", methods=("GET", "POST"))
def join():
    if request.method == "POST":
        return redirect(url_for("views.room", pin=request.form["pin"]))

    return render_template("join.html")


@views.route("/room/<int:pin>")
@pin_required
def room(pin):
    return render_template("room.html", user_can_skip=g.room.skip)


@views.get("/current-track")
@pin_required
def current_track():
    current_track = api.get_current_track()

    if type(current_track) is int:
        return "No Content - Spotify is closed", 204

    track_in_queue = (
        g.room.queue.filter_by(id=current_track["id"])
        .order_by(Tracks.position.desc())
        .first()
    )

    if track_in_queue:
        g.room.position_in_queue = track_in_queue.position
        db.session.commit()

        # Because calculating the dominant color is very slowly, the color is saved in the Database.
        current_track.update({"color": track_in_queue.color})

    recommendations = api.get_recommendations()
    current_track.update({"similar_tracks": recommendations})

    # queue = [
    #    {"name": track.name, "artist": track.artist, "image_url": track.image_url}
    #    for track in g.room.queue.order_by(Tracks.position)[
    #        g.room.position_in_queue + 1 :
    #    ]
    # ]

    queue = api.get_queue()

    current_track.update({"queue": queue})

    return current_track


@views.get("/search")
@pin_required
def search():
    q = request.args.get("q")
    if not q:
        abort(400)

    return api.search(q)


@views.route("/queue", methods=("GET", "POST", "PUT"))
@pin_required
def queue():
    if request.method == "POST" or request.method == "PUT":
        track_uri = request.args.get("uri")
        track_id = api.uri_to_id(track_uri)

        if not type(track_uri) is str:
            abort(400)

        already_in_queue = g.room.queue.filter_by(id=track_id).first()
        if already_in_queue:
            already_in_queue = (
                g.room.queue.filter_by(id=track_id)
                .order_by(Tracks.position.desc())
                .first()
            )
            if already_in_queue.position > g.room.position_in_queue:
                return "Already in queue", 304

        api.add_to_queue(track_uri)

        track = Tracks(room_pin=g.room.pin, **api.get_track_info(track_id))
        db.session.add(track)
        db.session.commit()

        return "Added to Playback queue.", 204

    elif request.method == "GET":
        response = {"tracks": []}
        for track in g.room.queue.order_by(Tracks.order):
            response["tracks"].append({"name": track.name, "artist": track.name})

        return response


@views.post("/skip")
@pin_required
def skip():
    if g.room.skip:
        return api.skip_track()
    else:
        abort(403)


@views.errorhandler(HTTPException)
def error_page(error):
    return render_template(
        "error.html",
        status_code=error.get_response().status_code,
        description=error.description,
    )
