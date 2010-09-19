from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
from decimal import Decimal
from jv3.study.study import mean, variance
import math
## Walk thru a user's actions, calculating things!

def analyzeUserWalk(user):
    totalDays, activeDays, aliveAndDeadTotal, aliveAndDeadGained = userWalk(user)
    aliveGained = map(lambda x:x[0],aliveAndDeadGained)
    nAddVel = sum(aliveGained)*1.0/activeDays
    nAddVar = variance(aliveGained)
    print "Add v:", nAddVel, ", var:", nAddVar
    deadGained = map(lambda x:x[1],aliveAndDeadGained)
    nDelVel = sum(deadGained)*1.0/activeDays
    nDelVar = variance(deadGained)*1.0
    print "Del v:", nDelVel, ", var:", nDelVar
    printBasicNoteStats(user)
    return nAddVel, nAddVar, nDelVel, nDelVar

def printBasicNoteStats(user):
    notes = Note.objects.filter(owner=user)
    print "# Notes:", notes.count()
    noteLen = map(lambda x:len(x.contents), notes)
    noteLines = map(lambda x:len(x.contents.split('\n')), notes)
    print "Ave #Chars:", mean(noteLen), ", Ave Var:", variance(noteLen) 
    print "Ave #Lines:", mean(noteLines), ", Ave Var:", variance(noteLines)

def userWalk(user):
    userNotes = Note.objects.filter(owner=user)
    userLogs = ActivityLog.objects.filter(owner=user)
    actLogsRepeating = userLogs.filter(action__in=['note-add','note-delete'])
    actLogs = reduceRepeatLogs(actLogsRepeating)
    actLogs.extend(userLogs.filter(action__in=['note-save','sidebar-open']))
    totDays, activeDays, chunkedLogs = chunkLogsByDay(actLogs)
    aliveAndDeadTotal = [] ##  Num (alive, dead) notes total on active day
    aliveAndDeadGained = [] ## Num (alive, dead) notes added/lost on active day
    runningLiving, runningDead = 0,0
    for logs in chunkedLogs:
        liveChange = len(filter(lambda x: x.action=='note-add', logs))
        deadChange = len(filter(lambda x: x.action=='note-delete', logs))
        runningLiving += liveChange
        runningDead += deadChange
        aliveAndDeadTotal.append((runningLiving, runningDead))
        aliveAndDeadGained.append((liveChange,deadChange))
        pass
    return (totDays, activeDays, aliveAndDeadTotal, aliveAndDeadGained)

def reduceRepeatLogs(logs):
    logDict = {}
    for log in logs:
        if log.noteid not in logDict:
            logDict[log.noteid] = [log]
        elif log.when not in map(lambda x:x.when, logDict[log.noteid]):
            logDict[log.noteid].append(log)
    cleanedLogs = []
    for noteid, logArr in logDict.items():
        cleanedLogs.extend(logArr)
        pass
    return cleanedLogs

## Returns list of [#total days, #active days, (lists of logs from diff. active dates)]
def chunkLogsByDay(logsList):
    logsList.sort(lambda x,y:cmp(x.when,y.when))
    chunkedList = reduce(chunkLogsByDayReducer, logsList) ## First entry is for list-compiling, not needed!
    ## Returns (#days between first/last act, #days active, chunkedList)
    return (chunkedList[0][1], len(chunkedList[1:]), chunkedList[1:])

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

