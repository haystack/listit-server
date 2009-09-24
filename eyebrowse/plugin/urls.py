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
                       (r'^plugin_post_events/$', views.post_events),
)
