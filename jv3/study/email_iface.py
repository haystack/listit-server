## startup
import os,sys,csv,json
from django import forms
from django.http import HttpResponseRedirect, HttpResponse,HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *

import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas

from django.db.models.query import QuerySet
from jv3.study.ca_plot import make_filename
import jv3.study.exporter as exporter

consenting = None 
recent_users = None

def _history_read():
   import csv,settings,time
   f0 = "%s/%s" % (settings.KARGER_EMAIL_IFACE_DB,"index.csv")
   datas = []
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      [ datas.append( { "id" : r[0], "when" : r[1], "to": r[2], "subject":r[3], "body":r[4], "misc":r[5] } ) for r in rdr ] 
      F.close()
   return datas

def _history_write(history):
    # history is a list of dict s [ {when: "", to: "", "text" : "" } ... ]
   import csv,settings,time
   f0 = "%s/%s" % (settings.KARGER_EMAIL_IFACE_DB,"index.csv")
   f1 = "%s/%s" % (settings.KARGER_EMAIL_IFACE_DB,"index-%d-%d-%d%d.csv" % (time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday, time.localtime().tm_hour))
   for f in [f0,f1]:
      print f
      F = open(f,'w')
      wtr = csv.writer(F)
      [ wtr.writerow([item['id'], item['when'], item['to'], item['subject'], item['body'], item['misc']]) for item in history ]
      F.close()
      pass
   pass

def _history_append(rec):
    hh = _history_read()
    hh.append(rec)
    _history_write(hh)
    return rec

send_thread = None
send_thread_running = False

def _history_update(txn):
   # update relevant rwo
   hh = _history_read()
   new_history = [h for h in hh if not h['id'] == txn['id']] + [txn]
   _history_write(new_history)
   pass

def  _send_email(txn):
    # magical method which sets up a thread
    import jv3.utils
    global send_thread_running
    send_thread_running = True
    global send_thread
    def _send_thread():
        print send_thread_running
        for to in txn["to"]:
            if not send_thread_running: break;
            print " -- sending email to -- ", to, "--", txn["subject"], "--", txn["body"]
            b = dict(txn)
            b["to"] = txn["to"][0:txn["to"].index(to)]
            _history_update(b)
            time.sleep(1)
    import threading
    send_thread = threading.Timer(0.1,_send_thread)
    send_thread.start()
    pass

def _check_auth(request):
    print "auth? ", request.user.is_authenticated(), repr(request.user)
    return request.user.is_authenticated() and not request.user.is_anonymous() and request.user.is_staff

def ke_get_users(request):
    if not _check_auth(request): return HttpResponseForbidden()
    return HttpResponse(json.dumps(len([u.email for u in User.objects.all()])),'text/json')

def ke_get_consenting_users(request):
    if not _check_auth(request): return HttpResponseForbidden()
    if consenting is None:
       _start_recent_users_thread()
       return HttpResponse(json.dumps([]),'text/json')
    return HttpResponse(json.dumps(len([u.email for u in consenting])),'text/json')

def ke_get_last_2_months_users(request):
   if not _check_auth(request): return HttpResponseForbidden()
   global recent_users
   if recent_users is None:
      import sys
      print >> sys.stderr, "starting thread......"
      #_ start_recent_users_thread()
      return HttpResponse("0",'text/json')
   return HttpResponse(json.dumps(len(recent_users)),'text/json')

def ke_get_email_history(request):
    if not _check_auth(request): return HttpResponseForbidden()        
    tosbyid = {}
    raw_history = _history_read()
    # compile the tos into one
    [ tosbyid.update([(rec['id'],tosbyid.get(rec['id'],[])+[rec['to']])]) for rec in raw_history]

    # this will get overwritten

    histbyid = dict([(rec['id'],rec) for rec in raw_history])

    for rid in tosbyid.keys():
        histbyid[rid]['to'] = tosbyid[rid]
        
    return HttpResponse(json.dumps(histbyid.values()), 'text/json')

def ke_cancel_send(request):
    if not _check_auth(request): return HttpResponseForbidden()        
    global send_thread
    global send_thread_running
    send_thread_running = False
    if send_thread is not None:
        try:            
            send_thread.cancel();
        except e:
            pass
        pass
    return HttpResponse("{}","text/json")

def ke_check_status(request):
    if not _check_auth(request): return HttpResponseForbidden()    
    id = request.GET['id']
    print id
    hist = _history_read()
    tos = [r['to'] for r in hist  if r['id'] == id]
    return HttpResponse(json.dumps(tos),'text/json')   

randid  = lambda N=10: ''.join([chr(ord('A')+random.randint(0,23)) for x in range(N)])


def ke_send_email(request):
   global consenting,recent
   if not _check_auth(request): return HttpResponseForbidden()    
   datas = json.loads(request.raw_post_data)

   subject  = datas["subject"]
   body  = datas["body"]   
   to_mode = datas["to"]
   matching_users = { "all" : User.objects.all(), "consenting" : consenting, "recent" : recent_users }.get(to_mode,None)
   if matching_users is None:
      HttpResponse(json.dumps({}), 'text/json')
   email_matching = [x[0] for x in matching_users.values_list('email')]
   new_record = { "id" : randid(), "when" : "%d" % (time.time()*1000), "to": email_matching, "subject": subject, "body" : body, "misc" : ""}
   _send_email(new_record)    
   return HttpResponse(json.dumps(new_record), 'text/json')


def compute_recent_users():
   import time
   print "computing recent users >>>>>>"
   try:
      print "computing conseting"

      global consenting
      consenting = [ u for u in User.objects.all() if is_consenting_study2(u)]
      print "done with conseting"
      today = lambda : long(time.time()*1000.0)
      months_to_msec = lambda months: long(24*60*60*1000*30*months)
      userids_anmonths = lambda n=2: set([u[0] for u in ServerLog.objects.exclude(user=None).filter(when__gt=long(today()-months_to_msec(n))).values_list('user')])
      u = User.objects.filter(id__in=userids_anmonths())
      print "done computing recent users"
   except e:
      import sys
      print sys.exc_info()
   return u

_srut_thread = None
def _start_recent_users_thread():
   import threading
   global _srut_thread 
   def doit():
      while True:
         global recent_users
         recent_users = compute_recent_users()
         time.sleep(60*60*24*7*4)
   if _srut_thread is None:
      _srut_thread = threading.Timer(0.1,doit)
      _srut_thread.start()


                              
                              
   
