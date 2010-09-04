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
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from jv3.models import Note, NoteForm, Event, CachedEventLogStats
from jv3.utils import get_most_recent, basicauth_get_user_by_emailaddr,json_response
import time,sys,traceback,logging
from django.template.loader import get_template

logging.basicConfig(filename='/tmp/eventviewerrors.log-'+repr(time.time()),level=logging.DEBUG)

def authenticate_user(request):
    # this authentication mechanism works for BOTH listit-style and eyebrowse-style authentication
    ba_user = basicauth_get_user_by_emailaddr(request)
    if ba_user is not None:
        return ba_user
    if request.user and request.user.username:
        return request.user
    return None

class EventLogCollection(Collection):

    def read(self,request):
        request_user = authenticate_user(request);
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        if (request.GET['type'] == 'get_max_log_id'):
            clientid = self._get_client(request)                    
            ## "what is the last thing i sent?"
            try:
                return self._handle_max_log_request(request_user,clientid);
            except:
                print sys.exc_info()
                logging.error(str(sys.exc_info()))
            return HttpResponse(JSONEncoder().encode({'value':0, 'num_logs':0}))            

        ## retrieve the entire activity log
        ## return self.responder.list(Event.objects.filter(owner=request_user), qs_user)                
        return HttpResponse(JSONEncoder().encode([]), self.responder.mimetype)

    def _handle_max_log_request(self,user,clientid):
        ## return the max id (used by the client to determine which recordsneed to be retrieved.)
        maxdate,count = self._get_max_helper(user,clientid)
        #print "event_max_log  ",user," returning ", long(maxdate), " count ",long(count)
        return HttpResponse(JSONEncoder().encode({'value':long(maxdate), 'num_logs':long(count)}))

    @staticmethod
    def _get_client(request):
        if request.GET.has_key('client'):
            return request.GET["client"]
        return None

    @staticmethod
    def get_most_recent(events):
        if events.count() > 0:
            return events.order_by('-start')[0]
        return None

    @staticmethod
    def _get_cached_event_log_stats(user,clientid):
        if clientid is not None:
            return CachedEventLogStats.objects.filter(user=user,client=clientid)
        return CachedEventLogStats.objects.filter(user=user)

    @staticmethod
    def _get_event_logs(user,clientid):
        if clientid is not None:
            return Event.objects.filter(owner=user,client=clientid)
        return Event.objects.filter(owner=user)
    
    # uses new caching table awesomeness
    def _get_max_helper(self,user,clientid):
        if self._get_cached_event_log_stats(user,clientid).count() == 0:
            user_event = self._get_event_logs(user,clientid)
            most_recent_event = self.get_most_recent(user_event)
            if most_recent_event is not None:
                maxdate,count = long(most_recent_event.start),len(user_event)
                self._set_maxdate_count_for_user(user,clientid,maxdate)
                return maxdate,count
            return 0,0

        cals = self._get_cached_event_log_stats(user,clientid).order_by('-count')[0]
        return cals.maxdate,cals.count

    def _set_maxdate_count_for_user(self,user,clientid,maxdate):
        tablerecs = self._get_cached_event_log_stats(user,clientid)
        if tablerecs.count() > 0:
            cal = tablerecs.order_by('-count')[0]
        else:
            cal = CachedEventLogStats(user=user,client=clientid)
        cal.maxdate = maxdate
        cal.count = self._get_event_logs(user,clientid).count()
        cal.save()
        pass        
    
    def create(self,request):
        """
        lets the user post new event in a giant single array of event log elements
        """
        request_user = authenticate_user(request);
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        #clientid = self._get_client(request) ## note to emax: this does not work!
        clientid = None
        maxwhen,count = self._get_max_helper(request_user,clientid)

        dupes = 0
        committed = [];
        decoded = JSONDecoder().decode(request.raw_post_data)
        print "event received ",request_user,len(decoded)
        for item in decoded:
            try:
                matches = Event.objects.filter(owner=request_user, start=item['start'],  entityid=item["entityid"])
                if matches.count() > 0:
                    dupes = dupes + 1
                    entry = matches[0]
                else:
                    entry = Event()
                entry.owner = request_user
                entry.start = item['start']
                entry.end = item['end']
                entry.type = item['type']
                entry.entityid = item['entityid']
                entry.entitytype = item['entitytype']
                entry.entitydata = item.get('entitydata',"").encode('ascii','ignore')
                clientid = item['client'] 
                entry.client = item['client']
                entry.save()
                committed.append(item['start'])

                maxwhen = max(maxwhen,entry.start)
                
            except StandardError, error:
                print "Error with entry %s item %s " % (repr(error),repr(item))
            pass

        print "event log dupes ", request_user, " ", dupes
         
        self._set_maxdate_count_for_user(request_user,clientid,maxwhen)        
        response = HttpResponse(JSONEncoder().encode({'committed':committed}), self.responder.mimetype)
        response.status_code = 200;
        return response

