import web
import re
import jukebox
import whoosh.analysis
try:
    import simplejson as json
except ImportError:
    import json

urls = (
	'/search', 'Search',
        '/track/(\d+)/play', 'PlayTrack'
       )

itunes = jukebox.ITunes()
app = web.application(urls, globals())

stopwords = set()
for line in open('stopwords.txt'):
    line = line.strip()
    stopwords.add(line)
word_finder = re.compile(r'[a-zA-Z]+')

stemmer = whoosh.analysis.StemmingAnalyzer()

class Search:
  def POST(self):
    params = dict(web.input())
    if not params.get('q'):
      raise web.webapi.badrequest()

    if params.get('limit') and not params.get('limit').isdigit():
      raise web.webapi.badrequest()
    
    q = strip_tags(params.get('q'))
    words = {}
    for match in word_finder.finditer(q):
        word = match.group(0)
        word = word.lower()
        if word in stopwords or len(word) <= 3:
          continue
        token = word
        if token not in words:
          words[token] = 1
        else:
          words[token] = words[token] + 1
    tags = [x for x, _ in sorted(words.items(),
        cmp=lambda x, y: cmp(y[1], x[1]))][:25]
    q = ' '.join(tags)
    limit = params.get('limit', 20)

    results = itunes.search(q, limit=limit)
    tracks = []
    for score, track in results:
        try:
            tracks.append({
                'id': track.id,
                'title':track.title,
                'artist':track.artist,
                'album':track.album,
                'lyrics':track.lyrics})
        except:
            print "missing track", track.itunes_track
    web.header('Content-Type', 'application/json; charset=utf-8')        
    json_result = json.dumps(dict(tags=tags, tracks=tracks))
    return json_result
    

class PlayTrack:
    def GET(self, id):
      track = itunes.get_track(id)
      itunes.play(track)
      web.header('Content-Type', 'text/html; charset=utf-8')
      return '<body onload="window.close()"></body>'


def strip_tags(value):
  return re.sub(r'<[^>]*?>', '', value)
    

if __name__ == "__main__":
    app.run()

   





