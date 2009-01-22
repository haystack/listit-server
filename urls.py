from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django_restapi.responder import *

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
)

if settings.DEVELOPMENT:
    urlpatterns += patterns('',
        (r'^listit/jv3/', include('jv3.urls')),
        (r'^listit/plum/', include('plum.urls')),
        (r'^(?P<path>.*)$', 'django.views.static.serve', 
                            {'document_root': 'www'})
    )
else:
    urlpatterns += patterns('',
        (r'^jv3/', include('jv3.urls')),
        (r'^plum/', include('plum.urls')),
    )

