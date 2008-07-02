from django.conf.urls.defaults import *

urlpatterns = patterns('',
   url(r'', include('django_restapi_tests.examples.simple')),
   url(r'', include('django_restapi_tests.examples.basic')),
   url(r'', include('django_restapi_tests.examples.template')),
   url(r'', include('django_restapi_tests.examples.custom_urls')),
   url(r'', include('django_restapi_tests.examples.fixedend_urls')),
   url(r'', include('django_restapi_tests.examples.authentication')),
   url(r'', include('django_restapi_tests.examples.submission')),
   url(r'', include('django_restapi_tests.examples.generic_resource')),
   url(r'^admin/', include('django.contrib.admin.urls'))
)
