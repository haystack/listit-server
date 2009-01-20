from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

from django_restapi.responder import *

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^listit/jv3/', include('jv3.urls')),
    (r'^listit/plum/', include('plum.urls')),
    (r'^(?P<path>.*)$', 'django.views.static.serve',  {'document_root': '/Users/emax/Desktop/projects/workspace/plum/server/www'}),
)
