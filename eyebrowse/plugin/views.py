from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from django.utils.simplejson import JSONEncoder, JSONDecoder
import django.contrib.auth.models as authmodels
from jv3.models import Event
from jv3.utils import json_response
import jv3.utils
import time
import sys
import urlparse    
from eyebrowse.models import PageView
from eyebrowse.models import *
from countries.models import Country
from eyebrowse.json.views import uniq
##
## this set of views are used by the plugin to post new events
##

def get_enduser_for_user(user):
    if EndUser.objects.filter(user=user).count() > 0:
        enduser = EndUser.objects.filter(user=user)[0]
    else:
        raise Http404('Internal error. Call brennan or emax. Something is wrong. Houston.')    
    return enduser


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

def save_entry(item, request_user):
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
                
            # yooz dont indent these - disgruntled python user
            entry.end = item['end']
            entry.entitydata = item.get('entitydata',"")
            entry.save()

            return item['start']
        except StandardError, error:
            print "Error with entry %s item %s " % (repr(error),repr(item))
            pass


def post_events(request):
    ## lets the user post new activity in a giant single array of activity log elements
    request_user = authenticate_user(request);
    if not request_user:
        return json_response({"error":"Incorrect user/password combination"}, 401)
    
    logs = JSONDecoder().decode(request.raw_post_data)
    committed = [save_entry(entry, request_user) for entry in logs ]
    hosts = uniq([log['entity']['host'] for log in logs], lambda x:x,None)
    notifications = get_notifications_for_user(request_user,hosts) 
    return json_response({"committed":len(committed), "notifications":notifications}, 200)


def get_notifications_for_user(user,hosts):
    #users = [EndUser.objects.all()[0].user] 
    users = [friendship.to_friend for friendship in user.friend_set.all()]
    recently = int(time.time()*1000 - (30*60*1000)) # 30 min ago
    
    return uniq([dict((('username',page.user.username), ('url',page.url), ('title',page.title), ('host',page.host), ('id', page.url + page.user.username)))
                 for page in PageView.objects.filter(user__in=users,host__in=hosts, endTime__gte=recently) ], lambda x:x['id'],None)
    #except Exception, e:
    #    print "get notifications exception", e 



## USER PRIVACY 

def get_user_following(request):
    user = authenticate_user(request)
    following = [friendship.to_friend.username for friendship in user.friend_set.all().order_by('to_friend__username')]
    followers = [friendship.from_friend.username for friendship in user.to_friend_set.all().order_by('from_friend__username')]
    return json_response({ "code":200, "results": [following, followers] }) 

def get_user_profile(request):
    user = authenticate_user(request)
    enduser = get_enduser_for_user(user)

    first_name = enduser.user.first_name
    last_name = enduser.user.last_name
    email = enduser.user.email
    location = str(Country.objects.filter(printable_name=enduser.location)[0].name)
    homepage = enduser.homepage
    birthdate = enduser.birthdate
    #photo = enduser.photo
    gender = enduser.gender
    tags = ' '.join(tag.name for tag in enduser.tags.all())

    response = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'location': location,
        'tags': tags,
        'homepage': homepage,
        'birthdate': birthdate.ctime(),
        'gender': gender,
        }

    return json_response({ "code":200, "results": response }) 

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
    #return json_response({ "code":200, "results": 'success' }) 

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
## CALLED ONLY FROM THE PLUGIN
def add_delete_from_whitelist(request):
    user = authenticate_user(request)
    if user is None:
        return json_response({ "code":404, "error": "Username or password incorrect" }) 

    privacysettings = user.privacysettings_set.all()[0]
    json = request.raw_post_data

    if len(json.strip()) == 0:
        return json_response({ "code":200 })

    add_dels = JSONDecoder().decode(json)
    assert type(add_dels) == dict, "Received thing not a dict, erroring"
    adds = add_dels['add']
    dels = add_dels['delete']
    # delete urls
    if privacysettings.whitelist is None:   privacysettings.whitelist = ''
    
    wl = privacysettings.whitelist.split(' ')
    wl = filter( lambda x : x not in dels , wl)
    wl = wl +  [ x for x in adds if not x in wl ] 
    privacysettings.whitelist = ' '.join(wl)
    
    # Save 
    privacysettings.save()
    return json_response({ "code":200 });


