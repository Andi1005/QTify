import requests, base64, json

from flask import url_for
from urllib.parse import urlencode

from secret import client_id, client_secret

url = "https://accounts.spotify.com"
server_url = "http://localhost:5000"

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
        "redirect_uri": server_url + url_for("redirect_page"),
        "state": "true"
    }

    print(query)

    query_string = urlencode(query)
    redirect_url = url + endpoint + query_string

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
        "redirect_uri": server_url + url_for("redirect_page"),
    }

    r = requests.post(url + endpoint, headers=headers, data=data)
    print(json.dumps(r.json(), indent=2))

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

    r = requests.post(url + endpoint, headers=headers, data=data)
    print(json.dumps(r.json(), indent=2))