import web
import re
from xml.dom.minidom import Document
import jukebox

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

    doc = Document()
    tracks = doc.createElement("tracks")
    doc.appendChild(tracks)

    q = strip_tags(params.get('q'))
    limit = params.get('limit', 10)

    results = itunes.search(q, limit=limit)
    for score, track in results:
      track_elem = doc.createElement('track')
      track_value = doc.createTextNode(track.title)
      track_elem.appendChild(track_value)
      tracks.appendChild(track_elem)
    return doc.toxml()
    

def strip_tags(value):
  return re.sub(r'<[^>]*?>', '', value)
    

if __name__ == "__main__":
    app.run()

   





