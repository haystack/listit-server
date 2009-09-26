import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from eyebrowse.plugin.views import *

urlpatterns = patterns('',
                       (r'^plugin_login$', login),  
                       (r'^plugin_get_max_event$', get_most_recent_event_time),
                       (r'^plugin_post_events/$', post_events),

                       # user privacy
                       (r'^add_privacy_url/$', add_privacy_url),
                       (r'^get_privacy_urls/$', get_privacy_urls),
                       (r'^delete_privacy_url/$', delete_privacy_url),
                       (r'^delete_url_entry/$', delete_url_entry),                       
                       (r'^add_delete_from_whitelist/$', add_delete_from_whitelist),                       
)
