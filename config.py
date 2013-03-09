import os

APP_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

SETTINGS = {
    'title': 'Nortd Labs Blog',
    'description': "Nortd Labs is a research and development studio. We generate work in the area of art, architecture, and system design.",
    'author': 'Nortd Labs',
    'email': 'helloworld@nortd.com',
    'url': 'http://blog.nortd.com',
    'items_per_page': 20,
    'sidebar_show_entry_pages': True,
    'page_name_to_be_always_top': 'Main',
    'sidebar_show_archive': False,
    'sidebar_show_tags': True,
    # Enable/disable Google Analytics
    # Set to your tracking code (UA-xxxxxx-x), or False to disable
    'google_analytics': 'UA-9834519-3',
    # Enable/disable Disqus-based commenting for posts
    # Set to your Disqus short name, or False to disable
    # 'disqus': 'nortdblog',
    'disqus': False,
}
