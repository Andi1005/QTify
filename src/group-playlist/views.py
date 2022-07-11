import requests
from flask import Blueprint
from flask import request, session, redirect, render_template, url_for, flash

import models
import auth
import spotify_api as api


views = Blueprint("views", __name__)


@views.route("/")
def index():
    request_url = auth.request_user_authorization("user-modify-playback-state")
    return render_template("index.html", user_auth_request=request_url)


@views.route("/redirect")
def redirect_page():
    code = request.args.get("code")

    spotify_auth_data = auth.request_access_token()

    if spotify_auth_data:
        # Create a new room
        room = models.Rooms(*spotify_auth_data)
        models.db.session.add(room)
        models.db.commit()

        session["host_of"] = room.pin

        return redirect(url_for("host"))

    else:
        return redirect(url_for("index"))


@views.route("/host", methods=("GET", "POST"))
def host():
    if not "host_of" in session:
        # No session found
        return redirect(url_for("index"))
        
    room_pin = session["host_of"]
    found_room = models.Rooms.query.filter_by(pin=room_pin)
    if not found_room:
        # Room doesn't exsist
        return redirect(url_for("index"))

    return render_template("host.html")


@views.route("/join", methods=("GET", "POST"))
def join():
    if request.method == "POST":
        pin = request.form["pin"]

        if pin is not None:
            if pin in models.Rooms:
                return redirect(url_for('room', pin=pin))
            
            else:
                pass # Room doesn't exsists
    
        else:
            pass # Invalid pin
        
    return render_template("join.html")


@views.route("/room/<int:pin>", methods=("GET", "POST"))
def room(pin):
    pin = request.args.get("pin")

    room = models.Rooms.query.filter_by(pin=pin)
    if not room:
        return redirect(url_for("join")) # Room doesn't exsist

    if request.method == "POST":
        track_uri = request.args.get("track_uri")
        api.add_to_queue(track_uri)

    return render_template("room.html")