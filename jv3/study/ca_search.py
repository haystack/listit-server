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

r = ro.r
emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
wstyke = User.objects.filter(email="wstyke@gmail.com")[0]
katfang = User.objects.filter(email="justacopy@gmail.com")[0]
karger = User.objects.filter(email="karger@mit.edu")[0]
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)
cap.set_basedir('/var/listit/www-ssl/_studyplots/')


search_cache = {}
search_query_cache = {}
all_searches = []
all_queries = []

def user_search(user,days_ago=None,nosmoothing=False):
    from jv3.study.content_analysis import activity_logs_for_user
    global search_cache
    global search_query_cache

    alogs = wuw.reduceRepeatLogsValues(activity_logs_for_user(user,None,days_ago))

    searches = []
    queries = []
    last_time = 0
    for al_i in range(len(alogs)):
        al = alogs[al_i]
        if al["action"] == 'search':
            try:
                query = JSONDecoder().decode(al["search"])
            except:
                continue
            if type(query) == dict:
                key = None
                if 'search' in query: key = 'search'
                if 'query' in query: key = 'query'
                if key is not None:
                    # no empty searches pls
                    if len(query[key].strip()) > 0 and nosmoothing or long(al['when'])-long(last_time) > (10*1000):  # 10 second smoothing
                        queries.append(query[key])
                        al['query'] = query[key]
                        searches.append(al)
                        last_time = al['when']
        elif al["action"] == 'clear-search' and nosmoothing or long(al['when'])-long(last_time) > (10*1000):
            al['query'] = ''
            searches.append(al)
            last_time = al["when"]

    search_cache[user.id] = searches
    search_query_cache[user.id] = queries

    return searches,nltk.FreqDist(queries)


## copied from wUserWalk but modified to take values() dicts instead of actual ActivityLog orms
## Returns list of [#total days, #active days, (lists of logs from diff. active dates)]
def chunkLogsByDay(logsList):
    if len(logsList) == 0: return (0, 0, [])
    logsList.sort(lambda x,y:cmp(x["when"],y["when"]))
    chunkedList = reduce(chunkLogsByDayReducer, logsList)
    ## Returns (#days between first/last act, #days active, chunkedList)
    return (chunkedList[0][1], len(chunkedList[1:]), chunkedList[1:])

## helper
def chunkLogsByDayReducer(x, y):
    dayInMS = 86400000
    if type(x) != type([]) and type(x["when"])==type(Decimal()):
        ## First value being considered
        dayOfSecondLog = math.floor((y["when"]-x["when"]) /dayInMS)
        if y["when"] - x["when"] < dayInMS:
            return [[x,dayOfSecondLog], [x,y]]
        else:
            return [[x,dayOfSecondLog],[x],[y]]
    else:
        ## First value stores time start, length of x is (1+#days)
        dayOfLog = math.floor((y["when"]-x[0][0]["when"]) / dayInMS)
        if dayOfLog > x[0][1]:
            ## The day is beyond the last logged day
            x.append([y])
            x[0][1] = dayOfLog
        else:
            ## Day is same as last logged day
            x[len(x)-1].append(y)
        return x

def chunk_searches(user):
    searches,dfreq = user_search(user)

    # weave notecaps back _in_. i know this is weird. but to help with partitioning
    #ncs = list(user.activitylog_set.filter(action='note-add').values())
    plusnotecaps = searches+[]
    plusnotecaps.sort(key=lambda x: long(x["when"]))
    tot,acti,chunked = chunkLogsByDay(plusnotecaps)
    chunked = [filter(lambda x: x["action"] in ["search","clear-search"], day) for day in chunked]
    return dfreq,tot,acti,chunked,mean([len(x) for x in chunked])

# def chunk(searches):
#     tot,acti,chunked = chunkLogsByDay(searches)
#     #print "searches chunked: ", tot,acti,chunked
#     #print mean([len(x) for x in chunked])
#     return tot,acti,chunked,mean([len(x) for x in chunked])

def find_intersecting_webpages(when,owner):
    margin = (30*1000.0)
    when = long(when)
    return set([x.values()[0] for x in owner.event_set.filter(type='www-viewed',start__lt=long(when+margin),end__gt=long(when-margin)).values('entityid')])

def get_searches(users):
    global search_cache
    global search_query_cache
    global all_searches
    global all_queries

    [user_search(user) for user in users] 

    for user in search_cache:
        for search in search_cache[user]:
            all_searches.append(search)
        for query in search_query_cache[user]:
            all_queries.append(query)

def words_per_search():
    global all_queries

    wps = [len(q.split()) for q in all_queries]

    return wps

def times_repeated():
    global search_query_cache

    tr = {}
    for user in search_query_cache:
        tr[user] = {}
        for query in search_query_cache[user]:
            if query not in tr[user]:
                tr[user][query] = 1
            else:
                tr[user][query] += 1

    return tr

def searchstats(users):
    results = {}
    totalfreq = nltk.FreqDist()
    for u in users:        
        f,t,a,c,m = chunk_searches(u)
        totalfreq = totalfreq + f 
        ws = []
        for ch in c:
            w = []
            for search in ch:
                w.extend(find_intersecting_webpages(search["when"],u))
            ws.append(w)            
        results[u.id] = {'queries':f,'tot':t,'active':a,'chunked':c,'webpage':ws,'mean':m}
    return results,totalfreq

def pr(s):
    print s,

def searchterms(users):
    totalfreq = nltk.FreqDist()
    total = 0
    
    def helper(a):
        if a.get("noteText",None) is not None:
            return a.get("noteText")
        if a.get('search',None) is not None and not a.get('search').find('{') == 0:
            return a.get("search")
    def getQuery(a):
        b = helper(a)
        if b is not None:  return b.lower().strip()
    
    for u in users:        
        zoo = wuw.reduceRepeatLogsValues2(u.activitylog_set.filter(action='search').values())
        total = total + len([z['noteText'].lower().strip() for z in zoo if z.get('noteText',None) is not None])
        totalfreq = totalfreq + nltk.FreqDist([z['noteText'].lower().strip() for z in zoo if z.get('noteText',None) is not None])

    return totalfreq,[ z['when']  for z in zoo ]
    
def get_search_hits(users):
    us = {}
    for u in users:
        usearches = []
        zoo = wuw.reduceRepeatLogsValues2(u.activitylog_set.filter(action='search').values())
        for z in zoo:
            s = z.get("search",'')
            if s is None or len(s.strip()) == 0: continue
            try:
                usearches.append(json.loads(s)["hits"])
            except:
                import sys
                print sys.exc_info()
        if len(usearches) > 0:
            us[u.id] = usearches
    return us

def times_search_used(users):
    times = []
    for u in users:
        if u.activitylog_set.filter(action='search').count() == 0: continue
        times.append(len(wuw.reduceRepeatLogsValues2(u.activitylog_set.filter(action='search').values())))
    return times

def percent_notes_retrieved(gsh):
    return dict([(uid,len(set(reduce(lambda x,y:x+y,v,[])))/(1.0*User.objects.filter(id=uid)[0].note_owner.count())) for uid,v in gsh.iteritems() if User.objects.filter(id=uid)[0].note_owner.count() > 0])

def freq_notes_retrieved(gsh):
    return dict([(uid,nltk.FreqDist(reduce(lambda x,y:x+y,v,[]))) for uid,v in gsh.iteritems() if User.objects.filter(id=uid)[0].note_owner.count() > 0])

def median_times_a_note_was_retrieved(gsh):
    boo = [(u,safemedian(nltk.FreqDist(reduce(lambda x,y:x+y, [s for s in p])).values())) for u,p in gsh.iteritems()]
    return dict( [(x,y) for x,y in boo if y is not None])

def correlate_note_search_with_num_notes_created(users):
    rsize = r.c()
    rsearch = r.c()
    for u in users:
        zoo = wuw.reduceRepeatLogsValues2(u.activitylog_set.filter(action='search').values())
        rsize = r.c(rsize, u.note_owner.count())
        rsearch = r.c(rsearch, len(zoo) )
    return rsize,rsearch,r('cor.test')(notes,searches)

def correlate_note_search_with_mean_alive(users):
    rsize = r.c()
    rsearch = r.c()
    for u in users:
        print u
        zoo = wuw.reduceRepeatLogsValues2(list(u.activitylog_set.filter(action='search').values()))
        if len(zoo) == 0: print "warning zero"
        if u.activitylog_set.count() == 0: continue
        try:
            rsize = r.c(rsize, wuw.user_mean_alive(u.id).values()[0])
            rsearch = r.c(rsearch, len(zoo) )
        except:
            print sys.exc_info()
    return rsize,rsearch,r('cor.test')(notes,searches)




