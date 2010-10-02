import os
from appscript import *
from jukebox import Jukebox, Track

def _clean(v):
    if v == k.missing_value:
        return None
    v = v.replace('\r', '\n')
    return v

class ITunes(Jukebox):
    def __init__(self, data_path=None):
        self.itunes = app('iTunes')
        (self.library,) = self.itunes.library_playlists.get()
        if data_path is None:
            data_path = os.path.expanduser(
                '~/Library/Application Support/PyJukebox/iTunes/')
        Jukebox.__init__(self, data_path)

    def __wrap_track(self, track):
        return ITunesTrack(track)

    def __wrap_tracks(self, tracks):
        for track in tracks:
            yield self.__wrap_track(track)

    def get_track(self, id):
        track = self.library.file_tracks.ID(id)
        return self.__wrap_track(track)

    def get_tracks(self):
        tracks = self.library.file_tracks.get()
        return self.__wrap_tracks(tracks)

    tracks = property(get_tracks)

    def search(self, query):
        tracks = self.itunes.search(self.library, for_=query)
        return self.__wrap_tracks(tracks)

class ITunesTrack(Track):
    def __init__(self, itunes_track):
        self.itunes_track = itunes_track

    def get_id(self):
        return self.itunes_track.id.get()
    
    id = property(get_id)

    def get_artist(self):
        return _clean(self.itunes_track.artist.get())

    def set_artist(self, artist):
        self.itunes_track.artist.set(artist)

    artist = property(get_artist, set_artist)

    def get_title(self):
        return _clean(self.itunes_track.name.get())

    def set_title(self, title):
        self.itunes_track.name.set(title)

    title = property(get_title, set_title)

    def get_lyrics(self):
        return _clean(self.itunes_track.lyrics.get())

    def set_lyrics(self, lyrics):
        self.itunes_track.lyrics.set(lyrics)

    lyrics = property(get_lyrics, set_lyrics)
