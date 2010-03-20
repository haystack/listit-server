import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *
from eyebrowse.delicious.views import *

urlpatterns = patterns('',
                       (r'^tag_the_users/?$', tag_the_users_page),
)
