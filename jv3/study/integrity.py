## startup
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
from django.db.models.query import QuerySet
from jv3.study.ca_plot import make_filename
r = ro.r
c = lambda vv : apply(r.c,vv)

## integrity distribution

def createadddist(u):
   nid2when = {}
   nid2create = {}

   # BUG IN DJANGO? query returns 0 
   # u = User.objects.filter(id=u.id) ## reproducible error
   if type(u) == User:
       u = [x for x in User.objects.filter(id=u.id)]
   elif type(u) == QuerySet:
       u = [x for x in u]
       
   # print u,type(u),len(u)
   print "alog ", ActivityLog.objects.filter(action__in=["note-add"],owner__in=u).count()

   keh = lambda o,nid : "%d:%d" % (o,nid)
   
   for when,noteid,owner in ActivityLog.objects.filter(owner__in=u,action="note-add").values_list('when','noteid','owner'):
      nid2when[keh(owner,noteid)] = nid2when.get(keh(owner,noteid),[]) + [when]

   for noteid,when,owner in reduce(lambda x,y: x+y, [ [x for x in U.note_owner.all().values_list('jid','created','owner')] for U in u]):
      nid2create[keh(owner,noteid)] = when

   print "notes length %d "% len(nid2create)
   print "alog length %d " % len(nid2when)
   
   print "notes missing %d " %len( [x for x in nid2when.keys() if x not in nid2create.keys()])
   print "alog missing %d " %len([x for x in nid2create.keys() if x not in nid2when.keys()])
   print "intersection %d " %len([x for x in nid2create.keys() if x in nid2when.keys()])

   intersection = [x for x in nid2create.keys() if x in nid2when.keys()]

   number = [len(x) for x in nid2when.values()]
   mind = [float(min(nid2when[T]) - nid2create[T]) for T in intersection ]   
   maxd = [float(max(nid2when[T]) - nid2create[T]) for T in intersection ]

   bogusnotes = [Note.objects.filter(jid=T.split(':')[1],owner=T.split(':')[0]) for T in intersection if float(min(nid2when[T]) - nid2create[T]) > 10000]

   return (number,mind,maxd,bogusnotes)
