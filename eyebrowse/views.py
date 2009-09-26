import re,sys,time,operator,os,math, datetime
from django.template import loader, Context
from django.http import HttpResponse,HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf.urls.defaults import *
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from eyebrowse.forms import *
from eyebrowse.models import *

## hook for creating relevant Page objects when new jv3.Event objects get created                                     
## by the listit server (which answers calls from listit)                                                             
def create_www_pageviews_for_each_event(sender, created=None, instance=None, **kwargs):
    # print "post-save event for sender %s : %s " % (repr(sender),repr(instance.entityid)) ## debug!!                 
    if (created and instance is not None):
        if instance.entitytype == "schemas.Webpage" and instance.entityid is not None:
            ## print "post-save url: %s " % instance.entityid ## debug!!                                              
            pageview = PageView.from_Event(instance)
            # print "Saving %s " % repr(pageview)                                                                     
            pageview.save()

post_save.connect(create_www_pageviews_for_each_event, sender=Event)
