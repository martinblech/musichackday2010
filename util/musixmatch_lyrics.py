import sys
from appscript import *
import urllib2
import pymusixmatch as mm

MUSIXMATCH_KEY = 'fe546221a278269d69df60d34bb5df03'
#mm.enable_caching('/tmp/musixmatch')

itunes = app('iTunes')

(library,) = itunes.library_playlists.get()

tracks = library.file_tracks.get()
#tracks = itunes.search(library, for_='jeff buckley')

def clean(v):
    if v == k.missing_value:
        return None
    v = v.replace('\r', '\n')
    return v

def download_lyrics(artist, trackname):
    search = mm.search_for_lyrics(artist, trackname, MUSIXMATCH_KEY)
    lyrics = search.get_next_page()
    try:
        return lyrics[0].get()
    except:
        return None

for track in tracks:
    artist = clean(track.artist.get())
    trackname = clean(track.name.get())
    if clean(track.lyrics.get()):
        continue
    print 'searching lyrics for', artist, '-', trackname
    lyrics = download_lyrics(artist, trackname)
    if lyrics:
        track.lyrics.set(lyrics)

track_count = 0
lyrics_count = 0
for track in tracks:
    track_count += 1
    print track.artist.get(), track.name.get()
    lyrics = clean(track.lyrics.get())
    if lyrics is not None:
        if not isinstance(lyrics, basestring):
            print >> sys.stderr, 'WARNING: strange value', type(lyrics), lyrics
    if lyrics:
        lyrics_count += 1
        print 'lyrics:', type(lyrics), lyrics

print 'done.', lyrics_count, ' out of ', track_count, 'tracks have lyrics'
