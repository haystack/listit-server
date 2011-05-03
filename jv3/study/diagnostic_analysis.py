import os,sys
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array

r = ro.r
emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
wstyke = User.objects.filter(email="wstyke@gmail.com")[0]
katfang = User.objects.filter(email="justacopy@gmail.com")
karger = User.objects.filter(email="karger@mit.edu")
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)

def diaginfos():
   import json
   results = []
   for slog in ServerLog.objects.filter(url='post_diagnostics').values('info'):
      try:
         info = json.loads(slog['info'])[0]
         results.append(info)
      except:
         print sys.exc_info()
   return results

def diaginfos_with_date():
   import json
   results = []
   for slog in ServerLog.objects.filter(url='post_diagnostics').values('when','info'):
      try:
         info = json.loads(slog['info'])[0]
         results.append((slog['when'],info))
      except:
         print sys.exc_info()
   return results


def diaginfos_by_clientid(infos=None):
   import json
   if infos is None: infos = diaginfos()
   return dict((info['clientid'],info) for info in infos)

number_of_distinct_clients = lambda icb: len(icb.keys())
number_of_distinct_users = lambda icb: len(list(set([v['username'] for v in icb.values()])))
number_of_blank_users = lambda icb: len(list([v['username'] for v in icb.values() if v['username'] == '']))

def clients_per_user(infos):
   by_user = {}
   if infos is None: infos = diaginfos()
   for info in infos :
      username = info.get('username','')
      if username == '': continue
      userclients = by_user.get(username,[])
      userclients.append(info)
      by_user[username] = userclients
   return by_user

number_of_clients_per_user = lambda infos: [len(set([X['clientid'] for X in info])) for info in clients_per_user(infos).values()]

def histogram_of_number_of_computers_per_user(width=900,height=500,filename='/var/listit/www-ssl/_studyplots/clients.png'):
   clientsperuser = number_of_clients_per_user(diaginfos())
   print clientsperuser
   #print "one"
   r.png('/tmp/foo',width=1024,height=768)
   aa = r.hist(c(clientsperuser))
   devoff();
   print "twos"
   try:
      print sum(aa[1])
      print "outputting to %s " % filename
      cap.hist(clientsperuser,filename=filename, labels=True,xlabel='number of computers per user', ylabel='number of users', width=width,height=height,title="Number of computers for signed up users (N=%d)" % sum(aa[1]))
   except:
      print sys.exc_info()
   return clientsperuser

def histogram_of_platforms(infos,filename='/var/listit/www-ssl/_studyplots/client_platforms.png'):
   platforms = {}
   infos = [v for v in diaginfos_by_clientid(infos).values()]
   for info in infos:
      platforms[info['platform_os']] = platforms.get(info['platform_os'],0) + 1
   print [x for x in platforms.iteritems()]
   cap.bar([x for x in platforms.iteritems()], width=900,height=500,filename=filename,labels=True,title="Distribution of List-It client installs by platform")
   return platforms

#infos = diaginfos()
#icb = diaginfos_by_clientid(infos)

def number_of_clients_per_day() :
   dis = diaginfos_with_date()
   days = {}
   for when,X in dis:
      bucket = int(long(when) / (24*60.0*60.0*1000.0))
      days[bucket] = days.get(bucket,set([])).union( [X['clientid']] )
   return dict([(x,len(y)) for x,y in days.iteritems()])
