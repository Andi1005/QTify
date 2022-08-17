from urllib.parse import urlencode

import requests
from flask import g

import auth
from models import db, Tracks


SPOTIFY_URL = "https://api.spotify.com/v1"
MARKET = "DE"


def make_header(): # All api calls need the same headers
    return {
        "Authorization": f"Bearer {g.room.access_token}"
    }


@auth.check_token
def add_to_queue(track_uri):
    endpoint = SPOTIFY_URL + "/me/player/queue?"
    query = {
        "uri":track_uri,
    }
    query_string = urlencode(query)
    response = requests.post(endpoint + query_string, headers=make_header())

    track_id = track_uri.split(":")[2]
    song = Tracks(**get_track_info(track_id), room=g.room)
    db.session.add(song)
    db.session.commit()
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
                "uri": track["uri"]
            }
            tracks.append(track_info)
        return {"tracks": tracks}

    else:
        return "IDK what happened", 500


@auth.check_token
def get_current_track():
    endpoint = SPOTIFY_URL + "/me/player/currently-playing"
    response = requests.get(endpoint, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()

        artists = response_dict["item"]["artists"]
        artists_names = [artist["name"] for artist in artists]
        artists_names = ", ".join(artists_names)

        seed = {
            "seed_artists": [artist["id"] for artist in artists[:min(4, len(artists))]],
            "seed_tracks": [response_dict["item"]["id"]],
        }

        track_info = {
            "is_playing": response_dict["is_playing"],
            "progress_ms": response_dict["progress_ms"],
            "duration_ms": response_dict["item"]["duration_ms"],

            "name": response_dict["item"]["name"],
            "image": response_dict["item"]["album"]["images"][0]["url"],
            "artists": artists_names,

            "similar_tracks": get_recommendations(**seed)
        }

        return track_info
    
    else:
        return "No Content - Spotify is closed", 204


def get_track_info(id):
    endpoint = SPOTIFY_URL + f"/tracks/{id}?"
    query = {
        "market": MARKET,
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()

        track_info = {
            "id": id,
            "name": response_dict["name"],
            "artist": response_dict["artists"][0]["name"],
            "artist_id": response_dict["artists"][0]["id"],
        }

        return track_info

    else:
        raise Exception


@auth.check_token
def get_recommendations(seed_artists=[], seed_genres=[], seed_tracks=[]):
    if len(seed_artists + seed_genres + seed_tracks) > 5:
        return

    endpoint = SPOTIFY_URL + "/recommendations?"
    query = {
        "seed_artists": ",".join(seed_artists),
        #"seed_genres": ",".join(seed_genres),
        "seed_tracks": ",".join(seed_tracks),
        "limit": 20,
        "market": MARKET,
    }
    query_string = urlencode(query)
    response = requests.get(endpoint + query_string, headers=make_header())

    if response.status_code == 200:
        response_dict = response.json()
        return [track["name"] for track in response_dict["tracks"]]


@auth.check_token
def skip_track():
    endpoint = SPOTIFY_URL + "/me/player/next"
    response = requests.post(endpoint, headers=make_header())
    if response.status_code == 204:
        return "Okay", 204
    else:
        return response.json()