import requests, base64, json, time, functools

from flask import url_for
from urllib.parse import urlencode

from secret import CLIENT_ID, CLIENT_SECRET
from models import db

spotify_url = "https://accounts.spotify.com"
server_url = "http://localhost:5000"
SCOPES = [
    "user-read-currently-playing",
    "user-modify-playback-state"
]

def generate_client_auth():
    message = f"{CLIENT_ID}:{CLIENT_SECRET}"
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")

    return base64_message

def request_user_authorization():
    endpoint = "/authorize?"
    query = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": ", ".join(SCOPES),
        "redirect_uri": server_url + url_for("views.redirect_page"),
        "state": "false"
    }

    query_string = urlencode(query)
    redirect_url = spotify_url + endpoint + query_string

    return redirect_url

def request_access_token(code):
    endpoint = "/api/token"
    headers = {
        "Authorization": "Basic " + generate_client_auth(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": server_url + url_for("views.redirect_page")
    }

    response = requests.post(spotify_url + endpoint, headers=headers, data=data) # -> access_token, token_type, espires_in, refresh_token, scope
    response_dict = response.json()

    response_data = {
        "access_token": response_dict["access_token"],
        "expires_at": time.time() + response_dict["expires_in"],
        "refresh_token": response_dict["refresh_token"]
    }
    
    return response_data

def refresh_access_token(refresh_token):
    endpoint = "/api/token"
    headers = {
        "Authorization": "Basic " + generate_client_auth(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post(spotify_url + endpoint, headers=headers, data=data)
    response_dict = response.json()

    response_data = {
        "access_token": response_dict["access_token"],
        "expires_at": time.time() + response_dict["expires_in"],
    }
    
    return response_data


def check_token(func):
    @functools.wraps(func)
    def wrapper(room, *args, **kwargs):
        if float(room.expires_at) < time.time():
            response = refresh_access_token(room.refresh_token)
            room.access_token = response["access_token"]
            room.expires_at = response["expires_at"]
            db.session.commit()

        return func(room, *args, **kwargs)
    return wrapper