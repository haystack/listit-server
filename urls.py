from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django_restapi.responder import *

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
)

if "STATS_SERVER" in settings.get_all_members() and settings.STATS_SERVER:
    urlpatterns += patterns('',
                            (r'^listit/stats/', include('jv3.stats.urls')),
                            (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}))
    
elif settings.DEVELOPMENT:
    urlpatterns += patterns('',
        (r'^listit/jv3/', include('jv3.urls')),
        (r'^listit/plum/', include('plum.urls')),
        (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}))
    
else: ## deployment!
    urlpatterns += patterns('',
        (r'^jv3/', include('jv3.urls')),
        (r'^plum/', include('plum.urls')),
    )

