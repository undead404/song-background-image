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
TRACK_TOP_TAGS = "http://ws.audioscrobbler.com/2.0/?method=track.getTopTags&api_key={api_key}&artist={artist}&track={track}&format=json"  # noqa

API_KEY = config("API_KEY")
LASTFM_USERNAME = config("LASTFM_USERNAME")


TAG_PATTERN = re.compile('[^a-zA-Z0-9]+')


def normalize_tag(tag):
    return TAG_PATTERN.sub(' ', tag.lower()).strip()


TAGS = None

with open('tags.json') as tags_file:
    TAGS = json.load(tags_file)


def extract_track_tags(track):
    print(
        "extract_track_tags('{artist}', '{track}', ..)".format(
            artist=track["artist"]["name"],
            track=track["name"],
        ),
    )
    track_data = request_data(
        TRACK_TOP_TAGS.format(
            api_key=API_KEY,
            artist=urllib.parse.quote(track["artist"]["name"]),
            track=urllib.parse.quote(track["name"]),
        ), "toptags"
    )
    if track_data is None:
        return (track["artist"]["name"], track["name"], {})
    return (track["artist"]["name"], track["name"], {TAGS[normalize_tag(tag["name"])]: tag["count"] for tag in track_data
                                                     ["tag"] if normalize_tag(tag["name"]) in TAGS})


def get_page_songs_tags(page_num):
    print("get_page_songs_tags({page_num})".format(page_num=page_num))
    loved_tracks_data = request_data(
        USER_GET_LOVED_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=page_num,
        ), "lovedtracks"
    )
    if loved_tracks_data is None:
        return []
    return map(extract_track_tags, loved_tracks_data["track"])


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

    with Pool() as pool:
        songs_tags_pages = pool.map(
            get_page_songs_tags,
            range(1, pages_num + 1),
        )
    print("Combining results...")
    songs_tags = {}

    def process_page(page_entries):
        global songs_tags
        for artist, song, tags in page_entries:
            if artist not in songs_tags:
                songs_tags[artist] = {}
            songs_tags[artist][song] = tags

    with Pool() as pool:
        pool.map(process_page, songs_tags_pages)
    with open('songs.json', 'w') as outfile:
        json.dump(
            {"data": songs_tags, "updated_at": str(datetime.now())}, outfile)
    print("Done")
