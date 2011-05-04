## Net Function for catching primitive events following a primitive event

import os,sys
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
from threading import Thread

import jv3.study.wolfe.masterPlot as MP

class EventCatcher(Thread):
    def __init__(self, user, maxTime, eventType, allowedEvents):
        Thread.__init__(self)
        self.user = user
        self.maxTime = int(maxTime)
        self.eventType = eventType
        self.allowedEvents = allowedEvents
        self.occurances = []
    def getUserID(self):
        return self.user.id
    def getLeadEvent(self):
        return self.eventType
    def getOccurances(self):
        return self.occurances
    def run(self):
        ## What you want thread to do
        self.occurances = catchNextEvent(self.user, self.maxTime, self.eventType, self.allowedEvents)

# ce.catchEventsAfter(dk, 5000, 'sidebar-open', ['note-add', 'note-edit', 'note-save', 'note-delete'])

## Get info about events in allowedEventsArr that occur within
## netTime (in msec) after each event of type eventType for a user
def catchEventsAfter(user, netTime, eventType, allowedEventsArr):
    "SLOW"
    logs = ActivityLog.objects.filter(owner=user)
    eventLogs = logs.filter(action=eventType).order_by('when')
    catchLogs = logs.filter(action__in=allowedEventsArr).order_by('when')
    if eventLogs.count() == 0:
        return -1
    numEventsWithFollowing = 0
    for eventLog in eventLogs:
        eventTime = eventLog.when
        caughtLogs = catchLogs.filter(when__gt=eventTime, when__lt=eventTime+netTime)
        cc = caughtLogs.count()
        if cc > 0:
            numEventsWithFollowing += 1
    return float(numEventsWithFollowing) / eventLogs.count()


def plotChanceNoteEventFollowsOpen(users, netTime=20000, eventType='sidebar-open', allowedEvents=['note-add','note-edit','note-save','note-delete']):
    bins = [0]*101 # a bin for each percentile (0 to 100%)
    for user in users:
        ratio = catchEventsAfter(user, netTime, eventType, allowedEvents)
        if ratio == -1:
            continue ## user had no event logs of action=eventType
        bins[int(round(100*ratio))] += 1
    MP.barPlot(bins, "t_ratio_events_follow_sidebar-open", main='Distribution: Percentage of sidebar-open events followed by note-add/edit/save/del events w/in 20 seconds',
               xl="Percent of sidebar-open followed by note-add/edit/save/del w/in 20 seconds", yl="Number of Users")
    return bins
    ##barPlot(list, filename="test_search_barplot", w=1400, h=900, names="", las=3, main="", sub="", xl="", yl="" ):



## Determine write or read sidebar-open/close sessions

def classifyUsers(users, minTimeOpen, maxTimeOpen):
    events = []
    for user in users:
        tmpEvents = classifyOpen(user, minTimeOpen, maxTimeOpen)
        if len(tmpEvents) > 50: ## An open-closer
            print "%s perc. of %s open-close events are write-events"%(
                int(100.0*sum(tmpEvents)/len(tmpEvents)),
                len(tmpEvents))
            events.append(tmpEvents)
            pass
        pass
    return events
                         
        

def classifyOpen(user, minTimeOpen, maxTimeOpen):
    events = [] ## "Write" or "Read" ?
    logs = ActivityLog.objects.filter(owner=user,
                                      action__in=['sidebar-open', 'sidebar-close',
                                                  'note-add', 'note-edit',
                                                  'note-save']).order_by('when')
    if logs.count() == 0:
        return events
    openTime = 0
    isOpen = False
    isWrite = False
    for log in logs:
        if log.when - openTime > maxTimeOpen: # Reset!
            isOpen = False
            isWrite = False
            pass
        if log.action == 'sidebar-open':
            isOpen = True
            openTime = log.when
        elif isOpen and log.action in ['note-add', 'note-edit', 'note-save']:
            isWrite = True
        elif isOpen and log.action == 'sidebar-close' and log.when - openTime > minTimeOpen:
            ## Record type of open event
            events.append(isWrite)
            isOpen = False
            isWrite = False
    ##print "%s perc. of %s open-close events are write-events"%(int(100.0*sum(events)/len(events)),                                                          len(events))
    return events



## Faster/better method!

## Catch FIRST event after
##   all events of (1+) type(s)
##   occuring within time limit
##   after a specific ONE type of event
def catchNextEvent(user, maxTime, eventType, allowedEvents):
    "Return description of each time allowedEvent followed eventType within maxTime"
    allEvents = [eventType]
    allEvents.extend(allowedEvents)
    remLogs = ActivityLog.objects.filter(owner=user, action__in=allEvents).order_by('when')
    if remLogs.count() == 0:
        return []
    occurances = []
    lastLog = False
    for log in remLogs:
        if log.action == eventType:
            lastLog = log
            continue
        if lastLog and lastLog.action == eventType and log.action in allowedEvents and lastLog.when+maxTime > log.when:
            occurances.append((log.action, int((log.when-lastLog.when)/100)/10.0) )
            lastLog = False
    return occurances

eventToNum = {'sidebar-open':1,
              'sidebar-close':2,
              'searchbar-focus':3,
              'note-add':4,
              'note-edit':5,
              'note-delete':6}


## Plot Parralel Coordinates! see plot
def plotProtoVis(users):
    items = [] #list of: {name:"buick skylark 320", mpg:15, ..., acc:11.5, year:70, origin:1}
    usersProcessed = 0
    for user in users:
        uNotes = Note.objects.filter(owner=user)
        numNotes = uNotes.count()
        openOcc = catchNextEvent(user, 1000*30, 'sidebar-open',
                                 ['search', 'note-add', 'note-edit', 'note-delete'])
        for occ in openOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum['sidebar-open'],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1]}
            items.append(item)
        searchOcc = catchNextEvent(user, 1000*30, 'search',
                                   ['note-add', 'note-edit', 'note-delete'])
        for occ in searchOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum['search'],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1]}
            items.append(item)
        usersProcessed += 1
        print usersProcessed
    jsonString = JSONEncoder().encode({'items':items})
    # Print to page: var data = JSON.parse(jsonString);
    # var items = data['items']
    testFile = open('test.js', 'w')
    testFile.writelines("var data = JSON.parse('%s');\nvar items=data['items'];"%(jsonString))
    testFile.close()
    return jsonString


def plotProtoVis2(users):
    import jv3.study.wUserWalk as uw
    items = [] #list of: {name:"buick skylark 320", mpg:15, ..., acc:11.5, year:70, origin:1}
    usersProcessed = 0
    for user in users:
        nAddVel, nAddVar, nDelVel, nDelVar = uw.analyzeUserWalk(user)
        uNotes = Note.objects.filter(owner=user)
        numNotes = uNotes.count()
        openOcc = catchNextEvent(user, 1000*30, 'sidebar-open',
                                 ['searchbar-focus', 'note-add', 'note-edit', 'note-delete'])
        for occ in openOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum['sidebar-open'],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1],
                    'nAddVel':nAddVel,
                    'nDelVel':nDelVel}
            items.append(item)
            pass
        searchOcc = catchNextEvent(user, 1000*30, 'searchbar-focus',
                                   ['note-add', 'note-edit', 'note-delete'])
        for occ in searchOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum['searchbar-focus'],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1],
                    'nAddVel':nAddVel,
                    'nDelVel':nDelVel}
            items.append(item)
            pass
        usersProcessed += 1
        print usersProcessed
    jsonString = JSONEncoder().encode({'items':items})
    # Print to page: var data = JSON.parse(jsonString);
    # var items = data['items']
    testFile = open('testVel.js', 'w')
    testFile.writelines("var data = JSON.parse('%s');\nvar items=data['items'];"%(jsonString))
    testFile.close()
    return jsonString

def plotProtoVis3(users):
    import jv3.study.wUserWalk as uw
    items = [] #list of: {name:"buick skylark 320", mpg:15, ..., acc:11.5, year:70, origin:1}
    usersProcessed = 0
    for user in users:
        #nAddVel, nAddVar, nDelVel, nDelVar = uw.analyzeUserWalk(user)
        ##aveCharPerNote, aveLinePerNote = uw.printBasicNoteStats(user)
        uNotes = Note.objects.filter(owner=user)
        numNotes = uNotes.count()
        flagEvent = 'sidebar-open'
        openOcc = catchNextEvent(user, 1000*30, flagEvent,
                                 ['searchbar-focus', 'note-add', 'note-edit', 'note-delete'])
        for occ in openOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum[flagEvent],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1]}
            items.append(item)
            pass
        
        flagEvent = 'searchbar-focus'
        searchOcc = catchNextEvent(user, 1000*30, flagEvent,
                                   ['note-add', 'note-edit', 'note-delete'])
        for occ in searchOcc:
            item = {'id':user.id, 'numNotes':numNotes,
                    'event':eventToNum[flagEvent],
                    'followingEvent':eventToNum[occ[0]],
                    'timeElapsed':occ[1]}
            items.append(item)
        usersProcessed += 1
        print usersProcessed
    jsonString = JSONEncoder().encode({'items':items})
    # Print to page: var data = JSON.parse(jsonString);
    # var items = data['items']
    testFile = open('testVel.js', 'w')
    testFile.writelines("var data = JSON.parse('%s');\nvar items=data['items'];"%(jsonString))
    testFile.close()
    return jsonString



def eventsFollowingEvent(users, eventType, followEvents, timeDelay):
    userData = {}
    for user in users:
        uid = user.id
        userData[uid] = {eventType : catchNextEvent(user, timeDelay, eventType, followEvents)}
    return userData

eventPairings = {'sidebar-open':['note-add','note-edit','note-delete','searchbar-focus'],
                 'searchbar-focus':['note-add', 'note-edit', 'note-delete']}




## Use threads to speed things up even more!
def compileEvents(users, eventPairings, timeDelay=30000):
    try:
        print "Processing %s users"%(len(users))
        procCount = 0
        threadEvents = []
        for user in users:
            for leadEvent, followEvents in eventPairings.items():
                procCount += 1
                print procCount
                ## Initialize and run thread
                caughtEvents = EventCatcher(user, timeDelay, leadEvent, followEvents)
                threadEvents.append(caughtEvents)
                caughtEvents.start()
            pass
        eventData = {}
        for leadEvent in eventPairings.keys():
            eventData[leadEvent] = {}
            for followEvent in eventPairings[leadEvent]:
                eventData[leadEvent][followEvent] = []
            pass
        for caughtEvents in threadEvents:
            caughtEvents.join()
        ## Process finished threads
            userid = caughtEvents.getUserID()
            leadEvent = caughtEvents.getLeadEvent()
            occurances = caughtEvents.getOccurances()
            for occ in occurances: ## occ[0] = following action type, occ[1] = elapsed time
                eventData[leadEvent][occ[0]].append(occ[1])
            print procCount
            procCount -= 1
            pass
        return eventData
    except KeyboardInterrupt:
        print "Exiting"
        return []


        
                                 
def getEventFlow(users, eventPairings, timeDelay=30*1000):
    eventData = {}
    for leadEvent, followEvents in eventPairings.items():
        if leadEvent not in eventData:
            eventData[leadEvent] = {}
        for followEvent in followEvents:
            if followEvent not in eventData[leadEvent]:
                eventData[leadEvent][followEvent] = []
            pass
        for user in users:
            print "%s - %s"%(leadEvent, user.id) 
            followOcc = catchNextEvent(user, timeDelay, leadEvent, followEvents)
            for occ in followOcc: # occ[1] is time in sec, occ[0] is action type of following event
                eventData[leadEvent][occ[0]].append(occ[1])
    return eventData

"""
In [1073]: len(evA['sidebar-open']['searchbar-focus'])
Out[1073]: 2284
In [1074]: len(evA['sidebar-open']['note-add'])
Out[1074]: 7285
In [1075]: len(evA['sidebar-open']['note-edit'])
Out[1075]: 5243
In [1076]: len(evA['sidebar-open']['note-delete'])
Out[1076]: 3413

In [1077]: len(evA['searchbar-focus']['note-add'])
Out[1077]: 1037
In [1078]: len(evA['searchbar-focus']['note-edit'])
Out[1078]: 971
In [1080]: len(evA['searchbar-focus']['note-delete'])
Out[1080]: 245
"""




## Count Things

def sidebarEvents(user):
    sbEvents = ActivityLog.objects.filter(owner=user, action__in=['sidebar-open', 'sidebar-close']).order_by('when')
    openDurations = [] ## list of durations that sidebar stays open
    lastOpen = False
    for log in sbEvents:
        if log.action == 'sidebar-open':
            lastOpen = log
        elif lastOpen:
            ## 'sidebar-close' event
            openDurations.append(log.when-lastOpen.when)
            lastOpen = False
    return openDurations

def openDurations(users):
    userDurations = {}
    for user in users:
        durs = sidebarEvents(user)
        userDurations[user.id] = durs
        if len(durs) == 0:
            continue
        print "%s - %s"%(len(durs), int(sum(durs)/(1000*len(durs)))/60.0)
    return userDurations


def plotSidebarDurations(users, userDurs=False):
    if not userDurs:
        userDurs = openDurations(users)
    sessionCount, sessionTime = [], []
    for durs in userDurs.values():
        if len(durs) == 0:
            continue
        sessionCount.append(len(durs))
        sessionTime.append(int(int(sum(durs))/(1000.0*len(durs))) / 60.0) ## in minutes
    MP.scatterPlot(sessionCount, sessionTime,
                   log='xy',
                   filename='sidebar_opens_logscale',
                   main="Sidebar Open->Close durations/counts",
                   xl="# Times sidebar 'Open->Close'",
                   yl="Average time sidebar open per 'open->close'")
    return userDurs
