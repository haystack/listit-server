import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import eyebrowse.views
import eyebrowse.json.urls
import eyebrowse.pages.urls
import eyebrowse.plugin.urls

lib = os.path.join(
    os.path.dirname(__file__), 'lib'
)

profile_uploads = os.path.join(
    os.path.dirname(__file__), 'profiles'
)

urlpatterns = eyebrowse.json.urls.urlpatterns
urlpatterns += eyebrowse.pages.urls.urlpatterns
urlpatterns += eyebrowse.plugin.urls.urlpatterns

## enable static serving for standalone server
if settings.DEVELOPMENT:
    urlpatterns += patterns('',
                            (r'^lib/(?P<path>.*)$', 'django.views.static.serve',{ 'document_root': lib }),
                            (r'^profiles/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': profile_uploads }))

    
    
