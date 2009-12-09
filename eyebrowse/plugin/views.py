from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from jv3.models import Event
from jv3.utils import json_response
import jv3.utils
import django.contrib.auth.models as authmodels
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from django.utils.simplejson import JSONEncoder, JSONDecoder
import time
import sys
import urlparse    
from eyebrowse.models import PageView
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
    err = ''
    try:
        user = authenticate_user(request);    
        if not user:
            return json_response({"error":"Incorrect user/password combination"},401);
        #print "!! get_most_recent %s " % _get_client(request)
        most_recent_activity = Event.objects.filter(owner=user,client=_get_client(request)).order_by("-start");
        if most_recent_activity.count() > 0:
            #print " most recent %d " % int(most_recent_activity[0].start)
            return json_response({'value':int(most_recent_activity[0].start)},200)
        return json_response({'value':0},200)
    except:
        err = sys.exc_info()        
    return json_response({'message':err},500)

def post_events(request):
    ## lets the user post new activity in a giant single array of activity log elements

    request_user = authenticate_user(request);
    if not request_user:
        return json_response({"error":"Incorrect user/password combination"}, 401)

    # user_events = Event.objects.filter(owner=request_user,client=_get_client(request))
    committed = [];
    
    for item in JSONDecoder().decode(request.raw_post_data):
        try:
            entries = Event.objects.filter(owner=request_user,
                                         start=item['start'],
                                         type=item['type'],
                                         entityid=item['entityid'],
                                         entitytype=item['entitytype'],
                                         client=item['client'])
            if entries.count() == 0 : 
                entry = Event();
                entry.owner = request_user
                entry.start = item['start']
                entry.type = item['type']
                entry.entityid = item['entityid']
                entry.entitytype = item['entitytype']
                entry.client = item['client']
            else:
                entry = entries[0]
                
            entry.end = item['end']
            entry.entitydata = item.get('entitydata',"")
            entry.save()
            committed.append(item['start'])
        except StandardError, error:
            print "Error with entry %s item %s " % (repr(error),repr(item))
            pass
    return json_response({"committed":committed}, 200)

## USER PRIVACY 

## @login_required
def get_privacy_urls(request):
    user = authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 
        
    privacysettings = user.privacysettings_set.all()[0]
    
    lst = []
    if privacysettings.whitelist is not None:
        lst = privacysettings.whitelist.split() 

    return json_response({ "code":200, "results": lst }) 

# depricated
## @login_required
def delete_privacy_url(request):
    ## added by emax:
    user = authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 
    
    privacysettings = user.privacysettings_set.all()[0] 

    inpt = request.GET['input'].strip()

    privacysettings.whitelist = ' '.join([ x for x in privacysettings.whitelist.split() if not x == inpt])

    privacysettings.save()
    return HttpResponseRedirect('/settings/')

# depricated
## @login_required
def add_privacy_url(request):
    ## added by emax:
    user = authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 

    privacysettings = user.privacysettings_set.all()[0]

    request_inpt = request.GET['input'].strip()
    if request_inpt.split(','):
        request_inpt = request_inpt.split(',')        

    for inpt in request_inpt:
        if inpt.startswith('http'):
            host = urlparse.urlparse(inpt)[1].strip()
        else:
            host = inpt
            if "/" in host:
                host = host[0:host.find("/")]

        val = {}

        if len(host) > 0:
            if privacysettings.whitelist is not None:
                wlist = privacysettings.whitelist.split(' ')
                if not host in wlist:
                    privacysettings.whitelist = ' '.join(wlist + [host])
                    val["host"] = host
            else:
                privacysettings.whitelist = host
                val["host"] = host
            
    # Save 
    privacysettings.save()
    ## val will be non-null iff it's new
    return json_response(val,200)

@login_required
def delete_url_entry(request):
    urlID = request.POST['ID'].strip()

    url_entry = PageView.objects.filter(id=urlID)
    url_entry.delete()

    return json_response({ "code":200 });

#@login_required
## CALLED ONLY FROM THE PLUGIN, YOS.
def add_delete_from_whitelist(request):
    user = authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 

    privacysettings = user.privacysettings_set.all()[0]
    json = request.raw_post_data

    if len(json.strip()) == 0:
        return json_response({ "code":200 })

    add_dels = JSONDecoder().decode(json)
    #print add_dels
    #print type(add_dels)
    assert type(add_dels) == dict, "Received thing not a dict, erroring"
    adds = add_dels['add']
    dels = add_dels['delete']
    # delete urls
    if privacysettings.whitelist is None:   privacysettings.whitelist = ''
    
    wl = privacysettings.whitelist.split(' ')
    wl = filter( lambda x : x not in dels , wl)
    wl = wl +  [ x for x in adds if not x in wl ] 
    privacysettings.whitelist = ' '.join(wl)
    #print privacysettings.whitelist
    
    # Save 
    privacysettings.save()
    return json_response({ "code":200 });


