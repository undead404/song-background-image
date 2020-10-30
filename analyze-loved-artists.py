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
TRACK_GET_INFO = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={track}&format=json"  # noqa
TRACK_TOP_TAGS = "http://ws.audioscrobbler.com/2.0/?method=track.getTopTags&api_key={api_key}&artist={artist}&track={track}&format=json"  # noqa
ALBUM_TOPTAGS = (
    "http://ws.audioscrobbler.com/2.0/?method=album.gettoptags&"
    "api_key={api_key}&artist={artist}&album={album}&format=json"
)
ARTIST_TOPTAGS = (
    "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&"
    "api_key={api_key}&artist={artist}&format=json"
)


API_KEY = config("API_KEY")
LASTFM_USERNAME = config("LASTFM_USERNAME")
# BIRTH_TIMESTAMP = 729777600
TRACKS_PER_PAGE = 50

# START_TIME = 1216846800
LAUNCH_TIME = int(datetime.now().timestamp())

total = None


def extend_taste(taste, taste_portion, multiply_by=1):
    # print("extend_taste(...)")
    new_taste = {tag: taste[tag] for tag in taste}
    for tag in taste_portion:
        new_taste[tag] = new_taste.get(tag, 0) + taste_portion[tag] * \
            multiply_by
    return new_taste


def get_page_taste_portion(page_num):
    global total
    print("get_page_taste_portion({page_num})".format(page_num=page_num))
    taste_portion = {}
    loved_tracks_data = request_data(
        USER_GET_LOVED_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=page_num,
        ), "lovedtracks"
    )
    if loved_tracks_data is None:
        return {}
    if total is None:
        total = int(loved_tracks_data["@attr"]["total"])
    for _, track in enumerate(loved_tracks_data["track"]):
        taste_portion = extend_taste(
            taste_portion,
            get_track_taste_portion(
                track["artist"]["name"],
                track["name"],
                int(track["date"]["uts"]),
            ),
            multiply_by=int(track["date"]["uts"]),
        )
    return taste_portion


def get_track_taste_portion(artist, track, track_uts):
    taste_portion = {}
    taste_portion[artist] = 1 / (LAUNCH_TIME - track_uts)
    return taste_portion


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
        if top_field not in data or data[top_field] is None:
            pprint(data)
            raise Exception("empty response")
        return data[top_field]
    except Exception:
        print('retry #{retries_num}... {url} [{top_field}]'.format(
            retries_num=retries_num + 1, top_field=top_field, url=url),
        )
        return request_data(url, top_field, retries_num=retries_num+1)


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


taste_portions = Pool().map(
    get_page_taste_portion,
    range(1, pages_num + 1),
)
print("Combining results...")
taste = functools.reduce(extend_taste, taste_portions, {})
# while pages_num is None or page_num <= pages_num:
#     extend_taste(taste, get_page_taste_portion(1))
# page_num += 1
# pprint(taste)
with open('loved.json', 'w') as outfile:
    json.dump(taste, outfile)

taste_pairs = sorted(
    taste.items(),
    key=lambda taste_pair: taste_pair[1],
    reverse=True,
)

top = taste_pairs[:200]
for tag_pair in top:
    print(tag_pair)
