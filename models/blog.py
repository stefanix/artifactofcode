import re
import datetime
import markdown

from google.appengine.ext import db
from google.appengine.api import memcache

def slugify(value):
    """
    Adapted from Django's django.template.defaultfilters.slugify.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class Post(db.Model):
    title = db.StringProperty()
    slug = db.StringProperty()
    is_page = db.BooleanProperty(default=False)
    is_entry_page = db.BooleanProperty(default=False)
    pub_date = db.DateTimeProperty(auto_now_add=True)
    edit_date = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty(auto_current_user_add=True)

    body = db.TextProperty()
    body_html = db.TextProperty()

    tags = db.StringListProperty()

    def get_absolute_url(self):
        if self.is_page:
            return "/%s" % (self.slug)
        else:
            return "/blog/%04d/%02d/%02d/%s" % (self.pub_date.year,
                                                self.pub_date.month,
                                                self.pub_date.day,
                                                self.slug)

    def get_edit_url(self, slug_error=False):
        if slug_error:
            slug_error = '?slug_error=1'
        else:
            slug_error = ''
        return "/admin/post/edit/%04d/%02d/%02d/%s%s" % (self.pub_date.year,
                                                       self.pub_date.month,
                                                       self.pub_date.day,
                                                       self.slug,
                                                       slug_error)

    def put(self):
        """
        Make sure that the slug is unique for the given date before
        the data is actually saved.
        """

        # Delete the cached archive list if we are saving a new post
        if not self.is_saved():
            memcache.delete('archive_list')

        # Delete the cached tag list whenever a post is created/updated
        memcache.delete('tag_list')

        # Delete the cached tag list whenever a post is created/updated
        memcache.delete('entry_page_list')

        self.test_for_slug_collision()
        self.populate_html_fields()

        key = super(Post, self).put()
        return key

    def test_for_slug_collision(self):
        if self.is_page:
            # Create a query to check for root slug uniqueness
            query = Post.all(keys_only=True)
            query.filter('is_page = ', True)
            query.filter('slug = ', self.slug)
            # Get the Post Key that match the given query (if it exists)
            post = query.get()
            # If any slug matches were found then an exception should be raised
            if post and (not self.is_saved() or self.key() != post):
                raise PageNameConstraintViolation(self.slug)

        # Build the time span to check for slug uniqueness
        start_date = datetime.datetime(self.pub_date.year,
                                       self.pub_date.month,
                                       self.pub_date.day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta
        # Create a query to check for slug uniqueness in the specified time span
        query = Post.all(keys_only=True)
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', self.slug)
        # Get the Post Key that match the given query (if it exists)
        post = query.get()
        # If any slug matches were found then an exception should be raised
        if post and (not self.is_saved() or self.key() != post):
            raise SlugConstraintViolation(start_date, self.slug)

    def populate_html_fields(self):
        # Setup Markdown with the code highlighter
        md = markdown.Markdown(extensions=['codehilite'])

        # Convert the body Markdown into html
        if self.body != None:
            self.body_html = md.convert(self.body)
            # make relative links root links, this makes wiki-style links work
            self.body_html = re.sub(r'href="([-\w]+)"', r'href="/\1"', self.body_html)



class SlugConstraintViolation(Exception):
    def __init__(self, date, slug):
        super(SlugConstraintViolation, self).__init__("Slug '%s' is not unique for date '%s'." % (slug, date.date()))

class PageNameConstraintViolation(Exception):
    def __init__(self, slug):
        super(PageNameConstraintViolation, self).__init__("Page name '%s' is not unique." % (slug))
