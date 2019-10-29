#!/env/bin python3
from datetime import datetime
from decouple import config
import glob
import json
from functools import lru_cache
from multiprocessing.dummy import Pool
import os.path
# from pprint import pprint
import re
import requests
import sys
import urllib
from logzero import logger, logfile

from audio import Audio
API_KEY = config("API_KEY")
API_SECRET = config("API_SECRET")
LASTFM_USERNAME = config("LASTFM_USERNAME")
BLACKLISTED_DOMAINS = []

TAG_PATTERN = re.compile('[^a-zA-Z0-9]+')

logfile('./logs/fix-tags-{:%Y-%m-%d}.log'.format(datetime.now()))


@lru_cache(maxsize=None)
def normalize_tag(tag):
    return TAG_PATTERN.sub(' ', tag.lower()).strip()


WHITELISTED_TAGS = {}
with open('tags.json') as tags_file:
    # WHITELISTED_TAGS = {
    #     normalize_tag(tag): tag.strip().title()
    #     for tag in tags_file.readlines()
    # }
    WHITELISTED_TAGS = json.load(tags_file)


@lru_cache(maxsize=None)
def encodeURIComponent(input_str, quotate=urllib.parse.quote):
    """
    Python equivalent of javascript's encodeURIComponent
    """
    return quotate(input_str.encode('utf-8'), safe='~()*!.\'')


@lru_cache(maxsize=None)
def fetch_album_tags(artist, album):
    # print("fetch_album_tags({artist}, {album})".format(
    #     artist=artist, album=album))
    try:
        return get((
            "http://ws.audioscrobbler.com/2.0/?method=album.gettoptags&"
            "api_key={api_key}&artist={artist}&album={album}&format=json"
        ).format(
            api_key=API_KEY,
            artist=encodeURIComponent(artist),
            album=encodeURIComponent(album),
        )).json()['toptags']['tag']
    except KeyError:
        return []


@lru_cache(maxsize=None)
def fetch_artist_tags(artist):
    # print("fetch_artist_tags({artist})".format(
    #     artist=artist))
    try:
        return get((
            "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&"
            "api_key={api_key}&artist={artist}&format=json"
        ).format(
            api_key=API_KEY,
            artist=encodeURIComponent(artist),
        )).json()['toptags']['tag']
    except KeyError:
        return []


def fetch_track_tags(artist, track):
    # print("fetch_track_tags({artist}, {track})".format(
    #     artist=artist, track=track))
    try:
        return get(
            ("http://ws.audioscrobbler.com/2.0/?method=track.gettoptags&"
             "api_key={api_key}&artist={artist}&track={track}&format=json"
             ).format(
                api_key=API_KEY,
                artist=encodeURIComponent(artist),
                track=encodeURIComponent(track),
            ),
        ).json()['toptags']['tag']
    except KeyError:
        return []


def get(url):
    # print('GET', url)
    return requests.get(url)


def get_audio_files(directory):
    glob_pattern = "{directory}/**/*.m4a".format(directory=directory.replace('[', '[[]'))
    for file_path in glob.iglob(glob_pattern, recursive=True):
        yield file_path
    glob_pattern = "{directory}/**/*.mp3".format(directory=directory.replace('[', '[[]'))
    for file_path in glob.iglob(glob_pattern, recursive=True):
        yield file_path


def get_main_tag(tags):
    for tag_info in tags:
        # if tag_info['count'] < 50:
        #     break
        normalized_tag = normalize_tag(tag_info['name'])
        if normalized_tag in WHITELISTED_TAGS:
            return WHITELISTED_TAGS[normalized_tag]


def guess_genre(track):
    if not track.get_artist():
        return ''
    if track.get_title():
        track_tags = fetch_track_tags(
            artist=track.get_artist(), track=track.get_title())
        # pprint(track_tags)
        track_tag = get_main_tag(track_tags)
        if track_tag:
            return track_tag
    if track.get_album():
        album_tags = fetch_album_tags(
            artist=track.get_artist(),
            album=track.get_album(),
        )
        # pprint(album_tags)
        album_tag = get_main_tag(album_tags)
        if album_tag:
            return album_tag
    artist_tags = fetch_artist_tags(artist=track.get_artist())
    # pprint(artist_tags)
    artist_tag = get_main_tag(artist_tags)
    if artist_tag:
        return artist_tag
    return ''


def process_audio(audio_file_path):
    try:
        track = Audio(audio_file_path)
        """printed_line = "[{genre}] {artist} - {album} - {title}".format(
            album=track.get_album(),
            artist=track.get_artist(),
            genre=track.get_genre(),
            title=track.get_title(),
        )
        if len(printed_line) > 160:
            printed_line = "{cut_line}...".format(cut_line=printed_line[:157])
        else:
            printed_line = printed_line.ljust(160)
        print(printed_line, end='\r')"""
        new_genre = guess_genre(track)
        if new_genre == track.get_genre():
            return
        logger.info(
            "{artist} - {album} - {title}: {old_genre} -> {genre}".format(
                album=track.get_album(),
                artist=track.get_artist(),
                genre=new_genre or '[Empty]',
                old_genre=track.get_genre() or '[Empty]',
                title=track.get_title(),
            ),
        )
        track.set_genre(new_genre)
    except Exception as error:
        logger.error(error)


if __name__ == "__main__":
    directory = sys.argv[1]
    logger.info('Start fixing tags')
    with Pool() as pool:
        pool.map(process_audio, get_audio_files(directory))
    logger.info('End fixing tags')
    # for audio_file_path in get_audio_files(directory):
    #     track = Audio(audio_file_path)
    #     new_genre = guess_genre(track)
    #     if new_genre == track.get_genre():
    #         continue
    #     print(
    #         "{artist} - {album} - {title}: {old_genre} -> {genre}".format(
    #             album=track.get_album(),
    #             artist=track.get_artist(),
    #             genre=new_genre or '[Empty]',
    #             old_genre=track.get_genre() or '[Empty]',
    #             title=track.get_title(),
    #         ),
    #     )
    #     track.set_genre(new_genre)
