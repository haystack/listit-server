from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
from decimal import Decimal
import math
## Walk thru a user's actions, calculating things!


def userWalk(user):
    userNotes = Note.objects.filter(owner=user)
    userLogs = ActivityLog.objects.filter(owner=user)
    #addLogsRepeating = userLogs.filter(action='note-add')
    #deleteLogsRepeating = userLogs.filter(action='note-delete')
    #bothLogs = reduceRepeatLogs(addLogsRepeating)
    #bothLogs.extend(reduceRepeatLogs(deleteLogsRepeating))
    #bothLogs.sort(lambda x,y:cmp(x.when,y.when))
    userLogs = 

    ## Now run thru logs
    aliveAndDeadCount = [] ##  Num (alive, dead) notes total on active day
    aliveAndDeadGained = [] ## Num (alive, dead) notes added/lost on active day
    


def reduceRepeatLogs(logs):
    logDict = {}
    for log in logs:
        if log.noteid not in logDict:
            logDict[log.noteid] = [log]
        if log.noteid in logDict and log.when not in map(lambda x:x.when, logDict[log.noteid]):
                logDict[log.noteid].append(log)
    cleanedLogs = []
    for noteid, logArr in logDict.items():
        cleanedLogs.extend(logArr)
        pass
    return cleanedLogs


## Returns list of (lists of logs from diff. active dates)
def chunkLogsByDay(logsList):
    return reduce(chunkLogsByDayReducer, logsList)[1:]

## helper
def chunkLogsByDayReducer(x, y):
    dayInMS = 86400000
    if type(x) != type([]) and type(x.when)==type(Decimal()):
        ## First value being considered
        dayOfSecondLog = math.floor((y.when-x.when) /dayInMS)
        if y.when - x.when < dayInMS:
            return [[x,dayOfSecondLog], [x,y]]
        else:
            return [[x,dayOfSecondLog],[x],[y]]
    else:
        ## First value stores time start, length of x is (1+#days)
        dayOfLog = math.floor((y.when-x[0][0].when) / dayInMS)
        if dayOfLog > x[0][1]:
            ## The day is beyond the last logged day
            x.append([y])
            x[0][1] = dayOfLog
        else:
            ## Day is same as last logged day
            x[len(x)-1].append(y)
        return x
        
