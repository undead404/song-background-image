#!/usr/bin/python3

import os
import sys
import glob
import mutagen.mp3
import mutagen.mp4
import mutagen.easymp4
import mutagen.easyid3

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
                data = get_mp3_meta(file)
                mp3s.append(data)
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
    glob_pattern = "{directory}/**/*.m4a".format(directory=directory)
    for file_path in glob.iglob(glob_pattern, recursive=True):
       yield file_path
    glob_pattern = "{directory}/**/*.mp3".format(directory=directory)
    for file_path in glob.iglob(glob_pattern, recursive=True):
       yield file_path


def get_mp3_meta(filepath):
    if filepath.endswith('.m4a'):
        data = {
            'filename': filepath,
            'length': int(mutagen.mp4.MP4(filepath).info.length),
            'tracknumber': mutagen.easymp4.EasyMP4(filepath).tags.get
                                                ('tracknumber')[0].split('/')[0]
               }
        return data
    elif filepath.endswith('.mp3'):
        return {
            'filename': filepath,
            'length': int(mutagen.mp3.MP3(filepath).info.length),
            'tracknumber': mutagen.easyid3.EasyID3(filepath)[
                                                'tracknumber'][0].split('/')[0]
               }


def write_playlist(mp3s, playlist="playlist.m3u"):
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
                                          directory, 'playlist.m3u'))
