#!/usr/bin/env python
#

import config
import os
import sys
import logging

import webapp2

# Force sys.path to have our own directory first, so we can import from it.
sys.path.insert(0, config.APP_ROOT_DIR)
sys.path.insert(1, os.path.join(config.APP_ROOT_DIR, 'externals'))

from handlers import blog, admin, importpost, error


app = webapp2.WSGIApplication(
  [('/', blog.IndexHandler),
   ('/blog/rss2', blog.RSS2Handler),
   ('/blog/tag/([-\w]+)', blog.TagHandler),
   ('/blog/(\d{4})', blog.YearHandler),
   ('/blog/(\d{4})/(\d{2})', blog.MonthHandler),
   ('/blog/(\d{4})/(\d{2})/(\d{2})', blog.DayHandler),
   ('/blog/(\d{4})/(\d{2})/(\d{2})/([-\w]+)', blog.PostHandler),
   ('/admin/clear-cache', admin.ClearCacheHandler),
   ('/admin/post/create(/[-\w]*)?', admin.CreatePostHandler),
   ('/admin/post/edit/(\d{4})/(\d{2})/(\d{2})/([-\w]+)', admin.EditPostHandler),
   ('/admin/import', importpost.ImportHandler),
   ('/([-\w]+)', blog.PageHandler),
   # If we make it this far then the page we are looking
   # for does not exist
   ('/.*', error.Error404Handler),
  ],
  debug=True)
  # debug=os.environ['SERVER_SOFTWARE'].startswith('Dev'))


if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
  logging.getLogger().setLevel(logging.DEBUG)
# logging.debug('a message')
# logging.info('a massage')
# logging.warning('a warning')
# logging.error('an error')
