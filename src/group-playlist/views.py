import json, functools

import requests
from flask import Blueprint
from flask import request, session, redirect, render_template, url_for, flash

from models import db, Rooms
import auth
import spotify_api as api


views = Blueprint("views", __name__)


def pin_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pin = request.args.get("pin")
        print(pin)
        if pin is None:
            return "Bad Request", 400

        room = db.session.query(Rooms).filter_by(pin=pin).first()
        if room is None:
            return "Bad Request", 400

        return func(*args, **kwargs)
    return wrapper


@views.route("/")
def index():
    return render_template("index.html")


@views.route("/redirect")
def redirect_page():
    code = request.args.get("code")
    if code is None:
        print(request.args.get("error"))
        return redirect(url_for("views.index"))

    spotify_auth_data = auth.request_access_token(code)
    if not spotify_auth_data:
        print("Couldn't recive access token.")
        return redirect(url_for("views.index"))

    # Create a new room
    room = Rooms(**spotify_auth_data)
    db.session.add(room)
    db.session.commit()

    session["host_of"] = room.pin

    return redirect(url_for("views.host"))        


@views.route("/host", methods=("GET", "POST"))
def host():
    if request.method == "GET":
        if not "host_of" in session:
            # No session found
            request_url = auth.request_user_authorization()
            return redirect(request_url)
            
        room_pin = session["host_of"]
        found_room = Rooms.query.filter_by(pin=room_pin)
        if not found_room:
            # Room doesn't exsist
            return redirect(url_for("views.index"))

        return render_template("host.html", pin=room_pin)


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
        pin = request.form["pin"]

        if pin is not None:
            if db.session.query(Rooms.pin).filter_by(pin=pin).first() is not None:
                return redirect(url_for('views.room', pin=pin))
            
            else:
                print("Room doesn't exsists")
    
        else:
            pass # Invalid pin
        
    return render_template("join.html")


@views.route("/room/<int:pin>", methods=("GET", "POST"))
def room(pin):
    pin = request.args.get("pin")

    room = Rooms.query.filter_by(pin=pin)
    if not room:
        return redirect(url_for("views.join")) # Room doesn't exsist

    if request.method == "POST":
        track_uri = request.args.get("track_uri")
        api.add_to_queue(track_uri)

    return render_template("room.html")


@views.route("/current-track")
def current_track():
    pin = request.args.get("pin")
    if pin is None:
        return "Bad Request", 400

    room = db.session.query(Rooms).filter_by(pin=pin).first()
    if room is None:
        return "Bad Request", 400

    response = api.get_current_track(room)
    return response


@views.route("/search")
def search():
    pin = request.args.get("pin")
    if pin is None:
        return "Missing pin", 400

    room = db.session.query(Rooms).filter_by(pin=pin).first()
    if room is None:
        return "Room doesn't exist", 400

    q = request.args.get("q")
    if not q:
        return "Missing search string", 400

    return api.search(room, q)
