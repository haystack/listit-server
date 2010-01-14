
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
	if deleted == 0:
		deleted=1;
	ratio = ratio + [undeleted*1.0/deleted]
	#ratio.append(undeleted*1.0/deleted)
    return ratio
