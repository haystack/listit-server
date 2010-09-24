from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
from decimal import Decimal
import math
import jv3.study.content_analysis as ca
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
    actLogs = reduceRepeatLogsBasic(actLogsRepeating)
    actLogs.extend(reduceRepeatLogsBasic(userLogs.filter(action__in=['note-save','sidebar-open'])))
    if len(actLogs) == 0:
        return (0,0,[],[])
    totDays, activeDays, chunkedLogs = chunkLogsByDay(actLogs)
    aliveAndDeadTotal = [] ##  Num (alive, dead) notes total on active day
    aliveAndDeadGained = [] ## Num (alive, dead) notes added/lost on active day
    runningLiving, runningDead = 0,0
    for logs in chunkedLogs:
        # print "=================================="
        # print [(x.when,x.action) for x in logs]
        liveChange = len(filter(lambda x: x.action=='note-add', logs))
        deadChange = len(filter(lambda x: x.action=='note-delete', logs))
        runningLiving += liveChange
        runningDead += deadChange
        aliveAndDeadTotal.append((runningLiving, runningDead))
        aliveAndDeadGained.append((liveChange,deadChange))
        pass
    return (totDays, activeDays, aliveAndDeadTotal, aliveAndDeadGained)

# this is buggy
# def reduceRepeatLogs(logs):
#     logDict = {}
#     whenSet = {}
#     for log in logs:
#         if log.noteid not in logDict: ## Noteid has no logs
#             logDict[log.noteid] = [log]
#             whenSet[log.noteid] = set([log.when])
#         elif log.when not in whenSet: ## noteid has logs, ensure no time conflicts
#             logDict[log.noteid].append(log)
#             whenSet[log.noteid] = whenSet[log.noteid].union([log.when])
#         pass
#     cleanedLogs = []
#     for noteid, logArr in logDict.items():
#         cleanedLogs.extend(logArr)
#         pass
#     return cleanedLogs


def reduceRepeatLogsValues(logs):
    logDict = {}
    whenSet = {}
    for log in logs:
        if log["noteid"] not in logDict:
            logDict[log["noteid"]] = [log]
            whenSet[log["noteid"]] = set([log["when"]])
        elif log["when"] not in whenSet:  # map(lambda x:x["when"], logDict[log["noteid"]]):
            logDict[log["noteid"]].append(log)
            whenSet[log['noteid']] = whenSet[log['noteid']].union([log["when"]])
    return reduce(lambda x,y:x+y,logDict.values(),[])

def reduceRepeatLogsValues2(logs):
    whenSet = set([])
    results = []
    for log in logs:
        if log["when"] not in whenSet:
            results.append(log)
            whenSet = whenSet.union([log["when"]])
    return results

def reduceRepeatLogsBasic(logs):
    whenSet = set([])
    results = []
    for log in logs:
        if log.when not in whenSet:
            results.append(log)
            whenSet = whenSet.union([log.when])
    return results

reduceRepeatLogs = reduceRepeatLogsBasic

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


_walk_cache = {}
# these guys are feature extractors much like ca's but per user

def user_percent_active_days(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    if (totDays <= 1 or activeDays <= 1): print '!!!!!!!!!!!!!!! ',userid,' has only 1 active day'        
    return ca.make_feature('percent_days_active',activeDays / (1.0*totDays))
def user_mean_alive_percent(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    #for alive,dead in adeadtotal: print alive,",",dead
    return ca.make_feature('mean_alive_notes',mean( [(alive/(1.0*(alive+dead+0.00001))) for alive,dead in adeadtotal ] ))
def user_var_alive_percent(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('variance_alive_notes',variance( [(alive/(1.0*(alive+dead+0.00001))) for alive,dead in adeadtotal ] ))

def user_mean_alive(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    #for alive,dead in adeadtotal: print alive,",",dead
    return ca.make_feature('mean_alive_notes',mean( [alive for alive,dead in adeadtotal ] ))
def user_var_alive(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('variance_alive_notes',variance( [alive for alive,dead in adeadtotal ] ))
def user_mean_dead(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    #for alive,dead in adeadtotal: print alive,",",dead
    return ca.make_feature('mean_alive_notes',mean( [dead for alive,dead in adeadtotal ] ))
def user_var_dead(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('variance_alive_notes',variance( [dead for alive,dead in adeadtotal ] ))


def user_mean_day_add(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('mean_new_notes_per_day',mean([alive for alive,dead in adeadgained ] ))
def user_var_day_add(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('var_new_notes_per_day',variance([alive for alive,dead in adeadgained ] ))
def user_mean_day_del(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('mean_del_notes_per_day',mean([dead for alive,dead in adeadgained ] ))
def user_var_day_del(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    return ca.make_feature('var_del_notes_per_day',variance([dead for alive,dead in adeadgained ] ))

def user_mean_change(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    delta = [(new - dead) for new,dead in adeadgained]
    #print [(new,dead) for new,dead in adeadgained]
    #print delta
    return ca.make_feature('mean_change', mean(delta))

def user_var_change(userid):
    global _walk_cache
    if userid not in _walk_cache:
        _walk_cache[userid] = userWalk(User.objects.filter(id=userid)[0])
    totDays,activeDays,adeadtotal,adeadgained = _walk_cache[userid]
    delta = [(new - dead) for new,dead in adeadgained]
    return ca.make_feature('var_change', variance(delta))

## Wolfe Code

#def is_user_active(user):
#    actLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-edit','note-save','note-delete', 'sidebar-open']).filter(when__gte=
