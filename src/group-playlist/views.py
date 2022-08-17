import json, functools, time

import requests
from flask import Blueprint
from flask import request, session, redirect, render_template, url_for, flash, g

from models import db, Rooms
import auth
import spotify_api as api


views = Blueprint("views", __name__)


def pin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pin = request.args.get("pin")
        if pin is None:

            if "host_of" in session:
                pin = session["host_of"]
                if pin is None:   
                    return "Bad Request - Invalid or no pin", 400

        room = db.session.query(Rooms).filter_by(pin=pin).first()
        if room is None:
            return "Bad Request - Room doesn't exists", 400

        if room.expires_at < time.time():
            return "Unauthorized - Room is expired", 401

        g.pin = pin
        g.room = room

        return func(*args, **kwargs)
    return wrapper


@views.route("/")
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


@views.route("/redirect") 
def redirect_page():
    code = request.args.get("code")
    if code is None:
        print(request.args.get("error"))
        return "Forbidden - Inappropriate answer from accounts.spotify.com", 403

    spotify_auth_data = auth.request_access_token(code)
    if not spotify_auth_data:
        return "Forbidden - Inappropriate answer from accounts.spotify.com", 403

    try:
        pin_length = int(session.pop("pin_length"))
        room_lifespan = int(session.pop("room_lifespan"))
        users_can_skip = bool(session.pop("users_can_skip"))
    except:
        return "Bad Request - Invalid room settings", 400

    room = Rooms(
        **spotify_auth_data, 
        pin_length=pin_length,
        lifespan=room_lifespan
    )
    db.session.add(room)
    db.session.commit()

    session["host_of"] = room.pin

    return redirect(url_for("views.host"))


@views.route("/host", methods=("GET", "POST"))
def host():
    if request.method == "GET":
        if not "host_of" in session:
            # No session found
            return redirect(url_for("views.create_room"))
            
        pin = session["host_of"]
        found_room = Rooms.query.filter_by(pin=pin)
        if not found_room:
            return "Gone - Room isn't in the database", 410
        elif False:
            pass # Handle an expired room

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
    if request.method == "POST":
        track_uri = request.args.get("track_uri") # TODO: validate track_uri
        api.add_to_queue(g.room, track_uri)

    return render_template("room.html")


@views.route("/current-track")
@pin_required
def current_track(): 
    response = api.get_current_track(g.room)
    return response


@views.route("/search")
@pin_required
def search():
    q = request.args.get("q")
    if not q:
        return "Missing search string", 400

    return api.search(g.room, q)


@views.route("/queue", methods=("POST",))
@pin_required
def add_to_queue():
    track_uri = request.args.get("uri")
    if not track_uri:
        return "Missing track uri", 400

    return api.add_to_queue(g.room, track_uri)