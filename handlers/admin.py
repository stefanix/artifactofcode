import re
import time
import datetime
import logging

import webapp2
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from models import blog
import view


def handle_flickr_photo_links(body):
    """Convert top-level flickr photo links to embedded images."""
    regex = r'(\b(http://)?(www.flickr.com/photos/[^/]+/[0-9]+)([^ :\s]*)(:(q|t|s|n|m|z|c|l|h|k|o))?)'
    matches = re.findall(regex, body)
    url_rpc_pairs = []
    for match in matches:
        entire_url = match[0]
        image_size_to_fetch = match[5]  # q|t|s|n|m|z|c|l|h|k|o
        if not image_size_to_fetch: image_size_to_fetch = 'z'  # width = 640
        # url something like: http://www.flickr.com/photos/stfnix/8506328751/sizes/z/
        url_to_fetch = 'http://'+match[2]+'/sizes/'+image_size_to_fetch+'/'
        logging.info('fetching: %s' % (url_to_fetch))
        thisrpc = urlfetch.create_rpc()
        url_rpc_pairs.append([entire_url, thisrpc])
        urlfetch.make_fetch_call(thisrpc, url_to_fetch)

    for url_rpc_pair in url_rpc_pairs:
        try:
            result = url_rpc_pair[1].get_result()
            if result.status_code == 200:
                html = result.content
                imageurl = None
                # regex match url in something like:
                # <div id="allsizes-photo">
                #     <img src="http://farm9.staticflickr.com/8530/8495139158_9b0ab3ea23_b.jpg">
                # </div>
                regex = r'id="allsizes-photo">[^<]*<img[^s]*src="([^\"]*)">'
                matches = re.findall(regex, html)
                if matches:
                    imageurl = matches[0]
                if not imageurl:
                    logging.warning("html response size: %s" % (len(html)))
                    logging.warning("pos: %s" % html.find("allsizes-photo"))
                    logging.warning("unable to find image url in html")
                    raise urlfetch.DownloadError
                body = body.replace(url_rpc_pair[0], '![]('+imageurl+')')
        except urlfetch.DownloadError:
            logging.warning("flickr link request timed out or failed.")

    return body


def handle_slug(slug, title):
    """Create slug and page properties.
    If slug is not given generate from title.
    If slug has a '/' prefix make post a root page.
    If slug has a leading '!' also list page on the sidebar.
    """
    slug = slug.strip()
    if slug == '' or slug == '/' or slug == '!' or slug == '!/':
        slug += blog.slugify(title)

    if len(slug)>0 and slug[0] == '!':
        is_entry_page = True
        slug = slug[1:]
    else:
        is_entry_page = False

    if len(slug)>0 and slug[0] == '/':
        is_page = True
        slug = slug[1:]
    else:
        is_page = False

    slug_defaulted = False
    matches = re.findall(r'([-\w]+)', slug)
    if not (bool(slug) and matches and slug == matches[0]):  # not valid slug?
        # fall back to using title
        slug = blog.slugify(title)
        slug_defaulted = True

    return slug, slug_defaulted, is_entry_page, is_page




class CreatePostHandler(webapp2.RequestHandler):

    def get(self, with_title):
        page = view.Page()
        if with_title:
            template_values = {
                'slug_default': '/'+with_title[1:],  # crop slash
                }
        else:
            template_values = {}
        page.render(self, 'templates/admin/post_form.html', template_values)

    def post(self, not_used):
        new_post = blog.Post()
        new_post.title = self.request.get('title')
        new_post.body = self.request.get('body')
        new_post.body = handle_flickr_photo_links(new_post.body)

        new_post.slug, slug_defaulted, new_post.is_entry_page, new_post.is_page = \
                handle_slug(self.request.get('slug'), new_post.title)

        new_post.tags = self.request.get('tags').split()

        if self.request.get('submit') == 'Submit':
            if new_post.title == "" and new_post.body == "":
                self.redirect('/')
            elif slug_defaulted:
                if not new_post.slug:
                    new_post.slug = str(int(time.time()))                
                new_post.put()
                self.redirect(new_post.get_edit_url(True))
            elif not new_post.slug:
                self.redirect('/admin/post/create')
            else:
                new_post.put()
                self.redirect(new_post.get_absolute_url())
        else:
            new_post.populate_html_fields()
            template_values = {
                'post': new_post,
                }
            page = view.Page()
            page.render(self, 'templates/admin/post_form.html', template_values)

class EditPostHandler(webapp2.RequestHandler):

    def get(self, year, month, day, slug):
        year = int(year)
        month = int(month)
        day = int(day)

        # Build the time span to check for the given slug
        start_date = datetime.datetime(year, month, day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta

        # Create a query to check for slug uniqueness in the specified time span
        query = blog.Post.all()
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', slug)
        post = query.get()

        if post == None:
            page = view.Page()
            page.render_error(self, 404)
        else:
            # make sure to do this before prefixing slug
            action_url = post.get_edit_url()
            # prefix slug with page properties
            if post.is_page:
                post.slug = '/'+post.slug
            if post.is_entry_page:
                post.slug = '!'+post.slug
            template_values = {
                'action': action_url,
                'post': post,
                'slug_error': self.request.get('slug_error'),
                }

            page = view.Page()
            page.render(self, 'templates/admin/post_form.html', template_values)

    def post(self, year, month, day, slug):
        year = int(year)
        month = int(month)
        day = int(day)

        # Build the time span to check for the given slug
        start_date = datetime.datetime(year, month, day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta

        # Create a query to check for slug uniqueness in the specified time span
        query = blog.Post.all()
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', slug)
        post = query.get()

        if post == None:
            page = view.Page()
            page.render_error(self, 404)
        else:
            action_url = post.get_edit_url()
            post.title = self.request.get('title')
            post.body = self.request.get('body')
            post.body = handle_flickr_photo_links(post.body)

            post.slug, slug_defaulted, post.is_entry_page, post.is_page = \
                    handle_slug(self.request.get('slug'), post.title)

            # if post.is_page:
            #     post.pub_date = datetime.datetime.now()
            post.edit_date = datetime.datetime.now()

            post.tags = self.request.get('tags').split()

            if self.request.get('submit') == 'Submit':
                if post.title == "" and post.body == "":
                    post.delete()
                    memcache.flush_all()  #makes sure tags are updated
                    self.redirect('/')
                elif slug_defaulted:
                    if not post.slug:
                        post.slug = str(int(time.time()))
                    post.put()
                    self.redirect(post.get_edit_url(True))
                else:
                    post.put()
                    self.redirect(post.get_absolute_url())
            else:
                post.populate_html_fields()
                template_values = {
                    'action': action_url,
                    'post': post,
                }
                page = view.Page()
                page.render(self, 'templates/admin/post_form.html', template_values)

class ClearCacheHandler(webapp2.RequestHandler):

    def get(self):
        memcache.flush_all()

