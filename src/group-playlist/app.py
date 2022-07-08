import os, json
import requests

import auth, db
from secret import secret_key



from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["DATABASE"] = os.path.join(app.instance_path, "instance/gp.sqlite")

db.init_app(app)


@app.route("/")
def index():
    request_url = auth.request_user_authorization("user-modify-playback-state")
    return render_template("index.html", user_auth_request=request_url)

@app.route("/redirect")
def redirect_page():
    args = request.args
    auth.request_access_token(args.get("code"))

    return redirect(url_for("host"))

@app.route("/host", methods=("GET", "POST"))
def host():
    if request.method == "POST":
        pass
        #Update settings

    return render_template("host.html")

@app.route("/join", methods=("GET", "POST"))
def join():
    args = request.args
    pin = args.get("pin")
    print(pin)

    if request.method == "POST":
        if pin is not None:
            return redirect(url_for('room', pin=pin))

    return render_template("join.html")

@app.route("/room/<int:pin>", methods=("GET", "POST"))
def room(pin):
    args = request.args
    pin = args.get("pin")

    if request.method == "POST":
        pass
        #Add song to queue

    return render_template("room.html")


def create_room():
    pass


if __name__ == "__main__":
    app.run(debug=True)
