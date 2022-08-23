import json, functools, time

import requests
from flask import Blueprint
from flask import request, session, redirect, render_template, url_for, g, abort
from werkzeug.exceptions import HTTPException

from .models import db, Rooms
from . import auth
from . import spotify_api as api


views = Blueprint("views", __name__)


def pin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pin = request.args.get("pin", kwargs.get("pin"))
        if pin is None:
            abort(400) # No pin in request

        room = db.session.query(Rooms).filter_by(pin=pin).first()
        if room is None:
            abort(404) # Room not found

        if room.expires_at < time.time():
            Rooms.query.filter_by(pin=pin).delete()
            db.session.commit()
            abort(410) # Room is expired

        g.pin = pin
        g.room = room

        return func(*args, **kwargs)
    return wrapper


@views.get("/")
def index():
    return render_template("index.html")


@views.route("/create", methods=("GET", "POST"))
def create_room():
    if request.method == "POST":
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
        print(request.args.get("error"))
        abort(403) # Inappropriate answer from accounts.spotify.com

    spotify_auth_data = auth.request_access_token(code)
    if not spotify_auth_data:
        abort(403) # Inappropriate answer from accounts.spotify.com

    try:
        pin_length = int(session.pop("pin_length"))
        room_lifespan = int(session.pop("room_lifespan"))
        users_can_skip = bool(session.pop("users_can_skip"))
    except:
        abort(400) # Needed inforations are not in session

    room = Rooms(
        **spotify_auth_data, 
        pin_length=pin_length,
        lifespan=room_lifespan,
        skip=users_can_skip
    )
    db.session.add(room)
    db.session.commit()

    session["host_of"] = room.pin

    return redirect(url_for("views.host"))


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

        return render_template("host.html", pin=pin)


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


@views.route("/room/<int:pin>", methods=("GET", "POST"))
@pin_required
def room(pin):
    print(pin)
    if request.method == "POST":
        track_uri = request.args.get("track_uri")
        if type(track_uri) is str:
            api.add_to_queue(track_uri)
        else:
            abort(400)
    return render_template("room.html", user_can_skip=g.room.skip)


@views.get("/current-track")
@pin_required
def current_track(): 
    response = api.get_current_track()
    return response


@views.get("/search")
@pin_required
def search():
    q = request.args.get("q")
    if not q:
        abort(400)

    return api.search(q)


@views.post("/queue")
@pin_required
def add_to_queue():
    track_uri = request.args.get("uri")
    if not track_uri:
        abort(400)

    return api.add_to_queue(track_uri)


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
