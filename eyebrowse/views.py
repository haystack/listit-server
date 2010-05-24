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
from eyebrowse.models import *
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder
from django.core.mail import send_mail
from django.template import loader, Context
import json

def get_title_from_evt(evt):
    if evt.entitydata:
        foo = JSONDecoder().decode(evt.entitydata)
        if foo:
            foo = foo[0]
            if foo:
                foo = foo['data']
                if foo:
                    foo = JSONDecoder().decode(foo)
                    if foo.has_key('title'):
                        return foo['title']
                    if foo.has_key('data'):
                        foo = JSONDecoder().decode(foo['data'])
                        if foo.has_key('title'):                    
                            return foo['title']
    return 

## hook for creating relevant Page objects when new jv3.Event objects get created 
## by the listit server (which answers calls from listit)                    
def create_www_pageviews_for_each_event(sender, created=None, instance=None, **kwargs):
    #print "post-save event for sender %s : %s " % (repr(sender),repr(instance.entityid)) 
    if (created and instance is not None):
        if instance.entitytype == "schemas.Webpage" and instance.entityid is not None:
            ## print "post-save url: %s " % instance.entityid ## debug!!
            pageview = PageView.from_Event(instance)
            # print "Saving %s " % repr(pageview)                                     
            pageview.save()

post_save.connect(create_www_pageviews_for_each_event, sender=Event, dispatch_uid='booz')


def email_users_eyebrowse(users,subject,template):
    t = loader.get_template(template)
    for u in users:
        #reg = get_newest_registration_for_user_by_email(u.email)
        if u.email == None:
            print "No registration found for user %s. Skipping" % repr(u.email)
            continue

        c = Context({'username':u.username})
        send_mail(subject, t.render(c), 'eyebrowse@csail.mit.edu', [u.email], fail_silently=False)
