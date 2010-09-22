## startup
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from jv3.models import *
import jv3.study.wUserWalk as wuw
from django.utils.simplejson import JSONDecoder
import nltk
import jv3.study.content_analysis as ca
from decimal import Decimal
import math
from jv3.study.content_analysis import mean
import jv3.study.wUserWalk as wuw
import json
from jv3.models import Note,ActivityLog
from django.contrib.auth.models import User
from jv3.study.study import safemedian
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
import jv3.study.integrity as integ
import jv3.study.thesis_figures as tfigs
import jv3.study.note_labels as nl
import jv3.study.intention as intent
import jv3.study.content_analysis as ca
import jv3.study.diagnostic_analysis as da
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas
import jv3.study.wFunc as wF
import jv3.study.wClean as wC
import rpy2,sys


emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
c = lambda vv : apply(r.c,vv)

class PerUser:
    
    def __init__(self,user):
        self.u = user
        self._compute_duration()

    def _compute_duration(self):
        # first and last notecapture-focus
        try: 
            self.start = long(ActivityLog.objects.filter(owner=self.u,action='notecapture-focus').order_by('when')[0].when)
            self.end = long(ActivityLog.objects.filter(owner=self.u,action='notecapture-focus').order_by('-when')[0].when)
        except :
            self.start = -1
            self.end = -1
            
        return (self.start,self.end)

    def consenting(self):
        return is_consenting_study2(self.u)
    
    def duration(self):
        return (self.start,self.end)

    def days_of_use(self):
        (start,end) = self.duration()
        return (end-start)/(1.0*24*3600*1000)

    def actions(self,n=None):
        if n:
            return ActivityLog.objects.filter(owner=self.u,noteid=n.jid)
        return ActivityLog.objects.filter(owner=self.u)

    def notes(self):
        return Note.objects.filter(owner=self.u).order_by('created')

    def deleted_per_day(self):
        start,end = self.duration()
        actions = ActivityLog.objects.filter(action="note-delete",owner=self.u)
        del_per_day = []
        while start < end:
            start = start + 24*60*60*1000
            dayend = start + 24*60*60*1000
            del_per_day.append(actions.filter(when__gte=start,when__lte=dayend).count())
            start = dayend
        return del_per_day

    def created_per_day(self):
        start,end = self.duration()
        n = ActivityLog.objects.filter(action="note-add",owner=self.u)        
        notes_per_day = []
        while start < end:
            start = start + 24*60*60*1000
            dayend = start + 24*60*60*1000
            notes_per_day.append(n.filter(when__gte=start,when__lte=dayend).count())
            start = dayend
        return notes_per_day
    

## static methods
    
def perusers_for_more_than_n_days(min_days,out_of,maxN=None):
    if out_of is None: out_of = [u for u in User.objects.all() if is_consenting_study2(u)]
    results = []
    for x in out_of:
        su = PerUser(x)
        if su.days_of_use() >= min_days:
            results.append(su)
        if maxN is not None and len(results) > maxN:
            return results

    return results
    #return [ x for x in out_of if x.days_of_use() >= min_days ]


## 
## QUESTION: are there individual differences in KEEPING -- whether people ACCUMULATE
##   NOTES or use listit as a temporary holding ground for information


## METHOD 1:histogram the ratio of kept : deleted notes to see if there are multiple modes

def make_lists_for_plot(users):
    deleted = []
    undeleted = []
    for user in users:
        deleted = deleted + [len(Note.objects.all().filter(owner=user).filter(deleted=1))]
        undeleted = undeleted + [len(Note.objects.all().filter(owner=user).filter(deleted=0))]
    
    return deleted, undeleted
def make_lists_for_hist(users):
    ratio = []
    for user in users:
        deleted = len(Note.objects.all().filter(owner=user).filter(deleted=1))
        undeleted = len(Note.objects.all().filter(owner=user).filter(deleted=0))
	if deleted == 0: deleted=1;
	ratio = ratio + [undeleted*1.0/deleted]
	#ratio.append(undeleted*1.0/deleted)
    return ratio

## ============================================================================================
## New user selection stuff


def active_days(userid):
    if userid not in wuw._walk_cache:
        wuw._walk_cache[userid] = wuw.userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = wuw._walk_cache[userid]
    if (totDays <= 1 or activeDays <= 1): print '!!!!!!!!!!!!!!! ',userid,' has only 1 active day'        
    return activeDays

def active_days_for_users(users):
    b = []
    for x in users:
        try:
            b.append((x.id,cas.active_days(x.id)))
        except:
            import sys
            print sys.exc_info()

    return dict(b)

def get_consenting_active_for(userpool,thresh_days=30):
    active_days = active_days_for_users(userpool)
    makes_the_cut = [x for x,y in active_days.iteritems() if y > thresh_days]
    return [u for u in userpool if u.id in makes_the_cut],dict([(x,y) for x,y in active_days.iteritems() if x in makes_the_cut])

def get_awesome(userpool,thresh_days=30,MIN_NOTES=30,MIN_LOGS=1000):
    userpool = filter(lambda u: u not in [emax,emax2,brenn],userpool)
    active_days = active_days_for_users(userpool)
    makes_the_cut = [x for x,y in active_days.iteritems() if y > thresh_days]
    return [u for u in userpool if u.id in makes_the_cut and u.note_owner.count() > MIN_NOTES and u.activitylog_set.count() > MIN_LOGS ],dict([(x,y) for x,y in active_days.iteritems() if x in makes_the_cut])
