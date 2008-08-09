
from django.conf.urls.defaults import *
import django.contrib.auth.views
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from django_restapi.receiver import *
from server.plum.models import Sighting
from server.plum.views import sightings_new, SightingsCollection
from django_restapi.authentication import HttpBasicAuthentication, HttpDigestAuthentication, djangouser_auth

sightings_view = SightingsCollection(
    queryset=Sighting.objects.all(),
    permitted_methods = ('GET',),
    expose_fields = ['lat', 'lon', 'dirr', 'when', 'mph'],
    responder=JSONResponder() );

urlpatterns = patterns('server.plum.views.',
                       (r'^sightings$', sightings_view),
                       (r'^gps$', sightings_new));
