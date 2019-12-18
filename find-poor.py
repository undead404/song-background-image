
import glob
from multiprocessing.dummy import Pool
import sys

from decouple import config

from audio import Audio
API_KEY = config("API_KEY")
API_SECRET = config("API_SECRET")
BITRATE_THRESHOLD = 224
dirs_with_poor_audio = set()


def get_audio_files(directory):
    glob_pattern = "{directory}/**/*.m4a".format(directory=directory)
    for file_path in glob.iglob(glob_pattern, recursive=True):
        yield file_path
    glob_pattern = "{directory}/**/*.mp3".format(directory=directory)
    for file_path in glob.iglob(glob_pattern, recursive=True):
        yield file_path


def process_audio(audio_file_path):
    try:
        track = Audio(audio_file_path)
        if track.get_bitrate() < BITRATE_THRESHOLD:
            directory_name = '/'.join(audio_file_path.split('/')[4:-1])
            if directory_name not in dirs_with_poor_audio:
                print(directory_name)
                dirs_with_poor_audio.add(directory_name)

    except Exception as error:
        print(error)


if __name__ == "__main__":
    directory = sys.argv[1]
    print('Start looking for poor audio')
    with Pool() as pool:
        pool.map(process_audio, get_audio_files(directory))
    print('ended looking for poor audio')
    with open('dirs_with_poor_audio.txt', 'w') as outfile:
        outfile.writelines(line + '\n' for line in sorted(dirs_with_poor_audio))
