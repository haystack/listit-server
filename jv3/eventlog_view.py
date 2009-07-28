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
from jv3.utils import get_most_recent, basicauth_get_user_by_emailaddr
import time
from django.template.loader import get_template
import sys


class EventLogCollection(Collection):

    def read(self,request):
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))
        
        if (request.GET['type'] == 'get_max_log_id'):
            ## "what is the last thing i sent?"
            return self._handle_max_log_request(request_user,request);
        
        ## retrieve the entire activity log
        return self.responder.list(Event.objects.filter(owner=request_user), qs_user)        

    def _handle_max_log_request(self,user,request):
        ## return the max id (used by the client to determine which recordsneed to be retrieved.)
        most_recent_activity = Event.objects.filter(owner=user,client=self._get_client(request)).order_by("-start");
        if most_recent_activity:
            return HttpResponse(JSONEncoder().encode({'value':int(most_recent_activity[0].start)}), self.responder.mimetype)
        print "returning 404-------"
        return self.responder.error(request, 404, ErrorDict({"value":"No activity found"}));

    def _get_client(self,request):
        if request.GET.has_key('client'):
            return request.GET["client"]
        return None        

    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        user_events = Event.objects.filter(owner=request_user,client=self._get_client(request))
        committed = [];
        for item in JSONDecoder().decode(request.raw_post_data):
            try:
                if len(user_events.filter(start=item['start'],entityid=item["entityid"])) > 0:
                    print "event log : skipping duplicate entry %d " % item['start'];
                    continue
                ##print "Committing %s item %s " % (entry.owner.email,repr(item))
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
