## @author Wolfe Styke
## Note Ranking Algorithms - For Shuffle Button Idea
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import datetime
import rpy2
#import rpy2.robjects as ro
#r = ro.r
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)

#cap.set_basedir('/home/emax/public_html/graphs')

## consenting users and notes
# u = [ us for us in User.objects.all() if is_consenting_study2(us)]
# n = Note.objects.filter(owner__in=u)


def _hourDiff(timestamp, hour):
    """ Returns # hours between note creation time of day and hour """
    dt = datetime.datetime.fromtimestamp(int(timestamp)/1000)
    maxH, minH = max(dt.hour, hour), min(dt.hour, hour)
    hourDiff = min(maxH - minH, minH + 24 - maxH)
    return hourDiff

def _todCompare(xTime, yTime, hour):
    """ Time of Day Closeness Comparison """
    xDiff = _hourDiff(xTime, hour)
    yDiff = _hourDiff(yTime, hour)
    if xDiff > yDiff:
        return 1
    elif yDiff > xDiff:
        return -1
    else:
        return 0

def sortByToD(notes, hour):
    """ Sorts notes by closeness to given hour of day """
    notes = notes[:] # copy notes
    notes.sort(lambda x, y: _todCompare(x.created, y.created, hour))
    return notes


