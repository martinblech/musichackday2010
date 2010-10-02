import os
import whoosh.index
import whoosh.fields
import whoosh.query
import whoosh.qparser

def _not_implemented(*args, **kwargs):
    raise Exception('not implemented')

class JukeboxException(Exception):pass

class Jukebox(object):
    def __init__(self, data_path, sync=False):
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        index_path = os.path.join(data_path, 'index')
        self.track_index = self._get_index(index_path, 'tracks')
        self.query_parser = whoosh.qparser.MultifieldParser(
                ['artist', 'title', 'lyrics'],
                fieldboosts=dict(artist=1, title=1, lyrics=1),
                group=whoosh.qparser.default.OrGroup)
        if sync:
            self.sync_track_index()

    def _get_index(self, index_path, index_name):
        if not whoosh.index.exists_in(index_path, index_name):
            print 'creating %s index at %s' % (index_name, index_path)
            if not os.path.exists(index_path):
                os.makedirs(index_path)
            schema = whoosh.fields.Schema(
                    id = whoosh.fields.ID(stored=True, unique=True),
                    artist = whoosh.fields.TEXT(stored=True),
                    title = whoosh.fields.TEXT(stored=True),
                    lyrics = whoosh.fields.TEXT(stored=True),
                    )
            index = whoosh.index.create_in(index_path, schema, index_name)
            index.writer().commit()
        return whoosh.index.open_dir(index_path, index_name)

    def _get_index_track(self, id, searcher=None):
        q = whoosh.query.Term('id', id)
        results = searcher.search(q)
        if len(results)==0:
            return None
        if len(results)==1:
            return results[0]
        raise JukeboxException('more than one track with id=%s' % id)

    def sync_track_index(self):
        print 'synchronizing track index...'
        searcher = self.track_index.searcher()
        writer = self.track_index.writer()
        try:
            for track in self.tracks:
                index_track = self._get_index_track(unicode(track.id), searcher)
                if index_track is None:
                    print "'%s - %s' missing, indexing..." % (track.artist,
                            track.title)
                    writer.add_document(id=unicode(track.id),
                            artist=track.artist, title=track.title,
                            lyrics=track.lyrics)
                elif index_track['lyrics'] != track.lyrics:
                    print "'%s - %s' has changed, updating..." % (track.artist,
                            track.title)
                    index_track['lyrics'] = track.lyrics
                    writer.update_document(**index_track)
        finally:
            searcher.close()
        writer.commit()
        self.track_index.optimize()
        print 'indexing sync finished'

    def __del__(self):
        self.track_index.close()

    get_track = _not_implemented
    get_tracks = _not_implemented
    tracks = property(get_tracks)

    native_search = _not_implemented

    def _search(self, query, searcher, offset=0, limit=100):
        q = self.query_parser.parse(query)
        results = searcher.search(q, limit=limit)
        return [(results.score(i), self.get_track(r['id']))
                for (i, r) in enumerate(results)]

    def search(self, query):
        searcher = self.track_index.searcher()
        try:
            return self._search(query, searcher)
        finally:
            searcher.close()


class Track:
    get_id = _not_implemented
    id = property(get_id)

    get_artist = _not_implemented
    set_artist = _not_implemented
    artist = property(get_artist, set_artist)

    get_title = _not_implemented
    set_title = _not_implemented
    title = property(get_title, set_title)

    get_lyrics = _not_implemented
    set_lyrics = _not_implemented
    lyrics = property(get_lyrics, set_lyrics)
