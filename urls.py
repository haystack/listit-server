from django.conf.urls.defaults import *

from django_restapi.responder import *

urlpatterns = patterns('',
    # Example:
    (r'^jv3/', include('server.jv3.urls')),

    # Uncomment this for admin:
#    (r'^admin/', include('django.contrib.admin.urls')),
)
