import re
import datetime
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext import db
from xml.dom import minidom 

from models import blog
import view



def parseDateTime(s):
	"""Create datetime object representing date/time
	   expressed in a string
 
	Takes a string in the format produced by calling str()
	on a python datetime object and returns a datetime
	instance that would produce that string.
 
	Acceptable formats are: "YYYY-MM-DD HH:MM:SS.ssssss+HH:MM",
							"YYYY-MM-DD HH:MM:SS.ssssss",
							"YYYY-MM-DD HH:MM:SS+HH:MM",
							"YYYY-MM-DD HH:MM:SS"
	Where ssssss represents fractional seconds.	 The timezone
	is optional and may be either positive or negative
	hours/minutes east of UTC.
	"""
	if s is None:
		return None
	# Split string in the form 2007-06-18 19:39:25.3300-07:00
	# into its constituent date/time, microseconds, and
	# timezone fields where microseconds and timezone are
	# optional.
	m = re.match(r'(.*?)(?:\.(\d+))?(([-+]\d{1,2}):(\d{2}))?$',
				 str(s))
	datestr, fractional, tzname, tzhour, tzmin = m.groups()
 
	# Create tzinfo object representing the timezone
	# expressed in the input string.  The names we give
	# for the timezones are lame: they are just the offset
	# from UTC (as it appeared in the input string).  We
	# handle UTC specially since it is a very common case
	# and we know its name.
	tz = None

	# Convert the date/time field into a python datetime
	# object.
	x = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")
 
	# Convert the fractional second portion into a count
	# of microseconds.
	if fractional is None:
		fractional = '0'
	fracpower = 6 - len(fractional)
	fractional = float(fractional) * (10 ** fracpower)
 
	# Return updated datetime object with microseconds and
	# timezone information.
	return x.replace(microsecond=int(fractional), tzinfo=tz)
	

class ImportHandler(webapp.RequestHandler):

    def get(self):
      
        if self.request.get('deleteall'):
          query = blog.Post().all()
          entries =query.fetch(1000)
          db.delete(entries)
          memcache.flush_all()      
      
        page = view.Page()
        page.render(self, 'templates/admin/import.html')

    def post(self):
        debug_text = ""
        atom_xml = self.request.get('atom')

        entried_imported = 0
        
        # parse atom xml and add entry
        #
        xmldoc = minidom.parseString(atom_xml) 
        for entry in xmldoc.getElementsByTagName("entry"):
          title = ""
          slug = ""
          body = ""
          tags = ""

          titledoc = entry.getElementsByTagName("title")[1]
          if titledoc.childNodes:
            #print titledoc.firstChild.data
            title = titledoc.firstChild.data

          slugdoc = entry.getElementsByTagName("chyrp:url")[0]
          if slugdoc.childNodes:
            #print slugdoc.firstChild.data
            slug = slugdoc.firstChild.data    

          bodydoc = entry.getElementsByTagName("body")[0]
          if bodydoc.childNodes:
            #print bodydoc.firstChild.data
            body = bodydoc.firstChild.data  

          tagsdoc = entry.getElementsByTagName("chyrp:tags")
          if len(tagsdoc) > 0:
            #print tagsdoc[0].firstChild.data
            tags = tagsdoc[0].firstChild.data
          
          datedoc = entry.getElementsByTagName("published")[0]
          if datedoc.childNodes:
            #print datedoc.firstChild.data
            date = parseDateTime(datedoc.firstChild.data)
            
          new_post = blog.Post()
          new_post.title = title
          new_post.slug = slug
          new_post.body = body
          tagssplit = tags.split(', ')
          if len(tagssplit) == 1 and tagssplit[0] == '':
            pass
          else:
            new_post.tags = tagssplit
          new_post.pub_date = date
          new_post.put()
          
          entried_imported += 1
                        
        template_values = {
            'import_report': True,
            'entried_imported': entried_imported,
            'debug_text': debug_text
            }
        page = view.Page()
        page.render(self, 'templates/admin/import.html', template_values)