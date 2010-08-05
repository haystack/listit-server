import os,sys
import jv3.study.wUtil as wUtil
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
from jv3.study.ca_plot import make_filename
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
import random

## Makes lines different colors - thickness of the lines as size of note ...
## Calculate hour offset, bin actions by hour, then slide with 6-hour

## window = width in hours of window for counting actions
def calc_time_offset(user, window=6):
    allLogs = ActivityLog.objects.filter(owner=user, action__in = ['note-add','note-edit','note-save','note-delete','sidebar-open','sidebar-close','significant-scroll','notes-reordered'])
    ## Bin by hour
    hourlyActions = [0 for i in range(24)]
    for log in allLogs: 
        hourlyActions[wUtil.msecToDate(log.when).hour] += 1
    hourlyActions.extend(hourlyActions) ## --> creates a double! hr = [0,1,...23,24,1,2,3...] making window code easier!
    ## Determine min k-hour window of activity
    minHour, minSum = 0,  sum(hourlyActions[0:window])  ## initialize to some valid choice
    lastHour, lastSum = 0,0
    for hr in xrange(0,25): ## 0-5, 1-6, ...,23-3, 24-4 ## 
        currSum = sum(hourlyActions[hr:hr+window])
        if currSum < minSum:
            minSum = currSum
            minHour = hr
        pass
    ## Report what the center of the minimum window is!
    print "The center of a", window, "hour window is: ", minHour + (window/2.0)
    return minHour + (window/2.0)




## look at url type notes - define a bookmark carefully (note, serves to help people retrieve page)

## note with url not bookmark is about a particular topic
