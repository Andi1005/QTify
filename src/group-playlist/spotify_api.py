import json
import time

from urllib.parse import urlencode

import requests

import auth


@auth.check_token
def add_to_queue():
    pass


@auth.check_token
def search(room, q):
    endpoint = "https://api.spotify.com/v1/search?"
    headers = {
        "Authorization": f"Bearer {room.access_token}"
    }
    query = {
        "q": q,
        "type": "track",
        "limit": 10,
        "market": "DE",
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=headers)
    
    if response.status_code == 200:
        response_dict = response.json()
        tracks = []
        for track in response_dict["tracks"]["items"]:
            track_info = {
                "name": track["name"],
                "artists": ", ".join([artist["name"] for artist in track["artists"]]),
                "image": track["album"]["images"][0]["url"],
                "uri": track["uri"]
            }
            tracks.append(track_info)
        return {"tracks": tracks}

    else:
        return "IDK what happened", 500


@auth.check_token
def get_current_track(room):
    endpoint = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {
        "Authorization": f"Bearer {room.access_token}"
    }

    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        response_dict = response.json()

        artists = response_dict["item"]["artists"]
        artists = [artist["name"] for artist in artists]
        artists = ", ".join(artists)

        track_info = {
            "is_playing": response_dict["is_playing"],
            "progress_ms": response_dict["progress_ms"],
            "duration_ms": response_dict["item"]["duration_ms"],

            "name": response_dict["item"]["name"],
            "image": response_dict["item"]["album"]["images"][0]["url"],
            "artists": artists,
            "debug": response_dict
        }

        return track_info
    
    else:
        return "Spotify is closed", 204
