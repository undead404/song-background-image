import os

import mutagen.easyid3
import mutagen.easymp4
import mutagen.mp3
AUDIO_META = {
    '.m4a': mutagen.easymp4.EasyMP4,
    '.mp3': mutagen.easyid3.EasyID3,
}


class Audio:
    __album = None
    __artist = None
    __bitrate = None
    __extension = None
    __filepath = None
    __info = None
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
    
    def get_extension(self):
        if self.__extension is None:
            _, self.__extension = os.path.splitext(self.__filepath)
        return self.__extension

    def get_bitrate(self):
        if self.__bitrate is None:
            if self.__info is None:
                self.__info = mutagen.mp3.MP3(self.__filepath)
            self.__bitrate = self.__info.info.bitrate // 1000
        return self.__bitrate
        

    def get_genre(self):
        if self.__genre is None:
            self.__genre = self.get_meta_value('genre')
        return self.__genre

    def get_info(self, key):
        if self.__info is None:
            self.__info = mutagen.mp3.MP3(self.__filepath)
        return self.__info.get(key)

    def get_meta(self):
        if self.__meta is None:
            self.__meta = AUDIO_META[self.get_extension()](self.__filepath)
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
        if 'mp3' in self.get_extension():
            self.get_meta().save(self.__filepath, v1=0, v2_version=3)
        else:
            self.get_meta().save()
