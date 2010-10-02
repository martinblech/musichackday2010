import os
import urllib2, urllib
import re
import urlparse
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from xml.dom import minidom

__name__ = 'pymusixmatch'
__version__ = '0.0.1'
__doc__ = 'A python interface to MusixMatch web service'
__license__ = 'gpl'

WS_SERVER = ('api.musixmatch.com', '/ws/1.0/')

#My api key -> fe546221a278269d69df60d34bb5df03

__cache_dir = None
__cache_enabled = False

OK = 200
ERRORS = {400: 'request had bad syntax or was inherently impossible to be satisfied',
          401: 'authentication failed, probably because of a bad API key',
          402: 'a limit was reached, either you exceeded per hour requests limits or your balance is negative',
          404: 'requested resource was not found',
          405: 'requested method was not found'}

class ServiceException(Exception):
    def __init__(self, status, msg):
        self._status = status
        self._msg = msg
	
    def __str__(self):
        return self._msg
	
    def get_id(self):
	return self._status

class _Request(object):
    """Representing an abstract web service operation."""

    global WS_SERVER
    (HOST_NAME, HOST_SUBDIR) = WS_SERVER

    def __init__(self, method_name, params, api_key):
        self.params = params
        self.method = method_name
        self.params['format'] = 'xml'
        self.params['apikey'] = api_key

    def _download_response(self):
        """Returns a response"""
        data = []
        for name in self.params.keys():
            data.append('='.join((name, urllib.quote_plus(self.params[name].replace('&amp;', '&').encode('utf8')))))
        data = '&'.join(data)
        url = "http://" + self.HOST_NAME + self.HOST_SUBDIR + self.method + '?' + data
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        return response.read() 

    def execute(self, cacheable=False):
        if is_caching_enabled() and cacheable:
            response = self._get_cached_response()
        else:
            response = self._download_response()
        self._check_error(response)
        return minidom.parseString(response)

    def _get_cache_key(self):
        """Cache key""" 
        keys = self.params.keys()[:]
        keys.sort()
        string = self.method
        for name in keys:
            string += name
            string += self.params[name]
        return get_md5(string)

    def _is_cached(self):
        """Returns True if the request is available in the cache."""
        return os.path.exists(os.path.join(_get_cache_dir(), self._get_cache_key()))

    def _get_cached_response(self):
        """Returns a file object of the cached response."""
        if not self._is_cached():
            response = self._download_response()
            response_file = open(os.path.join(_get_cache_dir(), self._get_cache_key()), "w")
            response_file.write(response)
            response_file.close()
        return open(os.path.join(_get_cache_dir(), self._get_cache_key()), "r").read()

    def _check_error(self, text):
        doc = minidom.parseString(text)
        e = int(_extract(doc, 'status_code'))
        if e != OK:
            if ERRORS.has_key(e):
                raise ServiceException(e, ERRORS[e])
            raise ServiceException(e, 'Unknown error')

class _BaseObject(object):
    """An abstract webservices object."""
        
    def __init__(self, api_key):                
        self.api_key = api_key
    
    def _request(self, method, cacheable=False, params=None):
        if not params:
            params = self._get_params()    
        return _Request(method, params, self.api_key).execute(cacheable)
    
    def _get_params(self):
        return dict()

class Track(_BaseObject):
    """A MusixMatch track."""
	
    def __init__(self, title, artist, mbid, api_key):
        _BaseObject.__init__(self, api_key)
	self.title = title
        self.artist = artist
        self.mbid = mbid

    def __repr__(self):
        return self.get_artist() + ' - ' + self.get_title()

    def get_title(self):
        return self.title

    def get_artist(self):
        return self.artist

    def get_mbid(self):
        return self.mbid

    def get_lyrics(self):
        doc = self._request("track.get", True, {'track_mbid': self.mbid})
        return Lyrics(_extract(doc, 'lyrics_id'), self, self.api_key)

class Lyrics(_BaseObject):
    """ A MusixMatch lyrics """

    def __init__(self, id, track, api_key):
        _BaseObject.__init__(self, api_key)
        self.id = id
        self.track = track
    
    def __repr__(self):
        return self.track.get_artist() + ' - ' + self.track.get_title() + ' - ' + self.get_id()

    def get(self):
        doc = self._request("lyrics.get", True, {'lyrics_id': self.id})
        return _extract(doc, 'lyrics_body')

    def get_id(self):
        return self.id

    def get_track(self):
        return self.track


class _Search(_BaseObject):
	"""An abstract class. Use one of its derivatives."""
	
	def __init__(self, ws_prefix, search_terms, api_key):
		_BaseObject.__init__(self, api_key)
		self._ws_prefix = ws_prefix
		self.search_terms = search_terms
		self._last_page_index = 0
	
	def _get_params(self):
		params = {}
		for key in self.search_terms.keys():
			params[key] = self.search_terms[key]
		return params
	
	def get_total_result_count(self):
		"""Returns the total count of all the results."""
		
		doc = self._request(self._ws_prefix + ".search", True)
		return _extract(doc, "available")
	
	def _retreive_page(self, page_index):
		"""Returns the node of matches to be processed"""	
		params = self._get_params()
		params["page"] = str(page_index)
		doc = self._request(self._ws_prefix + ".search", True, params)
		
		return doc.getElementsByTagName('body')[0]
	
	def _retrieve_next_page(self):
		self._last_page_index += 1
		return self._retreive_page(self._last_page_index)


class LyricsSearch(_Search):
	def __init__(self, artist_name, track_title, api_key):	
		_Search.__init__(self, "track", {"q_track": track_title, "q_artist": artist_name}, api_key)

	def get_next_page(self):
		"""Returns the next page of results as a sequence of Track objects."""
		master_node = self._retrieve_next_page()
		
		list = []
		for node in master_node.getElementsByTagName("track"):
                        track = Track(
                                _extract(node, "track_name"),
                                _extract(node, "artist_name"),
                                _extract(node, "track_mbid"),
                                self.api_key)
			list.append(Lyrics(_extract(node, "lyrics_id"), track, self.api_key))
		return list

def search_for_lyrics(artist_name, track_name, api_key):
    return LyricsSearch(artist_name, track_name, api_key)


def _extract(node, name, index = 0):
    """Extracts a value from the xml string"""
    try:
        nodes = node.getElementsByTagName(name)
        
        if len(nodes):
            if nodes[index].firstChild:
                return nodes[index].firstChild.data.strip()
            else:
                return None
    except:
        return None

def _extract_all(node, name, limit_count = None):
    """Extracts all the values from the xml string. returning a list."""
    
    list = []
    
    for i in range(0, len(node.getElementsByTagName(name))):
        if len(list) == limit_count:
            break
        list.append(_extract(node, name, i))
    return list

def enable_caching(cache_dir = None):
    global __cache_dir
    global __cache_enabled

    if cache_dir == None:
        import tempfile
        __cache_dir = tempfile.mkdtemp()
    else:
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        __cache_dir = cache_dir
    __cache_enabled = True

def disable_caching():
    global __cache_enabled
    __cache_enabled = False

def is_caching_enabled():
    """Returns True if caching is enabled."""
    global __cache_enabled
    return __cache_enabled

def _get_cache_dir():
    """Returns the directory in which cache files are saved."""
    global __cache_dir
    global __cache_enabled
    return __cache_dir

def get_md5(text):
    """Returns the md5 hash of a string."""
    hash = md5()
    hash.update(text.encode('utf8'))
    return hash.hexdigest()

