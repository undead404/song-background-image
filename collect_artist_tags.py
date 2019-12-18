from datetime import datetime
import functools
import json
from multiprocessing.dummy import Pool
from pprint import pprint
import re
import urllib
import requests
import sys
from decouple import config

USER_GET_LOVED_TRACKS = "http://ws.audioscrobbler.com/2.0/?method=user.getlovedtracks&user={user}&api_key={api_key}&format=json&page={page_num}"  # noqa
ARTIST_GET_TOPTAGS = "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&api_key={api_key}&artist={artist}&format=json"  # noqa

API_KEY = config("API_KEY")
LASTFM_USERNAME = config("LASTFM_USERNAME")
# BIRTH_TIMESTAMP = 729777600
TRACKS_PER_PAGE = 50

# START_TIME = 1216846800
LAUNCH_TIME = int(datetime.now().timestamp())

TAG_PATTERN = re.compile('[^a-zA-Z0-9]+')


def normalize_tag(tag):
    return TAG_PATTERN.sub(' ', tag.lower()).strip()


TAGS = None

with open('tags.json') as tags_file:
    TAGS = json.load(tags_file)


def extract_artist(track):
    return track["artist"]["name"]


def fetch_artist_tags(artist_name):
    print(
        "fetch_artist_tags('{artist}, ..)".format(
            artist=artist_name,
        ),
    )
    track_data = request_data(
        ARTIST_GET_TOPTAGS.format(
            api_key=API_KEY,
            artist=urllib.parse.quote(artist_name),
        ), "toptags"
    )
    if track_data is None:
        return (artist_name, {})
    return (artist_name, {TAGS[normalize_tag(tag["name"])]: tag["count"] for tag in track_data
                          ["tag"] if normalize_tag(tag["name"]) in TAGS})


def get_page_artists(page_num):
    print("get_page_artists_tags({page_num})".format(page_num=page_num))
    loved_tracks_data = request_data(
        USER_GET_LOVED_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=page_num,
        ), "lovedtracks"
    )
    if loved_tracks_data is None:
        return []
    return map(extract_artist, loved_tracks_data["track"])


def request_data(url, top_field, retries_num=0):
    # print("request_data({url}, {top_field}, {retries_num})".format(
    #     url=url, top_field=top_field, retries_num=retries_num))
    try:
        response = requests.get(url, timeout=2**retries_num)
        if response.status_code >= 300:
            print("Status {code}".format(code=response.status_code))
            return
        data = response.json()
        if "error" in data:
            print("Error {error}: {message}".format(**data))
            return
        return data[top_field]
    except Exception:
        print('retry #{retries_num}... {url} [{top_field}]'.format(
            retries_num=retries_num + 1, top_field=top_field, url=url),
        )
        return request_data(url, top_field, retries_num=retries_num+1)


if __name__ == "__main__":
    data = request_data(
        USER_GET_LOVED_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=1,
        ), "lovedtracks"
    )
    if data is None:
        sys.exit(1)
    pages_num = int(
        data["@attr"]["totalPages"],
    )
    page_num = 1
    # pages_num = None
    # pages_num = 2
    artists = set()
    with Pool() as pool:
        artists_pages = pool.map(
            get_page_artists,
            range(1, pages_num + 1),
        )
    for artists_page in artists_pages:
        artists.update(artists_page)
    print("Combining results...")
    artists_tags = {}
    with Pool() as pool:
        for artist_name, artist_tags in pool.map(fetch_artist_tags, artists):
            if len(artist_tags) > 0:
                artists_tags[artist_name] = artist_tags

    with open('artists.json', 'w') as outfile:
        json.dump(
            {"data": artists_tags, "updated_at": str(datetime.now())}, outfile)
    print("Done")
