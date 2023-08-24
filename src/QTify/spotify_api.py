from urllib.parse import urlencode
import asyncio

import requests
from flask import g
import scipy
import numpy as np

from PIL import Image
from io import BytesIO


from . import auth
from .models import db, Tracks


SPOTIFY_URL = "https://api.spotify.com/v1"
MARKET = "DE"


def make_header() -> dict:  # All api calls need the same headers
    return {"Authorization": f"Bearer {g.room.access_token}"}


def uri_to_id(uri: str) -> str:
    """Extract a spotify id from a uri.
    Such a uri is looks like 'spotify:track:<id>'. For an id we only need the 3rd part.
    """

    return uri.split(":")[2]


def request_image(src: str) -> Image:
    img_response = requests.get(src)
    img = Image.open(BytesIO(img_response.content))

    return img


@auth.check_token
def add_to_queue(track_uri):
    endpoint = SPOTIFY_URL + "/me/player/queue?"
    query = {
        "uri": track_uri,
    }
    query_string = urlencode(query)
    response = requests.post(endpoint + query_string, headers=make_header())

    if response.status_code == 204:
        return "Added to Playback queue.", 204

    else:
        return response.json()


@auth.check_token
def search(q):
    endpoint = SPOTIFY_URL + "/search?"
    query = {
        "q": q,
        "type": "track",
        "limit": 10,
        "market": MARKET,
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()
        tracks = []
        for track in response_dict["tracks"]["items"]:
            track_info = {
                "name": track["name"],
                "artists": ", ".join([artist["name"] for artist in track["artists"]]),
                "image": track["album"]["images"][0]["url"],
                "uri": track["uri"],
            }
            tracks.append(track_info)

        return {"tracks": tracks}


@auth.check_token
def get_current_track():
    endpoint = SPOTIFY_URL + "/me/player/currently-playing"
    response = requests.get(endpoint, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()

        artists = response_dict["item"]["artists"]
        artists_names = [artist["name"] for artist in artists]
        artists_names = ", ".join(artists_names)

        track_info = {
            "is_playing": response_dict["is_playing"],
            "progress_ms": response_dict["progress_ms"],
            "duration_ms": response_dict["item"]["duration_ms"],
            "id": response_dict["item"]["id"],
            "name": response_dict["item"]["name"],
            "image": response_dict["item"]["album"]["images"][0]["url"],
            "artists": artists_names,
        }

        return track_info

    else:
        return 204


@auth.check_token
def get_queue():
    QUEUE_LENGTH = 10

    endpoint = SPOTIFY_URL + "/me/player/queue"
    response = requests.get(endpoint, headers=make_header())

    if not response.status_code == 200:
        raise Exception

    response_dict = response.json()

    # May be used later instead of requesting the current track separate.
    currently_playing = response_dict["currently_playing"]

    queue = [
        {
            "name": track["name"],
            "artist": ", ".join([artist["name"] for artist in track["artists"]]),
            "image_url": track["album"]["images"][0]["url"],
            "track_uri": track["uri"],
        }
        for track in response_dict["queue"][:QUEUE_LENGTH]
    ]

    return queue


def get_track_info(id):
    endpoint = SPOTIFY_URL + f"/tracks/{id}?"
    query = {
        "market": MARKET,
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()

        image_url = response_dict["album"]["images"][0]["url"]

        track_info = {
            "id": id,
            "name": response_dict["name"],
            "artist": response_dict["artists"][0]["name"],
            "artist_id": response_dict["artists"][0]["id"],
            "image_url": image_url,
        }

        return track_info

    else:
        raise Exception


@auth.check_token
def get_recommendations():
    endpoint = SPOTIFY_URL + "/recommendations?"
    seed_tracks = (
        Tracks.query.filter_by(room=g.room).order_by(Tracks.position.desc()).all()
    )

    if len(seed_tracks) < 5:
        return

    seed_tracks = [track.id for track in seed_tracks[-5:]]

    query = {
        "seed_tracks": ",".join(seed_tracks),
        "min_popularity": 70,
        "min_danceability": 0.3,
        "min_energiy": 0.4,
        "limit": 20,
        "market": MARKET,
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()
        recommendations = []
        for track in response_dict["tracks"]:
            name = track["name"]
            idx = name.rfind("(")
            recommendation = name
            if not idx == -1:
                if "feat." in name[idx:] or "with" in name[idx:]:
                    recommendation = name[:idx]

            while recommendation[-1] == " ":
                recommendation = recommendation[: len(recommendation) - 1]
            recommendations.append(recommendation)

        return recommendations


@auth.check_token
def skip_track():
    endpoint = SPOTIFY_URL + "/me/player/next"
    response = requests.post(endpoint, headers=make_header())
    if response.status_code == 204:
        return "Okay", 204
    else:
        return response.json()
