
from jv3.models import *
import jv3.study.wUserWalk as wuw
from django.utils.simplejson import JSONDecoder
import nltk
import jv3.study.content_analysis as ca
from decimal import Decimal
import math
from jv3.study.content_analysis import mean
import jv3.study.wUserWalk as wuw

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
    for u in users:        
        zoo = wuw.reduceRepeatLogsValues2(u.activitylog_set.filter(action='search').values())        
        totalfreq = totalfreq + nltk.FreqDist([z['noteText'].lower().strip() for z in zoo if z.get('noteText',None) is not None])
    return totalfreq,[ z['when']  for z in zoo ]
    
