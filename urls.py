from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

from django_restapi.responder import *

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^jv3/', include('jv3.urls')),
    (r'^plum/', include('plum.urls')),                       
)
