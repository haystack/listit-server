from django.conf.urls.defaults import *
import django.contrib.auth.views
from django.contrib.auth.models import User
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from django_restapi.receiver import *
from jv3.models import SPO, SPOForm, Note, NoteForm, ActivityLog
from jv3.views import SPOCollection, NoteCollection, ActivityLogCollection, userexists, createuser, confirmuser, submit_bug_report, reconsent
from jv3.views import changepassword, changepassword_request, changepassword_confirm, notes_post_multi
from jv3.study import study
from jv3.utils import *
from django.contrib.auth.models import *
from jv3.models import *
from jv3.study.exporter import *
from django.utils.simplejson import JSONDecoder,JSONEncoder
from math import log
from datetime import date
import decimal


def serial_stats(stats):
    return "\n".join(["%s:%s" % (k,JSONEncoder().encode(v)) for k,v in stats])

def summary(request, **kwargs): ## startyear=2009, startmonth=1, startday=1, endyear=2009, endmonth=1, endday=1, dst=-1):
    ## returns total and by-day statistics for
    for (k,v) in kwargs.iteritems():
        kwargs[k] = int(v)

    if not kwargs.has_key("endyear"):
        end_secs = time.mktime(time.localtime())
    else:
        end_secs = time.mktime( (kwargs['endyear'],kwargs['endmonth'],kwargs['endday'],00,00,00,00,00,kwargs.get('dst',-1)))

    start_secs = time.mktime( (kwargs['startyear'],kwargs['startmonth'],kwargs['startday'],00,00,00,00,00,kwargs.get('dst',-1)))
    stats = []
    stats.append( ('start time', time.ctime(start_secs)))
    stats.append( ('end time', time.ctime(end_secs) ))
    stats.append( ('start time msecs' , int(start_secs*1000) ) )
    stats.append( ('end time msecs', int(end_secs*1000) ))
                  
    stats.append(('total users', User.objects.all().count()))
    stats.append(('total consenting users',len(study.non_stop_consenting_users())))

    stats.append(('total notes',Note.objects.all().count()))    
    stats.append(('total notes (from consenting users)',len(study.non_stop_consenting_users())))

    stats.append(('users who have not synced', len(study.users_with_less_than_n_notes(1,User.objects.all()))))
    stats.append(('consenting users who have not synced', len(study.users_with_less_than_n_notes(1))))

    stats.append(('users active during time', len(study.users_active_during(start_secs,end_secs))))
    stats.append(('total notes created during time',len(study.notes_by_users_created_between(start_secs,end_secs,users=User.objects.all()))))
    stats.append(('total notes modified during time',len(study.notes_by_users_edited_between(start_secs,end_secs,users=User.objects.all()))))
    
    response = HttpResponse(serial_stats(stats), "text/plain")
    response.status_code = 200;
    return response;

def cumulativeStuff(request,set,relevant_date_accessor):
    counts = {}
    for n in set:
        day = int(int(relevant_date_accessor(n))/(24*60*60*1000.0))*24*60*60*1000
        counts[day] = counts.get(day,0) + 1;
    response = HttpResponse(JSONEncoder().encode(counts), "text/json")
    response.status_code = 200;
    return response

cumulativeNotes = lambda request: cumulativeStuff(request,Note.objects.all(),lambda note: note.created)
cumulativeUserRegistrations = lambda request: cumulativeStuff(request,UserRegistration.objects.all(), lambda userreg: userreg.when)
        
