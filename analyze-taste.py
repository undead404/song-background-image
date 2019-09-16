import json
import multiprocessing
from pprint import pprint
import urllib
import requests
from decouple import config

USER_GET_RECENT_TRACKS = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={api_key}&format=json&page={page_num}"  # noqa
TRACK_GET_INFO = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={track}&format=json"  # noqa

API_KEY = config("API_KEY")
LASTFM_USERNAME = config("LASTFM_USERNAME")


def extend_taste(taste, taste_portion):
    # print("extend_taste(...)")
    for tag in taste_portion:
        if tag in taste:
            taste[tag] += taste_portion[tag]
        else:
            taste[tag] = taste_portion[tag]


def get_page_taste_portion(page_num):
    print("get_page_taste_portion({page_num})".format(page_num=page_num))
    taste_portion = {}
    recent_tracks_data = acquire(
        USER_GET_RECENT_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=page_num,
        ),
        "recenttracks",
    )
    for track in recent_tracks_data["track"]:
        extend_taste(
            taste_portion,
            get_track_taste_portion(
                track["artist"]["#text"],
                track["name"],
            ),
        )
    return taste_portion


def get_track_taste_portion(artist, track):
    print(
        "get_track_taste_portion('{artist}', '{track}')".format(
            artist=artist,
            track=track,
        ),
    )
    track_data = acquire(
        TRACK_GET_INFO.format(
            api_key=API_KEY,
            artist=urllib.parse.quote(artist),
            track=urllib.parse.quote(track),
        ),
        "track",
    )
    try:
        duration = int(track_data["duration"][:-3])
    except:
        duration = 250
    tags = (tag["name"] for tag in track_data["toptags"]["tag"])
    return {tag: duration for tag in tags}


def acquire(url, field_name, retries_num=0):
    try:
        return json.loads(
            requests.get(url, timeout=2**retries_num).text
        )[field_name]
    except Exception:
        print('retry #{retries_num}... {url}'.format(
            retries_num=retries_num + 1, url=url),
        )
        return acquire(url, field_name, retries_num=retries_num+1)


taste = {}
data = acquire(
    USER_GET_RECENT_TRACKS.format(
        api_key=API_KEY,
        user=LASTFM_USERNAME,
        page_num=1,
    ),
    "recenttracks"
)
pages_num = int(
    data["@attr"]["totalPages"],
)
page_num = 1
# pages_num = None
# pages_num = 1


def process_page(page_num):
    extend_taste(
        taste, get_page_taste_portion(page_num),
    )


multiprocessing.Pool().map(
    process_page,
    range(1, pages_num + 1),
)
# while pages_num is None or page_num <= pages_num:
#     extend_taste(taste, get_page_taste_portion(1))
# page_num += 1
with open('listened.json', 'w') as outfile:
    json.dump(taste, outfile)

taste_pairs = sorted(
    taste.items(),
    key=lambda taste_pair: taste_pair[1],
    reverse=True,
)
pprint(taste_pairs[:10])
