#!/usr/bin/python3

import os
import sys
import glob
import json
import pprint
from decouple import config
import mutagen.mp3
import mutagen.easyid3
import requests

API_KEY = config("API_KEY")
API_SECRET = config("API_SECRET")
LASTFM_USERNAME = config("LASTFM_USERNAME")

#
# MP3 playlist generator
#
# Generate an mp3 playlist file (.m3u), sorted by album track number.
#
# DEPENDENCIES
#
#   - Mutagen (http://code.google.com/p/mutagen/)
#
# NOTE: To install `mutagen`, run:
#
#   $ cd /path/to/mutagen/download/directory && python setup.py install
#
# USAGE
#
# You can pass directoryectories two ways this script - as arguments or
# via standard input.
#
#   $ m3u.py /AphexTwin/Drukqs
#
# or multiple directoryectories:
#
#   $ find /directory/Music -type d -links 2 | m3u.py -
#
# Author: Jon LaBelle <jon@tech0.com>
# Date: Sun Jul 28 2013 06:27:42 GMT-0500 (CDT)
#


def create_m3u(directory=".", recursive=False, playlist=''):

    try:
        print("Processing directory '{directory}'...".format(
            directory=directory))

        mp3s = []
        # os.chdir(directory)

        for file in get_mp3_files(directory):
            try:
                file_mp3_meta = get_mp3_meta(file)
                # print(file_mp3_meta["artist"][0], file_mp3_meta["title"][0])
                if not is_loved(file_mp3_meta):
                    continue
                pprint.pprint(file_mp3_meta)
                mp3s.append(get_mp3_meta(file))
            except mutagen.mp3.HeaderNotFoundError:
                print("mutagen.mp3.MP3 Header Error on file: ", file)
            except KeyError:
                print("KeyError on file: ", file)

        if mp3s:
            mp3s.sort(key=get_sort_key)
            for mp3 in mp3s[-10:]:
                print(mp3)
            write_playlist(mp3s, os.path.join(directory, playlist))
        else:
            print("No mp3 files found in '{}'.".format(directory))

    finally:
        pass


def get_sort_key(mp3):
    i2 = mp3["filename"].rindex(os.path.sep)
    i1 = mp3["filename"].rindex(os.path.sep, 0, i2)
    # key = mp3["filename"][i1:i2], mp3["filename"][i2:]
    key = mp3["filename"][i1:]
    # print(key)
    return key


def get_mp3_files(directory):
    glob_pattern = "{directory}/**/*.mp3".format(directory=directory)
    return glob.iglob(glob_pattern, recursive=True)


def get_mp3_meta(filepath):
    id3_data = mutagen.easyid3.EasyID3(filepath)
    return {
        'artist': id3_data['artist'],
        'filename': filepath,
        'length': int(mutagen.mp3.MP3(filepath).info.length),
        'title': id3_data['title'],
        'tracknumber': id3_data[
            'tracknumber'][0].split('/')[0]
    }


loved_tracks = []


def is_loved(file_mp3_meta):
    global loved_tracks
    if len(loved_tracks) == 0:
        pages_num = None
        current_page = 1
        while pages_num is None or current_page <= pages_num:
            response = requests.get(
                '''http://ws.audioscrobbler.com/2.0/'''
                '''?method=user.getlovedtracks&user={lastfm_username}&'''
                '''api_key={api_key}&format=json&page={page}'''.format(
                    api_key=API_KEY, lastfm_username=LASTFM_USERNAME,
                    page=current_page))
            data = json.loads(response.text)
            loved_tracks.extend(data["lovedtracks"]["track"])
            if pages_num is None:
                pages_num = int(data["lovedtracks"]["@attr"]["totalPages"])
            print(current_page, 'of', pages_num)
            current_page += 1
    try:
        next(
            loved_track for loved_track in loved_tracks
            if loved_track['name'] == file_mp3_meta["title"][0] and
            loved_track['artist']['name'] == file_mp3_meta["artist"][0])
        return True
    except:
        return False


def write_playlist(mp3s, playlist="loved.m3u"):
    print("Writing playlist '{}'...".format(playlist))
    # write the playlist
    outfile = open(playlist, 'w')
    outfile.write("#EXTM3U\n")

    for mp3 in mp3s:
        outfile.write("#EXTINF:{mp3_length},{mp3_filename}\n".format(
            mp3_length=mp3['length'], mp3_filename=mp3['filename']))
        outfile.write(mp3['filename'] + "\n")

    outfile.close()


if __name__ == "__main__":

    # directories containing music files
    directorys = []

    if len(sys.argv) == 2 and sys.argv[1] == '-':
        # we do not have command line arguments, so read from STDIN
        for line in sys.stdin:
            directorys.append(line.strip())
    else:
        # passed in directoryectories on the command line
        for directory in sys.argv[1:]:
            directorys.append(directory)

    # for each directoryectory passed to us, go
    # to it and make the M3U out of the
    # mutagen.mp3.MP3 files there
    for directory in directorys:
        create_m3u(directory, recursive=True, playlist=os.path.join(
            directory, 'loved.m3u'))
