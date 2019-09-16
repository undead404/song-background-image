import os

import mutagen.easyid3
import mutagen.easymp4
AUDIO_META = {
    '.m4a': mutagen.easymp4.EasyMP4,
    '.mp3': mutagen.easyid3.EasyID3,
}


class Audio:
    __album = None
    __artist = None
    __filepath = None
    __genre = None
    __meta = None
    __title = None

    def __init__(self, filepath):
        self.__filepath = filepath

    def get_album(self):
        if self.__album is None:
            self.__album = self.get_meta_value('album')
        return self.__album

    def get_artist(self):
        if self.__artist is None:
            self.__artist = self.get_meta_value('artist')
        return self.__artist

    def get_genre(self):
        if self.__genre is None:
            self.__genre = self.get_meta_value('genre')
        return self.__genre

    def get_meta(self):
        if self.__meta is None:
            _, ext = os.path.splitext(self.__filepath)
            self.__meta = AUDIO_META[ext](self.__filepath)
        return self.__meta

    def get_meta_value(self, key):
        try:
            return self.get_meta()[key][0]
        except Exception:
            return ''

    def get_title(self):
        if self.__title is None:
            self.__title = self.get_meta_value('title')
        return self.__title

    def set_genre(self, new_genre):
        self.get_meta()['genre'] = new_genre
        self.get_meta().save(self.__filepath, v1=0, v2_version=3)
