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
from jv3.models import Note, NoteForm
import jv3.utils
from jv3.models import Event
from jv3.utils import get_most_recent, basicauth_get_user_by_emailaddr,json_response
import time
from django.template.loader import get_template
import sys,traceback


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
        print request_user
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))
        
        if (request.GET['type'] == 'get_max_log_id'):
            ## "what is the last thing i sent?"
            return self._handle_max_log_request(request_user,request);
        
        ## retrieve the entire activity log
        return self.responder.list(Event.objects.filter(owner=request_user), qs_user)        

    def _handle_max_log_request(self, user,request):
        ## return the max id (used by the client to determine which recordsneed to be retrieved.)
        print "_handle_max_log_request get client is : %s "  % self._get_client(request)
        try:
            most_recent_activity = Event.objects.filter(owner=user,client=self._get_client(request)).order_by("-start");
            # print " records %d : from %s to %s "  % (len(most_recent_activity),most_recent_activity[len(most_recent_activity)-1].start,most_recent_activity[0].start)
            if most_recent_activity:
                return HttpResponse(JSONEncoder().encode({'value':int(most_recent_activity[0].start)}), self.responder.mimetype)
            #print "returning 404-------"
            print "no activity found, returning 404"
        except:
            print sys.exc_info()
            
        return self.responder.error(request, 404, ErrorDict({"value":"No activity found"}));

    def _get_client(self,request):
        if request.GET.has_key('client'):
            return request.GET["client"]
        return None        

    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = authenticate_user(request);
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        committed = [];
        for item in JSONDecoder().decode(request.raw_post_data):
            try:
                matches = Event.objects.filter(owner=request_user,client=item['client'],start=item['start'],entityid=item["entityid"])
                if matches.count() > 0:
                    entry = matches[0]
                else:
                    entry = Event()
                entry.owner = request_user
                entry.start = item['start']
                entry.end = item['end']
                entry.type = item['type']
                entry.entityid = item['entityid']
                entry.entitytype = item['entitytype']
                entry.entitydata = item.get('entitydata',"")
                entry.client = item.get("client","")
                entry.save()
                committed.append(item['start'])
            except StandardError, error:
                print "Error with entry %s item %s " % (repr(error),repr(item))
        pass

        response = HttpResponse(JSONEncoder().encode({'committed':committed}), self.responder.mimetype)
        response.status_code = 200;
        return response

def post_events(request):
    """
    lets the user post new activity in a giant single array of activity log elements
    """
    print "post_events --"
    request_user = authenticate_user(request);
    if not request_user:
        return json_response({"error":"Incorrect user/password combination"}, 401)

    committed = [];
    # print "rpd:"
    # print request.raw_post_data

    for item in JSONDecoder().decode(request.raw_post_data):
        try:
            entry = Event.objects.filter(owner=request_user, start=item['start'], type=item['type'],  entityid=item['entityid'],entitytype=item['entitytype'],client=item['client'])
            if entry.count() == 0 :
                print "creating new event %s -> %s " % (repr(item['start']),item['entityid'])
                entry = Event();
                entry.owner = request_user
                entry.start = item['start']
                entry.type = item['type']
                entry.entityid = item['entityid']
                entry.entitytype = item['entitytype']
                entry.client = item['client']
            else:
                entry = entry[0]
                print "updating old event %s " % entry.start


            entry.end = item['end']
            entry.entitydata = item.get('entitydata',"")
            try:
                entry.save()
            except StandardError, error:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                print "*** print_tb:"
                traceback.print_tb(exceptionTraceback, file=sys.stdout)
                ##sys.exc_info()[2].print_tb()
                ##sys.exc_info()[2].print_stack()
                print "save err with entry %s item %s " % (repr(error),repr(item))
                pass

            committed.append(item['start'])
        except StandardError, error:
            print "Error with entry %s item %s " % (repr(error),repr(item))
            pass
    return json_response({"committed":committed}, 200)
    
