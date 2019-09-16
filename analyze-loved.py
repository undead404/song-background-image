from datetime import datetime
import functools
import json
import multiprocessing
from pprint import pprint
import re
import urllib
import requests
from decouple import config

USER_GET_RECENT_TRACKS = "http://ws.audioscrobbler.com/2.0/?method=user.getlovedtracks&user={user}&api_key={api_key}&format=json&page={page_num}"  # noqa
TRACK_GET_INFO = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={artist}&track={track}&format=json"  # noqa

API_KEY = config("API_KEY")
LASTFM_USERNAME = config("LASTFM_USERNAME")
# BIRTH_TIMESTAMP = 729777600
TRACKS_PER_PAGE = 50

# START_TIME = 1216846800
LAUNCH_TIME = int(datetime.now().timestamp())

total = None
TAG_PATTERN = re.compile('[^a-zA-Z0-9]+')


def normalize_tag(tag):
    return TAG_PATTERN.sub(' ', tag.lower()).strip()


TAGS = None

with open('tags.json') as tags_file:
    TAGS = json.load(tags_file)


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
    response = request(
        USER_GET_RECENT_TRACKS.format(
            api_key=API_KEY,
            user=LASTFM_USERNAME,
            page_num=page_num,
        ),
    )
    recent_tracks_data = json.loads(response.text)
    if total is None:
        total = int(recent_tracks_data["lovedtracks"]["@attr"]["total"])
    for track_i, track in enumerate(recent_tracks_data["lovedtracks"]["track"]):  # noqa
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
    print(
        "get_track_taste_portion('{artist}', '{track}', ..)".format(
            artist=artist,
            track=track,
        ),
    )
    response = request(
        TRACK_GET_INFO.format(
            api_key=API_KEY,
            artist=urllib.parse.quote(artist),
            track=urllib.parse.quote(track),
        ),
    )
    track_data = json.loads(response.text)
    # try:
    #     duration = int(track_data["track"]["duration"][:-3])
    # except:
    #     duration = 250
    tags = (TAGS[normalize_tag(tag["name"])] for tag in track_data["track"]
            ["toptags"]["tag"] if normalize_tag(tag["name"]) in TAGS)
    return {tag: 1 / (LAUNCH_TIME - track_uts) for tag in tags}


def request(url, retries_num=0):
    try:
        return requests.get(url, timeout=2**retries_num)
    except Exception:
        print('retry #{retries_num}... {url}'.format(
            retries_num=retries_num + 1, url=url),
        )
        return request(url, retries_num=retries_num+1)


response = request(
    USER_GET_RECENT_TRACKS.format(
        api_key=API_KEY,
        user=LASTFM_USERNAME,
        page_num=1,
    ),
)
pages_num = int(
    json.loads(
        response.text
    )["lovedtracks"]["@attr"]["totalPages"],
)
page_num = 1
# pages_num = None
# pages_num = 2


taste_portions = multiprocessing.Pool().map(
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
pprint(taste_pairs[:100])
