from django.conf.urls.defaults import *
import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.syndication.views import feed
from eyebrowse.blog.views import *
from eyebrowse.blog.feeds import *

feeds = {
    'rss': RssFeed,
    'atom': AtomFeed,
    }

urlpatterns = patterns('',
                       url(r'^blog/?$', blog),
		       (r'^blog/(\d{4,4})/(\d{2,2})/([\w\-]+)/$', singlepost),
                       )



