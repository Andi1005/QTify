import requests, base64, json, time

from flask import url_for
from urllib.parse import urlencode

from secret import client_id, client_secret

spotify_url = "https://accounts.spotify.com"
redirect_url = "http://localhost:5000" + url_for("redirect_page")

def generate_client_auth():
    message = f"{client_id}:{client_secret}"
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")

    return base64_message

def request_user_authorization(scope):
    endpoint = "/authorize?"
    query = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_url,
        "state": "true"
    }

    print(query)

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
        "redirect_uri": redirect_url
    }

    response = requests.post(spotify_url + endpoint, headers=headers, data=data) # -> access_token, token_type, espires_in, refresh_token, scope
    response_dict = response.json()

    access_token = response_dict["access_token"]
    expires_at = time.time() + response_dict["expires_in"]
    refresh_token = response_dict["refresh_token"]

    return [access_token, expires_at, refresh_token]

def refresh_access_token(refresh_token):
    endpoint = "/api/token"
    headers = {
        "Authorization": "Basic " + generate_client_auth(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "code": refresh_token,
    }

    r = requests.post(spotify_url + endpoint, headers=headers, data=data)
    print(json.dumps(r.json(), indent=2))