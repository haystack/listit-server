from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings
from jv3.models import Event
from jv3.utils import json_response
import jv3.utils
import django.contrib.auth.models as authmodels
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from django.utils.simplejson import JSONEncoder, JSONDecoder
import time
import sys

##
## this set of views are used by the plugin to post new events
##

def authenticate_user(request):
    # this authentication mechanism works for BOTH plugin-style authentication (headers)
    # and cookies (request.USER) which is what is necessary to visit the web site
    # 
    ba_user = jv3.utils.basicauth_get_user_by_emailaddr(request)
    if ba_user is not None:
        return ba_user
    if request.user and request.user.username:
        return request.user
    return None

def _get_client(request):
    ## only available on plugin calls
    if request.GET.has_key('client'):
        return request.GET["client"]
    if request.META.has_key('HTTP_X_CLIENTID'):
        return request.META["HTTP_X_CLIENTID"]
    return None        

def login(request):
    user = authenticate_user(request);
    if not user:
        return json_response({"error":"Incorrect user/password combination"},401);
    return json_response({},200)

def get_most_recent_event_time(request):
    print request
    user = authenticate_user(request);    
    if not user:
        return json_response({"error":"Incorrect user/password combination"},401);
    print "!! get_most_recent %s " % _get_client(request)
    most_recent_activity = Event.objects.filter(owner=user,client=_get_client(request)).order_by("-start");
    if most_recent_activity:
        print " most recent %d " % int(most_recent_activity[0].start)
        return json_response({'value':int(most_recent_activity[0].start)},200)
    
    return json_response({'value':0},200)

def post_events(request):
    """
    lets the user post new activity in a giant single array of activity log elements
    """
    request_user = authenticate_user(request);
    if not request_user:
        return json_response({"error":"Incorrect user/password combination"}, 401)

    user_events = Event.objects.filter(owner=request_user,client=_get_client(request))
    committed = [];
    
    for item in JSONDecoder().decode(request.raw_post_data):
        try:
            if len(user_events.filter(start=item['start'],entityid=item["entityid"])) > 0:
                # print "event log : skipping duplicate entry %d " % item['start'];
                continue
                ##print "Committing %s item %s " % (entry.owner.email,repr(item))
            entry = Event.objects.filter(owner=request_user,
                                         start=item['start'],
                                         type=item['type'],
                                         entityid=item['entityid'],
                                         entitytype=item['entitytype'],
                                         client=item['client'])
            if entry.count() == 0 : 
                entry = Event();
                entry.owner = request_user
                entry.start = item['start']
                entry.type = item['type']
                entry.entityid = item['entityid']
                entry.entitytype = item['entitytype']
                entry.client = item['client']
                
            entry.end = item['end']
            entry.entitydata = item.get('entitydata',"")
            entry.save()
            committed.append(item['start'])
        except StandardError, error:
            print "Error with entry %s item %s " % (repr(error),repr(item))
            pass
    return json_response({"committed":committed}, 200)
