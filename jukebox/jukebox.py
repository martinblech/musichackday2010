def _not_implemented(*args, **kwargs):
    raise Exception('not implemented')

class Jukebox:
    get_tracks = _not_implemented
    tracks = property(get_tracks)

    search = _not_implemented

class Track:
    get_artist = _not_implemented
    set_artist = _not_implemented
    artist = property(get_artist, set_artist)

    get_title = _not_implemented
    set_title = _not_implemented
    title = property(get_title, set_title)

    get_lyrics = _not_implemented
    set_lyrics = _not_implemented
    lyrics = property(get_lyrics, set_lyrics)
