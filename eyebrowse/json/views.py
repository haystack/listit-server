import re,sys,time,operator,os,math,datetime,random
from datetime import date
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf.urls.defaults import *
from eyebrowse.models import *
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from os.path import splitext
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder
from django.db.models import Sum
from django.db.models import query
from django.db.models.query import QuerySet
from jv3.utils import json_response
import urlparse
# beaker
from eyebrowse.beakercache import cache
from datetime import timedelta

class EVENT_SELECTORS:
    class Page:
        @staticmethod
        def access(queryset):
            return [s[0] for s in queryset.values_list('url')]
        @staticmethod
        def filter_queryset(queryset,url):
            return queryset.filter(url=url)
    class Host:
        @staticmethod
        def access(queryset):
            return [s[0] for s in queryset.values_list('host')] 
        @staticmethod
        def filter_queryset(queryset,host):
            return queryset.filter(host=host)
        
def get_enduser_for_user(user):
    if EndUser.objects.filter(user=user).count() > 0:
        enduser = EndUser.objects.filter(user=user)[0]
    else:
        raise Http404('Internal error. Call brennan or emax. Something is wrong. Houston.')    
    return enduser

def _mimic_entity_schema_from_url(url):
    import urlparse
    prot, host, page, foo, bar, baz = urlparse.urlparse(url)
    return {"id":url, "host":host, "path": page, "type":"schemas.Webpage"}

def _unpack_from_to_msec(request):
    return (request.GET.get('from',0), request.GET.get('to',long(time.mktime(time.localtime())*1000)))

def _get_top_hosts_n(users,start,end):
    time_per_host = _get_time_per_page(users,start,end,grouped_by=EVENT_SELECTORS.Host) 

    ordered_visits = [h for h in time_per_host.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    return ordered_visits    

def _get_top_pages_n(users,start,end):
    time_per_page = _get_time_per_page(users,start,end,grouped_by=EVENT_SELECTORS.Page) 

    ordered_visits = [h for h in time_per_page.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    return ordered_visits    

def _h_generator(domain):
    domain = domain.lower().strip()
    summ = sum([ ord(char) for char in domain ])
    denom = 1  # in case you want to play.
    ratio = summ/denom 
    return ratio % 360

def _get_graph_points_for_results(results, to_msec, from_msec, n):
    to_msec = int(to_msec)
    from_msec = int(from_msec)
    n = int(n)

    interp = (to_msec - from_msec) / n
    counts = int(math.floor((to_msec - from_msec) / interp))
    ttData = [0]*(counts + 1) # total time spent per time block
    avgDataNum = [0]*(counts + 1) # number of websites per time block
    def get_date_array():
        foo = [0]*(counts + 1)
        for count in range(0, counts):
            foo[count] = from_msec + (interp * count)
        return foo
    dateArray = get_date_array()

    # gets total time on websites per time block(count)
    for result in results:
        for count in range(0, counts):
            if count >= counts:
                if result.startTime > dateArray[count]:
                    ttData[count] += int(result.endTime - result.startTime)
                    avgDataNum[count] += 1
                else:
                    pass
            else:
                if result.startTime > dateArray[count] and result.startTime < dateArray[count + 1]:
                    ttData[count] += int(result.endTime - result.startTime)
                    avgDataNum[count] += 1
                else:
                    pass
                    
    def get_avg_data():
        foo = [0]*counts
        for count in range(0, counts): 
            foo[count] = ttData[count] / (avgDataNum[count] + 1)
        return foo
    avgData = get_avg_data()

    return { "avgTime": avgData, "totalTime": ttData }



def index_of(what, where):
    try:
        return [ h[0] for h in where ].index(what)
    except:
        pass
    return None

def index_of_url(what, where):
    try:
        return [ h['url'] for h in where ].index(what)
    except:
        pass
    return None


def get_title_from_evt(evt):
    foo =  JSONDecoder().decode(JSONDecoder().decode(evt.entitydata)[0]['data'])
    if foo.has_key('title'):
        return foo['title']
    return   

def round_time_to_day(time):
    new_time = int(math.floor(int(time) / 86400000) * 86400000)
    return new_time        

def round_time_to_half_day(time):
    new_time = int(math.floor(int(time) / 43200000) * 43200000)
    return new_time        

def round_time_to_hour(time):
    new_time = int(math.floor(int(time) / 3600000) * 3600000)
    return new_time        

def _get_time_per_page(user,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Page):
    if type(user) == QuerySet:
        mine_events = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec)
    elif type(user) == list:
        mine_events = PageView.objects.filter(user__in=user,startTime__gte=from_msec,endTime__lte=to_msec)
    else:
        mine_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        
    uniq_urls  = set( grouped_by.access(mine_events) )
    times_per_url = {}
    for url in uniq_urls: #might be faster to annotate rather than do this
        # might be faster to define a variable here rather than doing filter 2x for the if and the reduce
        grouped_by_filtered = grouped_by.filter_queryset(mine_events,url).values_list('startTime','endTime')
        # to make sure not to reduce an empty item 
        if grouped_by_filtered:
            times_per_url[url] = long(reduce(lambda x,y: x+y, [ startend[1]-startend[0] for startend in grouped_by_filtered ] ))
        else:
            pass
    return times_per_url

def _get_visits_per_pageview(pageviews):            
    ## this function takes FOREVER
    visits_per_view = {} 
    for view in pageviews:
        visits_per_view[view.url] = visits_per_view.get(view.url,0) + 1
    return visits_per_view        

# attempts at making this faster
  #  results =  dict((v.url, results.get(view.url,0) + 1) for v in pageviews)
  #  return [(visits_per_view.get(view.url,0) + 1) for view in pageviews]


def _get_pageviews_ordered_by_count(pageviews):
    visits_per_pageview = _get_visits_per_pageview(pageviews) 
    
    ordered_visits = [h for h in visits_per_pageview.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    
    results = [PageView.objects.filter(url=visit[0]).values()[0] for visit in ordered_visits]
    ## Page.objects.filter(url__in=[visit[0] for visit in ordered_visits[:20]]).values()
    return results

def sort_by_counts(count_dict):
    l = count_dict.items()
    l.sort(key=lambda x: -x[1])
    return l

def defang_pageview(pview):    
    return {
        "start" : long(pview["startTime"]), 
        "end" : long(pview["endTime"]), 
        "url" : pview["url"], 
        "host": pview["host"], 
        "title": pview["title"], 
        "id":pview["id"], 
        "hue": _h_generator(pview["host"]) } 
    ## too slow "location":get_enduser_for_user(pview.user).location }

# if you need username
def defang_pageview_values(pview):    
    return {
        "start" : long(pview["startTime"]), 
        "end" : long(pview["endTime"]), 
        "url" : pview["url"], 
        "host": pview["host"], 
        "title": pview["title"], 
        "id":pview["id"],
        "user": User.objects.filter(id=pview["user_id"])[0].username, 
        "hue": _h_generator(pview["host"]) } 


## emax added this to be fancy
def uniq(lst,key=lambda x: x,n=None):
    result = []
    keys = []
    for ii in range(len(lst)):
        xi = lst[ii]
        ki = key(xi)
        if ki not in keys:
            keys.append(ki)
            result.append(xi)
        if n is not None and len(result) >= n:
            return result    
    return result        

def get_views_user(from_msec, to_msec, username):
    user = get_object_or_404(User, username=username)

    hits = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).values()
    return [ defang_pageview(evt) for evt in hits ]    

## get most recent urls now returns elements with distinct titles. no repeats!
def get_latest_views(request):
    if not 'username' in request.GET:
        return json_response({ "code":404, "error": "get has no 'username' key" }) 

    n = int(request.GET['num'])

    req_type = request.GET['type']

    @cache.region('ticker')
    def fetch_data(req_type):
        if 'user' in req_type:
            user = get_object_or_404(User, username=request.GET['username'])
            phits = PageView.objects.filter(user=user).order_by("-startTime")[0:n].values()
        elif 'friends' in req_type:
            usr = get_object_or_404(User, username=request.GET['username'])
            users = [friendship.to_friend for friendship in usr.friend_set.all()]
            phits = PageView.objects.filter(user__in=users).order_by("-startTime")[0:n].values()
        else:
            phits = PageView.objects.filter().order_by("-startTime")[0:n].values() #global

        uphit = uniq(phits,lambda x:x["url"],n)
        return [ defang_pageview_values(evt) for evt in uphit ]

    results = fetch_data(req_type)

    if request.GET.has_key('id'):
        urlID = int(request.GET['id'])
        filter_results = []
        for result in results:
            if int(result['id']) > urlID:
                filter_results.append(result)
        if len(filter_results) > 0:
            return json_response({ "code":200, "results": filter_results })
        else:
            return json_response({ "code":204 })

    return json_response({ "code":200, "results": results })


def get_profile_queries(req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    @cache.region('long_term')
    def fetch_data(users):
        number = 0
        totalTime = 0
        try: 
            if type(users) == QuerySet:
                number += PageView.objects.filter().count()
                totalTime += int(PageView.objects.filter().aggregate(Sum('duration'))['duration__sum'])
            elif type(users) == list:
                number += PageView.objects.filter(user__in=users).count()
                totalTime += int(PageView.objects.filter(user__in=users).aggregate(Sum('duration'))['duration__sum'])
            else:
                number += PageView.objects.filter(user=users).count()
                totalTime += int(PageView.objects.filter(user=users).aggregate(Sum('duration'))['duration__sum'])
        except:
            pass
        if number > 0:
            average = int(totalTime/1000)/int(number)
            return { 'number': number, 'totalTime': totalTime/1000, 'average': average }
        return { 'number': 0, 'totalTime': 0, 'average': 0 }

    results = fetch_data(users)
    return results


def get_page_profile_queries(url, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()] # list
    else:
        users = User.objects.all() # queryset

    @cache.region('long_term')
    def fetch_data(inputURL, users, gaak):
        number = 0
        totalTime = 0
        try: 
            if type(users) == QuerySet:
                number += PageView.objects.filter(url=inputURL).count()
                totalTime += int(PageView.objects.filter(url=inputURL).aggregate(Sum('duration'))['duration__sum'])
            elif type(users) == list:
                number += PageView.objects.filter(user__in=users, url=inputURL).count()
                totalTime += int(PageView.objects.filter(user__in=users, url=inputURL).aggregate(Sum('duration'))['duration__sum'])
            else:
                number += PageView.objects.filter(user=users, url=inputURL).count()
                totalTime += int(PageView.objects.filter(user=users, url=inputURL).aggregate(Sum('duration'))['duration__sum'])
        except:
            pass

        if number > 0:
            average = int((totalTime/1000)/number)
            return { 'number': number, 'totalTime': totalTime/1000, 'average': average }
        return { 'number': 0, 'totalTime': 0, 'average': 0 }

    results = fetch_data(url, users, "page_profile_queries")
    return results


def get_most_shared_hosts(request, n):
    n = int(n)

    @cache.region('very_long_term')
    def fetch_data(n, fetch_type):
        results = {}
        users = User.objects.all()
        for user in users:
            try:
                for url in PrivacySettings.objects.filter(user=user)[0].whitelist.split():
                    if url in results:
                        results[url] += 1
                    else:
                        results[url] = 1
            except:
                pass
        return sorted(results.items(), key=lambda (k,v): (-v,k))[0:n]

    results = fetch_data(n, "shared_urls")
    return json_response({ "code":200, "results": results }) 

    
def get_top_hosts_compare(end_time, interp, n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)

    second_end = end_time
    second_start = end_time - interp
    first_end = second_start
    first_start = second_start - interp

    @cache.region('long_term')
    def fetch_data(users, hosts):
        times_per_url_first = _get_top_hosts_n(users,first_start,first_end) # can pass multiple or single users
        times_per_url_second = _get_top_hosts_n(users,second_start,second_end)
        
        results = []

        # if the first list is longer than the second list
        # this throws a  ValueError('list.index(x): x not in list',)
        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
            old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference
                results.append( times_per_url_second[i] + (diff,) )
            else:
                results.append( times_per_url_second[i] )

        return results[0:n]

    results = fetch_data(users, 'top_hosts')
    return results


def top_and_trending_pages(users, req_type, first_start, first_end, second_start, second_end):
    n = 17
    @cache.region('long_term')
    def fetch_data(users, pages):
        times_per_url_first = _get_top_pages_n(users,first_start,first_end)
        times_per_url_second = _get_top_pages_n(users,second_start,second_end)
        
        results = []

        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
                old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
                if old_rank is not None:
                    diff = - (i - old_rank)  # we want the gain not the difference
                    results.append( times_per_url_second[i] + (diff,) )
                else:
                    results.append( times_per_url_second[i] + (0,) )
                    
        top_pages = results[0:n]
        results.sort(key=lambda x: -x[2])

        trending = results[0:n]        

        tre_titles = []
        for result in trending:
            try:
                tre_titles.append(PageView.objects.filter(url=result[0])[0].title)
            except:
                tre_titles.append("")

        top_titles = []
        for result in top_pages:
            try:
                top_titles.append(PageView.objects.filter(url=result[0])[0].title)
            except:
                top_titles.append("")

        return {"top":top_pages, "trending":trending, "tre_titles":tre_titles, "top_titles":top_titles}

    results = fetch_data(users, 'top_and_trending_pages')
    return results;


def get_top_and_trending_pages(end_time, interp, n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)

    second_end = end_time
    second_start = end_time - interp
    first_end = second_start
    first_start = second_start - interp

    results = top_and_trending_pages(users, 'top_and_trending_pages', first_start, first_end, second_start, second_end)
    return results


def get_JSON_top_and_trending_pages(request):
    if not 'username' in request.GET:
        return json_response({ "code":404, "error": "get has no 'username' key" }) 
    
    username = request.GET['username'].strip()
    
    end_time = int(time.time()*1000)
    interp = int(86400*1000/2) # 12 hours
    
    req_type = {}
    if request.GET['type'].strip() == 'user':
        req_type['user'] = username
    elif request.GET['type'].strip() == 'friends':
        req_type['friends'] = username
    else:
        req_type['global'] = 'global'

    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()
        
    n = int(17)

    second_end = end_time
    second_start = end_time - interp
    first_end = second_start
    first_start = second_start - interp

    results = top_and_trending_pages(users, req_type, first_start, first_end, second_start, second_end)
    return json_response({ "code":200, "results": results });


def get_JSON_eyebrowse_social_page(request):
    if not 'username' in request.GET:
        return json_response({ "code":404, "error": "get has no 'username' key" }) 
    
    username = request.GET['username'].strip()
    num = request.GET['len'].strip()
    
    end_msec = int(time.time()*1000)
    interp = int(86400*1000/2) # 12 hours

    @cache.region('long_term')
    def fetch_data(username, pages):
        req_type = {}
        request_type = {}

        req_type['friends'] = username

        personalCache = get_top_and_trending_pages(int(end_msec), interp, 16, req_type)
        personal = personalCache['trending']        
        personal_titles = personalCache['tre_titles'] #[0:num]       

        request_type['global'] = 'global'

        trendingCache = get_top_and_trending_pages(int(end_msec), interp, 16, request_type)
        trending = trendingCache['trending']  #[0:num]        
        tre_titles = trendingCache['tre_titles'] #[0:num]       

        return {"personal":personal, "trending":trending, "tre_titles":tre_titles, "personal_titles":personal_titles}

    results = fetch_data(username, 'eyebrowse_social_page')
    return json_response({ "code":200, "results": results });


def get_profile_graphs(endTime, interp, username):    
    user = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, baaa):
        from_msec = round_time_to_half_day(endTime - interp)
        to_msec = round_time_to_half_day(endTime)        

        views = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        data = {}

        weekPts = [0]*7
        hrPts = [0]*24

        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            # returns the day of the week as an integer, where Monday is 0 and Sunday is 6. 
            weekPts[weekday] += 1

            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            hrPts[hour] += 1

        data.update(_get_graph_points_for_results(views, to_msec, from_msec, 28))

        data['dayWeek'] = weekPts
        data['timeDay'] = hrPts
        return data

    results = fetch_data(user, "profile_graphs") 
    return results


def get_pagestats_graphs(endTime, interp, url, req_type):    
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    @cache.region('long_term')
    def fetch_data(url, users, bar):
        from_msec = round_time_to_half_day(endTime - interp)
        to_msec = round_time_to_half_day(endTime)

        if type(users) == QuerySet:
            views = PageView.objects.filter(url=url,startTime__gte=from_msec,endTime__lte=to_msec)
        elif type(users) == list:
            views = PageView.objects.filter(user__in=users, url=url,startTime__gte=from_msec,endTime__lte=to_msec)
        else:
            views = PageView.objects.filter(user=users,url=url,startTime__gte=from_msec,endTime__lte=to_msec)

        data = {}

        weekPts = [0]*7
        hrPts = [0]*24

        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            # returns the day of the week as an integer, where Monday is 0 and Sunday is 6. 
            weekPts[weekday] += 1

            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            hrPts[hour] += 1

        data.update(_get_graph_points_for_results(views, int(to_msec), int(from_msec), int(28)))

        data['dayWeek'] = weekPts
        data['timeDay'] = hrPts
        return data

    results = fetch_data(url, users, "pagestats_graphs") 
    return results


def get_mini_line_graph(from_msec_raw, to_msec_raw, num, req_type):    
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    from_msec_rounded = round_time_to_hour(from_msec_raw)
    to_msec_rounded = round_time_to_hour(to_msec_raw)

    @cache.region('long_term')
    def fetch_data(users, from_msec, to_msec, num):
        if type(users) == QuerySet:
            views = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec)
        elif type(users) == list:
            views = PageView.objects.filter(user__in=users,startTime__gte=from_msec,endTime__lte=to_msec)
        else:
            views = PageView.objects.filter(user=users,startTime__gte=from_msec,endTime__lte=to_msec)

        return _get_graph_points_for_results(views, to_msec, from_msec, num)

    results = fetch_data(users, from_msec_rounded, to_msec_rounded, num) 
    return results


def get_dot_graph(n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)
    @cache.region('long_term')
    def fetch_data(users, barbar):
        if type(users) == QuerySet:
            views = PageView.objects.all().order_by("-startTime")[0:n]
        elif type(users) == list:
            views = PageView.objects.filter(user__in=users).order_by("-startTime")[0:n]
        else:
            views = PageView.objects.filter(user=users).order_by("-startTime")[0:n]

        dots = {}
        for view in views:
             dots[int(view.id)] = {"url":view.url, "hue": _h_generator(view.host), "title": view.title}

        l = dots.items()
        #l.sort(key=lambda x: x[1])
        return l

    results = fetch_data(users, "dot_graph") 
    return results

# NEEDS FIXIN TODO
def get_top_users(interp, n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)

    @cache.region('very_long_term')
    def fetch_data(interp, req_type, bozon):
        to_msec = int(time.time()*1000)
        from_msec = to_msec - interp

        results = []

        if type(users) == QuerySet or type(users) == list:
            for user in users:
                try:
                    results.append( {"user": user.username, "number": PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).count() } )
                except:
                    pass
        else:
            results.append( {"user": users.username, "number": PageView.objects.filter(user=users,startTime__gte=from_msec,endTime__lte=to_msec).count() } )

        results.sort(key=lambda x:-x["number"])
        return results[0:n]
        
    return fetch_data(interp, req_type, "top_users")

# NEEDS FIXIN TODO
def get_top_users_for_url(n, url, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()] # list
    else:
        users = User.objects.all() # queryset

    n = int(n)

    @cache.region('very_long_term')
    def fetch_data(req_type, url, barbar):
        to_msec = int(time.time()*1000)
        from_msec = to_msec - (18122400000) # past three weeks

        results = []

        try:
            for user in users:
                try:
                    number = PageView.objects.filter(user=user,url=url,startTime__gte=from_msec,endTime__lte=to_msec).count()
                    results.append( {"user": user.username, "number": number } )
                except:
                    pass

            results.sort(key=lambda x: -x["number"])
            
            return results[0:n]
        except:
            return results

    return_results = fetch_data(req_type, url, "top_users_url")
    return return_results

# NOT USED YET
def get_percent_logging(url_raw, req_type):
    if 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()] # list
    else:
        users = User.objects.all() # queryset

    scheme, url_parsed, boo, foo, bar, baz = urlparse.urlparse(url_raw)

    @cache.region('long_term')
    def fetch_data(url, users, gack):
        results = []
        
        if (users) == list:
            return PrivacySettings.objects.filter(user__in=users, whitelist__in=url).count()/User.objects.all().count()
        else:
            return PrivacySettings.objects.filter(whitelist__in=url).count()/User.objects.all().count()

    return_results = fetch_data(url_parsed, users, "percent_logging")
    return return_results

        
def get_closest_url(request):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    url = request.GET['url']
    ## finds the urls that best match the given url. if there
    ## is an exact match, only returns that.
    if PageView.objects.filter(url=url).count() > 0:
        return json_response({ "code":200, "results": [url] });
    
    hits = list(set([ url['url'] for url in PageView.objects.filter(url__contains=url).values('url') ]))
    hits.sort( lambda x,y: len(x)-len(y) )
    return json_response({ "code":200, "results": hits });


def to_from_url(url, users, req_type):
    @cache.region('very_long_term')
    def fetch_data(url, users, req_type):
        to_msec = int(time.time()*1000)
        from_msec = to_msec - (18122400000) # past three weeks

        if type(users) == QuerySet:
            accesses = PageView.objects.filter(url=url, startTime__gte=from_msec,endTime__lte=to_msec)
        elif type(users) == list:
            accesses = PageView.objects.filter(user__in=users, url=url, startTime__gte=from_msec,endTime__lte=to_msec)
        else:
            accesses = PageView.objects.filter(user=users, url=url, startTime__gte=from_msec,endTime__lte=to_msec)

        pre = {}
        next = {}
        titles = {}
        for access in accesses:
            # get the page we logged IMMEDIATELY before access for the particular access's user in question
            prev_access = PageView.objects.filter(startTime__lt=access.startTime,user=access.user).order_by("-startTime")[0]
            if prev_access.url != url:
                pre[prev_access.url] = pre.get(prev_access.url,0) + 1
                if prev_access.title is not None:
                    titles[prev_access.url] = prev_access.title
                else:
                    titles[prev_access.url] = prev_access.url
            else:
                pass
            # get the page we logged IMMEDIATELY before access for the particular access's user in question
            next_access = PageView.objects.filter(startTime__gt=access.startTime,user=access.user).order_by("startTime")[0]
            if next_access.url != url:
                next[next_access.url] = next.get(next_access.url,0) + 1
                if next_access.title is not None:
                    titles[next_access.url] = next_access.title
                else:
                    titles[next_access.url] = next_access.url
            else:
                pass
                    
        pre_sorted = sort_by_counts(pre)[:7]
        next_sorted = sort_by_counts(next)[:7]

        return { 'pre':pre_sorted, 'next':next_sorted, 'pre_titles': [ titles[x[0]] for x in pre_sorted ] , 'next_titles' : [ titles[x[0]] for x in next_sorted ] }
    return fetch_data(url, users, req_type)


def get_to_from_url(n, url, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()
    
    # check if url exists in the logs
    if  len(PageView.objects.filter(url=url)) < 1:
        # fail silently 
        return {'pre':"", 'next':"", 'pre_titles': "" , 'next_titles' : "" }

    return_results = to_from_url(url, users, req_type)
    return return_results


## INDEX PAGE
def get_homepage(request):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" }) 

    from_msec,to_msec = _unpack_from_to_msec(request)

    request_type = {'global':'all'}

    # this should help if the homepage gets hit really hard
    @cache.region('ticker')
    def fetch_data(baaa):
        top_users = get_top_users(int(int(to_msec) - int(from_msec)), 10, request_type)    
## TODO FIGURE OUT A BETTER WAY to get top user   
        views_user = get_views_user(from_msec, to_msec, top_users[0]['user']) 
        return ["", views_user]

    results = fetch_data("get_homepage")
    return json_response({ "code":200, "results": results });


## TICKER PAGE
#date_now = lambda : datetime.datetime.ctime(datetime.datetime.now())
def get_ticker(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    request_type = {}
    if request.GET['type'].strip() == 'user':
        request_type['user'] = request.user.username
    elif request.GET['type'].strip() == 'friends':
        request_type['friends'] = request.user.username
    else:
        request_type['global'] = 'global'

    # not sure if caching this is necissary at all but it might help
    @cache.region('short_term')
    def fetch_data(bar, boz):  
        from_msec,to_msec = _unpack_from_to_msec(request)
        interp = int(to_msec) - int(from_msec)

        top_users = get_top_users(interp, 10, request_type)
        top_trending = get_top_and_trending_pages(int(to_msec), interp, 16, request_type)
        profile_queries = get_profile_queries(request_type)
        return [top_users, top_trending, profile_queries]

    results = fetch_data("ticker_page", request_type)
    return json_response({ "code":200, "results": results });


## USERS PAGE
def get_users_page(request):
    if not 'interp' in request.GET:
        return json_response({ "code":404, "error": "get has no 'interp' key" }) 
    
    request_type = {'global':'all'}

    interp = int(request.GET['interp'].strip())

    top_users = get_top_users(interp, 10, request_type)
    profile_queries = get_profile_queries(request_type)

    return json_response({ "code":200, "results": [top_users, profile_queries] });


## PROFILE PAGE
def get_profile(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    request_type = {}
    request_type['user'] = request.GET['type'].strip()

    @cache.region('long_term')
    def fetch_data(request_type, bozz):
        now = int(time.time()*1000)
        interp = 604800000

        top_hosts = get_top_hosts_compare(now, interp, 10, request_type)
        profile_queries = get_profile_queries(request_type)
        graphs = get_profile_graphs(now, interp, request_type['user'])
        return [graphs, top_hosts, profile_queries]

    results = fetch_data(request_type, "profile_page")

    return json_response({ "code":200, "results": results });


## PAGE STATS PAGE
def get_pagestats(request):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    request_type = {}
    if request.GET['type'].strip() == 'user':
        request_type['user'] = request.user.username
    elif request.GET['type'].strip() == 'friends':
        request_type['friends'] = request.user.username
    else:
        request_type['global'] = 'global'

    url = request.GET['url'].strip()

    # not sure if caching this is necissary at all but it might help
    @cache.region('short_term')
    def fetch_data(boom, request_type, url):
        now = int(time.time()*1000)
        interp = 604800000*3 # 3 weeks
    
        percent_logging = get_percent_logging(url, request_type)
        profile_queries = get_page_profile_queries(url, request_type)
        top_users = get_top_users_for_url(10, url, request_type)
        graphs = get_pagestats_graphs(now, interp, url, request_type)
        to_from_url = get_to_from_url(7, url, request_type)
        return [graphs, top_users, profile_queries, to_from_url, percent_logging]

    results = fetch_data("pagestats", request_type, url)
    return json_response({ "code":200, "results": results });

## GRAPHS PAGE
def get_views_user_json(request, username):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" })

    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)

    ## again this is only to help in emergency and is probably unnecissary
    @cache.region('short_term')
    def fetch_data(from_msec, to_msec, user):
	hits = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).values()
	return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_raw, to_msec_raw, user)

    return json_response({ "code":200, "results": results });


def get_hourly_daily_top_urls_user(request, username, n):
    n = 20 #int(n)
    inputUser = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, n):
        to_msec = int(time.time()*1000)
        from_msec = to_msec - (18122400000) # past three weeks

        views = PageView.objects.filter(user=user, startTime__gte=from_msec,endTime__lte=to_msec)

        hrPts = dict([ (i, {}) for i in range(0,24) ])
        weekPts = dict([ (i, {}) for i in range(0,7) ])

        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            
            if view.url in hrPts[hour]:
                hrPts[hour][view.url]['val'] += 1
            else:
                hrPts[hour][view.url] = {}
                hrPts[hour][view.url]['val'] = 1
                hrPts[hour][view.url]['hue'] = _h_generator(view.host) 

            if view.url in weekPts[weekday]:
                weekPts[weekday][view.url]['val'] += 1
            else:
                weekPts[weekday][view.url] = {}
                weekPts[weekday][view.url]['val'] = 1
                weekPts[weekday][view.url]['hue'] = _h_generator(view.host) 

        lResult = []

        for x in range(7):
            phlat = weekPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2['val'])
            lResult.append((x,phlat[:n]))

        rResult = []
        for x in range(24):
            phlat = hrPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2['val'])
            rResult.append((x,phlat[:n]))

        return [lResult,rResult]
    return_results = fetch_data(inputUser, n)
        
    return json_response({ "code":200, "results": return_results }) 

## PULSE PAGE
def get_pulse_json(request_type, from_msec, to_msec):
    @cache.region('long_term')
    def fetch_data(bar, cache):    
        interp = int(to_msec) - int(from_msec)

        profile_queries = get_profile_queries(request_type)
        line_graph = get_mini_line_graph(from_msec, to_msec, 100, request_type)

        top_hosts = get_top_hosts_compare(int(to_msec), interp, 16, request_type)
        top_trending = get_top_and_trending_pages(int(to_msec), interp, 16, request_type)
        return [profile_queries, [], line_graph, top_trending, top_hosts]  # random array at 1 is from old version
        
    results = fetch_data("pulse", request_type)
    return results


def get_pulse(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    from_msec,to_msec = _unpack_from_to_msec(request)

    request_type = {}
    if request.GET['type'].strip() == 'user':
        request_type['user'] = request.user.username
    elif request.GET['type'].strip() == 'friends':
        request_type['friends'] = request.user.username
    else:
        request_type['global'] = 'global'

    results = get_pulse_json(request_type, from_msec, to_msec)

    return json_response({ "code":200, "results": results });


## PLUGIN
def get_plugin_stats(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    from_msec,to_msec = _unpack_from_to_msec(request)

    request_type = {}
    if request.GET['type'].strip() == 'user':
        request_type['user'] = request.user.username
    elif request.GET['type'].strip() == 'friends':
        request_type['friends'] = request.user.username
    else:
        request_type['global'] = 'global'

    results = get_pulse_json(request_type, from_msec, to_msec)

    num = 3500 
    results.append(get_dot_graph(num, request_type))

    return json_response({ "code":200, "results": results });

def get_top_friend_and_number_friends_for_url(request, username):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    user = get_object_or_404(User, username=username)
    get_url = request.GET['url'].strip()

    @cache.region('very_long_term')
    def fetch_data(url, user, bar):
        friends = [friendship.to_friend for friendship in user.friend_set.all()]
        results = []
        num_friends = 0
        top_friend = [{"user":"", "number":0}]
        for friend in friends:
            number = PageView.objects.filter(user=friend,url=url).count()
            results.append( {"user": friend.username, "number": number } )
            if number > 0:
                num_friends += 1

        try:
            top_friend = sorted(results, key=lambda x: -x["number"])[0]
        except:
            pass
        return {'top_friend':top_friend,'num_friends':num_friends}

    return_results = fetch_data(get_url, user, 'get_to_friend_and_number_friends_for_url')
    return return_results


# EYEBROWSER
def _get_query_for_request(request):
    query = "EndUser.objects.filter("

    group = request.GET['groups']  # string that corresponds to a tag
    country = request.GET['country'] #**string that corresponds to a country value
    friends = request.GET['friends'] #a string "friends" or "everyone"
    gender = request.GET['gender'] # a string "male"
    age = request.GET['age'] # a tuple with 2 ages [20,24]
    time = request.GET['time']  # either recently or over all time
    
    if gender != "all":
        query += " gender=gender,"
        
    if country != "any":
        query += " location=country,"
        
    if group != "any":
        query += " tags__name__contains=group,"
            
    if age != "all":
        current = [ date.today().year, date.today().month, date.today().day ]  ## year month day
        start_date = datetime.date(current[0] - eval(age)[1], current[1], current[2])
        end_date = datetime.date(current[0] - eval(age)[0], current[1], current[2])
        query += " birthdate__range=(start_date, end_date), "

    query.strip(',')  ## remove the comma at the end
    return query


def get_latest_sites_for_filter(request):
    n = 20
    query = _get_query_for_request(request)
    friends = request.GET['friends'] # a string "friends" or "everyone"
    seen = request.GET['seen'] # 0 for all 1 for has seen
    group = request.GET['groups']  # string that corresponds to a tag

    endusers = eval(query + ").values_list('user_id')") 
    
    if friends is "my friends":
        user = User.objects.filter(username=request.user.username)
        friends = [friendship.to_friend for friendship in user.friend_set.all()] 
        endusers = [friend.id for friend in friends if endusers.index(friend.id) ] 
        # is there a more effecient way of finding overlap between 2 arrays?

    # always recently
    phits = PageView.objects.filter(user__in=User.objects.filter(id__in=endusers), startTime__gt=int(time.time() * 1000) - 86400000).order_by("-startTime")[0:n].values() 
                
    uphit = uniq(phits,lambda x:x["url"],n)
    results = [ defang_pageview_values(evt) for evt in uphit ]

    # filter out seen sites
    if request.user.username and seen == "sites not seen":
        user = User.objects.filter(username=request.user.username)

        user_uniq = uniq(PageView.objects.filter(user=user).values(),lambda x:x["url"],None)
        results = [site for site in results if not user_uniq[site["url"]]] # not tested  -- maybe user_uniq[site] ??

    if request.GET.has_key('id'):
        urlID = int(request.GET['id'])
        filter_results = [site for site in results if int(site['id']) > urlID]
        if len(filter_results) > 0:
            return json_response({ "code":200, "results": filter_results })
        else:
            return json_response({ "code":204 })

    return json_response({ "code":200, "results": results })


def defang_enduser(enduser, user):
    if user and user.username != enduser.user.username:
        is_friend = user.to_friend_set.all().filter(from_friend=enduser.user).count()
        is_followed_by = user.friend_set.all().filter(to_friend=enduser.user).count()
    else: 
        is_friend = None
        is_followed_by = None

    if enduser.birthdate is not None:
        bday = int((int(time.time()) - int(time.mktime(time.strptime(str(enduser.birthdate), '%Y-%m-%d %H:%M:%S'))))/ 31556926),  # large number is seconds in a year
    else:
        bday = None

    return {'username': enduser.user.username,
            'location': enduser.location,
            'tags': ' '.join(tag.name for tag in enduser.tags.all()),
            'age': bday,
            "latest_view": [defang_pageview(pageview) for pageview in PageView.objects.filter(user=enduser.user).order_by("-startTime").values()[:1]], ## VERY ANNOYING but seems safe
            "is_friend": is_friend,
            "is_followed_by": is_followed_by,
            'website': enduser.homepage,
            'id': enduser.user.id,
            'gender': enduser.gender
            }

def get_top_users_for_filter(request):
    n = 20
    query = _get_query_for_request(request)
    friends = request.GET['friends'] # a string "friends" or "everyone"
    seen = request.GET['seen'] # 0 for all 1 for has seen
    group = request.GET['groups']  # string that corresponds to a tag

    if request.user.username:
        request_user = get_object_or_404(User, username=request.user.username)
    else:
        requset_user = False

    @cache.region('long_term')
    def fetch_data(qry, user, bar):
        if qry == "EndUser.objects.filter(":
            endusers = EndUser.objects.all();
        else: 
            endusers = eval(qry + ").values_list('user_id')") 
 
            if friends is "my friends":
                user = User.objects.filter(username=request.user.username)
                friends = [friendship.to_friend for friendship in user.friend_set.all()] 
                endusers = [friend for friend in friends if endusers.index(friend.id) ]  ## friend.user

        ## rank the users
        results = [[enduser, PageView.objects.filter(user=enduser.user).count()] for enduser in endusers]
        results.sort(key=lambda x:-x[1])

        return results[:n]


     ## forgot the shorter way of doing this
    if friends is "my friends":
        usr = request.user.username
    else:
        usr = "all"

    results = fetch_data(query, usr, "users")
    
    return json_response({"code":200, "results": [[defang_enduser(item[0], request_user), item[1]] for item in results] })


def get_trending_sites(request):
    n = 20
    query = _get_query_for_request(request)
    friends = request.GET['friends'] # a string "friends" or "everyone"
    seen = request.GET['seen']
    group = request.GET['groups']  # string that corresponds to a tag

    @cache.region('long_term')
    def fetch_data(qry, user, foo, seen):
        if qry == "EndUser.objects.filter(":
            ## if there is no qry 
            new_pageviews = PageView.objects.filter(startTime__gt=int(time.time() * 1000) - 86400000)
            old_pageviews = PageView.objects.filter(startTime__range=(int(time.time() * 1000) - (86400000 *2), int(time.time() * 1000) - 86400000))

        else: 
            endusers = eval(qry + ").values_list('user_id')") 
 
            if friends is "my friends":
                user = User.objects.filter(username=request.user.username)
                friends = [friendship.to_friend for friendship in user.friend_set.all()] 
                endusers = [friend.id for friend in friends if endusers.index(friend.id) ] 
                # is there a more effecient way of finding overlap between 2 arrays?

            # always recently
            new_pageviews = PageView.objects.filter(user__in=User.objects.filter(id__in=endusers), startTime__gt=int(time.time() * 1000) - 86400000)
            old_pageviews = PageView.objects.filter(user__in=User.objects.filter(id__in=endusers), startTime__range=(int(time.time() * 1000) - (86400000 *2), int(time.time() * 1000) - 86400000))
                

            # filter out sites seen by user 
            if request.user.username and seen == "sites not seen":
                user = User.objects.filter(username=request.user.username)
                
                user_uniq = uniq(PageView.objects.filter(user=user).values(),lambda x:x["url"],None)
                new_pageviews = [site for site in new_pageviews if not user_uniq[site["url"]]] # not tested  -- maybe1 user_uniq[site] ??
                old_pageviews = [site for site in old_pageviews if not user_uniq[site["url"]]] # not tested  -- maybe1 user_uniq[site] ??

        results = []

        ## rank the pageviews
        ordered_new_pageviews = _get_pageviews_ordered_by_count(new_pageviews)
        ordered_old_pageviews = _get_pageviews_ordered_by_count(old_pageviews)

        for i in range(len(ordered_new_pageviews)): ## iterate over the more recent dudes
            old_rank = index_of_url(ordered_new_pageviews[i]['url'],ordered_old_pageviews)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference
                results.append([ordered_new_pageviews[i], diff] )
            else:
                pass
                    
        results.sort(key=lambda x: -x[1])        
        return [defang_pageview(pview[0]) for pview in results[:n]]

     ## forgot the shorter way of doing this
    if friends is "my friends":
        usr = request.user.username
    else:
        usr = "all"

    results = fetch_data(query, usr, "trending", seen)
    return json_response({"code":200, "results": results})




def get_to_from_url_plugin(request, n):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    url = request.GET['url'].strip()

    # added this to check if url exists in the logs
    if  len(PageView.objects.filter(url=url)) < 1:
        # fail silently 
        return json_response({ "code":200, "results": {'pre':"", 'next':"", 'pre_titles': "" , 'next_titles' : "" } })
    n = int(n)

    users = User.objects.all()
    req_type = {}
    req_type['global'] = 'global'

    return_results = to_from_url(url, users, req_type)

    if request.GET.has_key('username'):
        username = request.GET['username']
        friend_stats = get_top_friend_and_number_friends_for_url(request, username)
        return json_response({ "code":200, "results": return_results, "friend_stats": friend_stats })
        
    return json_response({ "code":200, "results": return_results })


# FILL CACHE
# ok so each of these are 2 functions because if you indent the return statment of the cached function it doesnt cache

# to_from_url for both plugin and page stats
def fill_to_from_url_cache():
    to_msec = int(time.time()*1000)
    from_msec = to_msec - (18122400000) # past three weeks

    users = User.objects.all()
    req_type = {}
    req_type['global'] = 'global'

    phits = PageView.objects.filter(startTime__gt=from_msec,endTime__lte=to_msec).order_by("-startTime").values()
    uphit = uniq(phits,lambda x:x["url"],None)

    for url in uphit:        
        cache_to_from_url(url['url'],users, req_type, phits, uphit)
    return 'party a lot'
    
def cache_to_from_url(url,users, req_type, phits, uphit):
    @cache.region('very_long_term')
    def fetch_data(url, users, req_type):
        pre = {}
        next = {}
        titles = {}
        accesses = [f for f in phits if f['url'] == url] 
        for access in accesses:
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                #prev_access = sorted([f for f in phits if f['startTime'] < access['startTime'] and f['user_id'] is access['user_id']], key=lambda(v2):-v2['startTime'])[0] 
                #sorted to give biggest number

                # this is pre-sorted
                prev_access = [f for f in phits if f['startTime'] < access['startTime'] and f['user_id'] is access['user_id']][0] 

                if prev_access['url'] != url:
                    pre[prev_access['url']] = pre.get(prev_access['url'],0) + 1
                    if prev_access['title'] is not None:
                        titles[prev_access['url']] = prev_access['title']
                    else:
                        titles[prev_access['url']] = prev_access['url']
                else:
                    pass
            except:
                pass
            try:
                # get the page we logged IMMEDIATELY before access for the particular access's user in question
                next_access = sorted([f for f in phits if f['startTime'] > access['startTime'] and f['user_id'] is access['user_id']], key=lambda(v2):v2['startTime'])[0]
                #sorted to give smallest number
                if next_access['url'] != url:
                    next[next_access['url']] = next.get(next_access['url'],0) + 1
                    if next_access.title is not None:
                        titles[next_access['url']] = next_access['title']
                    else:
                        titles[next_access['url']] = next_access['url']
                else:
                    pass
            except:
                pass
            
        def sort_by_counts(count_dict):
            l = count_dict.items()
            l.sort(key=lambda x: -x[1])
            return l
        
        pre_sorted = sort_by_counts(pre)[:7]
        next_sorted = sort_by_counts(next)[:7]

        return { 'pre':pre_sorted, 'next':next_sorted, 'pre_titles': [ titles[x[0]] for x in pre_sorted ] , 'next_titles' : [ titles[x[0]] for x in next_sorted ] }

    return_results = fetch_data(url, users, req_type)    
    return 'party a little'
