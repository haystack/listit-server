from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

from django_restapi.responder import *

urlpatterns = patterns('',

    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
#    (r'^admin/(.*)', include('django.contrib.admin.urls')),
    # Uncomment the next line for to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    (r'^jv3/', include('jv3.urls')),
)
