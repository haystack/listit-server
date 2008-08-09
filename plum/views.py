# Create your views here.
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings

from django.utils.simplejson import JSONEncoder, JSONDecoder
import django.contrib.auth.models as authmodels
from django_restapi.authentication import basicauth_get_user 
from server.django_restapi.resource import Resource
from server.django_restapi.model_resource import InvalidModelData
import time

from server.plum.models import Sighting


class  SightingsCollection(Collection):
    ## read is covered by the superclass
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        #request_user = basicauth_get_user(request);        
        #qs_user = Note.objects.filter(owner=request_user)
        return self.responder.list(request, self.queryset)

def sightings_new(request):
    ## for posting from GPSTracker: 
    ## http://www.websmithing.com/portal/Programming/tabid/55/articleType/ArticleView/articleId/2/Google-Map-GPS-Cell-Phone-Tracker.aspx
    sighting = Sighting()
    sighting.lat = request.GET['lat'];
    sighting.lon = request.GET['lng'];
    sighting.when = int(time.time()*1000);
    sighting.dirr = request.GET['dir'];
    sighting.mph= request.GET['mph'];
    sighting.save();
    image_data = open('/z/www/red.png','rb').read();
    # print "data len is %d " % len(image_data)
    return  HttpResponse(image_data, mimetype='image/png');
