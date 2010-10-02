import web
import re
import jukebox
import simplejson

urls = ('/search', 'Search')

itunes = jukebox.ITunes(sync=True)
app = web.application(urls, globals())

class Search:
  def GET(self):
    params = dict(web.input())
    if not params.get('q'):
      raise web.webapi.badrequest()

    if params.get('limit') and not params.get('limit').isdigit():
      raise web.webapi.badrequest()
    
    q = strip_tags(params.get('q'))
    limit = params.get('limit', 10)

    results = itunes.search(q, limit=limit)
    tracks = []
    for score, track in results:
      tracks.append({'id': track.id, 'title':track.title})
    web.header('Content-Type', 'application/json; charset=utf-8')        
    return simplejson.dumps(tracks)
    

def strip_tags(value):
  return re.sub(r'<[^>]*?>', '', value)
    

if __name__ == "__main__":
    app.run()

   





