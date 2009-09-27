import re,sys,time,operator,os,math, datetime
from django.template import loader, Context
from django.http import HttpResponse,HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf.urls.defaults import *
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from eyebrowse.forms import *
from eyebrowse.models import *
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from os.path import splitext
from django.db.models.signals import post_save
from jv3.models import Event ## from listit, ya.
from django.utils.simplejson import JSONEncoder, JSONDecoder
# beaker
from eyebrowse.beakercache import cache
from django.db.models import Sum
from django.db.models import query
from django.db.models.query import QuerySet
from jv3.utils import json_response
import urlparse

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
            return [s[0] for s in queryset.values_list('host')] # <- comparatively lame. # pretty badass too: [urlparse.urlparse(url[0])[1] for url in queryset.values_list('host')]
        @staticmethod
        def filter_queryset(queryset,host):
            return queryset.filter(host=host) #queryset.filter(entityid__contains="://%s/"%url)         ## tres. badass!!!

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

def _get_pages_for_user(user,from_msec,to_msec):
    return PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)

def _unpack_from_to_msec(request):
    return (request.GET.get('from',0), request.GET.get('to',long(time.mktime(time.localtime())*1000)))

def _unpack_times(request):
    return (long(request.GET['first_start']), long(request.GET['first_end']), long(request.GET['second_start']), long(request.GET['second_end']))

def _get_top_hosts_n(users,start,end):
    time_per_host = _get_time_per_page(users,start,end,grouped_by=EVENT_SELECTORS.Host) 

    ordered_visits = [h for h in time_per_host.iteritems()]
    ordered_visits.sort(lambda u1,u2: int(u2[1] - u1[1]))
    return ordered_visits    

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

def _get_time_per_page(user,from_msec,to_msec,grouped_by=EVENT_SELECTORS.Page):
    if type(user) == QuerySet:
        mine_events = PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec)
    elif type(user) == list:
        mine_events = PageView.objects.filter(user__in=user,startTime__gte=from_msec,endTime__lte=to_msec)
    else:
        mine_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        
    uniq_urls  = set( grouped_by.access(mine_events) )
    times_per_url = {}
    for url in uniq_urls:
        # might be faster to define a variable here rather than doing filter 2x for the if and the reduce
        grouped_by_filtered = grouped_by.filter_queryset(mine_events,url).values_list('startTime','endTime')
        # to make sure not to reduce an empty item 
        if grouped_by_filtered:
            times_per_url[url] = long(reduce(lambda x,y: x+y, [ startend[1]-startend[0] for startend in grouped_by_filtered ] ))
        else:
            pass
    return times_per_url

def defang_pageview(pview):    
    return {"start" : long(pview.startTime), "end" : long(pview.endTime), "url" : pview.url, "host": pview.host, "title": pview.title, "id":pview.id, "user": pview.user.username } 
    ## too slow "location":get_enduser_for_user(pview.user).location }

def get_views_user(from_msec, to_msec, username):
    user = get_object_or_404(User, username=username)

    hits = _get_pages_for_user(user ,from_msec,to_msec)
    return [ defang_pageview(evt) for evt in hits ]    

def get_recent_web_page_view_user(request, username, n):
    user = get_object_or_404(User, username=username)
    n = int(n)

    # gets unique pages
    phits = PageView.objects.filter(user=user).order_by("-startTime")

    if n < 0 or n is None:
        n = len(phits)

    uphit = uniq(phits,lambda x:x.title,n)
    
    results = [ defang_pageview(evt) for evt in uphit ]

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

    return json_response({ "code":200, "results": results });


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
    def fetch_data(inputURL, users):
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

    results = fetch_data(url, users)
    return results


def get_most_shared_hosts(request, n):
    n = int(n)

    @cache.region('long_term')
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

    
def get_top_hosts_compare(first_start, first_end, second_start, second_end, n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)

    @cache.region('long_term')
    def fetch_data(users, first_start, first_end, second_start, second_end):
        times_per_url_first = _get_top_hosts_n(users,first_start,first_end) # can pass multiple or single users
        times_per_url_second = _get_top_hosts_n(users,second_start,second_end)
        
        def index_of(what, where):
            try:
                return [ h[0] for h in where ].index(what)
            except:
                print sys.exc_info()
                pass
            return None

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

    results = fetch_data(users, first_start, first_end, second_start, second_end)
    return results


def get_top_urls_following(request, username, n):
    if not 'first_start' in request.GET:
        return json_response({ "code":404, "error": "get has no 'first_start' key" }) 

    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.to_friend for friendship in user.friend_set.all()]

    n = int(n)
    first_start,first_end,second_start,second_end = _unpack_times(request)
    times_per_url_first = _get_top_n(user,first_start,first_end)
    times_per_url_second = _get_top_n(user,second_start,second_end)

    for friend in following:
        friend_user = get_object_or_404(User, username=friend.username)
        times_per_url_first.append(_get_top_n(friend_user,first_start,first_end))
        times_per_url_second.append(_get_top_n(friend_user,first_start,first_end))

    def index_of(what, where):
        try:
            return [ h[0] for h in where ].index(what)
        except:
            print sys.exc_info()
            pass
        return None

    results = []
    for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
        old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
        if old_rank is not None:
            diff = - (i - old_rank)  # we want the gain not the difference
            results.append(times_per_url_second[i] + (diff,) )
        else:
            results.append( times_per_url_second[i] )

    return json_response({ "code":200, "results": results[0:n] })


def _get_graph_points_for_results(results, to_msec, from_msec, n):
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


def get_profile_graphs(from_msec_raw, to_msec_raw, username):    
    user = get_object_or_404(User, username=username)
    from_msec_rounded = round_time_to_half_day(from_msec_raw)
    to_msec_rounded = round_time_to_half_day(to_msec_raw)

    @cache.region('long_term')
    def fetch_data(user, from_msec, to_msec):
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

    results = fetch_data(user, from_msec_rounded, to_msec_rounded) 
    return results


def get_pagestats_graphs(from_msec_raw, to_msec_raw, url, req_type):    
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    from_msec_rounded = round_time_to_half_day(from_msec_raw)
    to_msec_rounded = round_time_to_half_day(to_msec_raw)

    @cache.region('long_term')
    def fetch_data(url, users, from_msec, to_msec):
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

        data.update(_get_graph_points_for_results(views, to_msec, from_msec, 28))

        data['dayWeek'] = weekPts
        data['timeDay'] = hrPts
        return data

    results = fetch_data(url, users, from_msec_rounded, to_msec_rounded) 
    return results


def get_trending_urls(request, n):
    if not 'first_start' in request.GET:
        return json_response({ "code":404, "error": "get has no 'first_start' key" }) 

    user = User.objects.all();
    user = user[0] ## again this is fail not sure how to iterate through the users esp if they have not logged anything
    n = int(n)
    first_start,first_end,second_start,second_end = _unpack_times(request)
    times_per_url_first = _get_top_n(user,first_start,first_end)
    times_per_url_second = _get_top_n(user,second_start,second_end)
    
    def index_of(what, where):
        try:
            return [ h[0] for h in where ].index(what)
        except:
            print sys.exc_info()
            pass
        return None

    results = []
    for i in range(len(times_per_url_second)): ## iterate over the more recent dudes
        old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
        if old_rank is not None:
            diff = - (i - old_rank)  # we want the gain not the difference
            results.append(times_per_url_second[i] + (diff,) )
        else:
            results.append( times_per_url_second[i] )
                
    return json_response({ "code":200, "results": results[0:n] }) ## [(u, long(times_per_url[u])) for u in urls_ordered[0:n]] })

    

def get_top_users(from_msec, to_msec, n, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()

    n = int(n)

    from_msec_rounded = round_time_to_half_day(from_msec)
    to_msec_rounded = round_time_to_half_day(to_msec)

    @cache.region('top_users_long_term')
    def fetch_data(from_msec, to_msec, req_type):
        results = []
        for user in users:
            try:
                results.append( {"user": user.username, "number": PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).count() } )
            except:
                pass
        results.sort(key=lambda x:-x["number"])
        return results[0:n]
        
    return fetch_data(from_msec_rounded, to_msec_rounded, req_type)


def get_top_users_for_url(from_msec, to_msec, n, url, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()] # list
    else:
        users = User.objects.all() # queryset

    n = int(n)

    from_msec_rounded = round_time_to_half_day(from_msec)
    to_msec_rounded = round_time_to_half_day(to_msec)

    barbar = "foo" # to keep cache unique
    @cache.region('top_users_long_term')
    def fetch_data(from_msec, to_msec, url, barbar):
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

    return_results = fetch_data(from_msec_rounded, to_msec_rounded, url, barbar)
    return return_results


def get_percent_logging(url_raw, req_type):
    if 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()] # list
    else:
        users = User.objects.all() # queryset

    scheme, url_parsed, boo, foo, bar, baz = urlparse.urlparse(url_raw)

    @cache.region('top_users_long_term')
    def fetch_data(url, users):
        results = []
        
        if (users) == list:
            return PrivacySettings.objects.filter(user__in=users, whitelist__in=url).count()/User.objects.all().count()
        else:
            return PrivacySettings.objects.filter(whitelist__in=url).count()/User.objects.all().count()

    return_results = fetch_data(url_parsed, users)
    return return_results


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

## get most recent urls now returns elements with distinct titles. no repeats!
def get_most_recent_urls(request, n):
    n = int(n)

    # gets unique pages
    phits = PageView.objects.filter().order_by("-startTime")

    if n < 0 or n is None:
        n = len(phits)

    uphit = uniq(phits,lambda x:x.title,n)
    
    results = [ defang_pageview(evt) for evt in uphit ]

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


def get_users_most_recent_urls(request, username, n):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" }) 

    user = get_object_or_404(User, username=username)
    n = int(n)

    from_msec,to_msec = _unpack_from_to_msec(request)
    hits = _get_pages_for_user(user,from_msec,to_msec)

    return json_response({ "code":200, "results": [ defang_pageview(evt) for evt in hits[0:n] ] });    
        
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

def get_to_from_url(n, url, req_type):
    if 'user' in req_type:
        users = get_object_or_404(User, username=req_type['user'])
    elif 'friends' in req_type:
        usr = get_object_or_404(User, username=req_type['friends'])
        users = [friendship.to_friend for friendship in usr.friend_set.all()]
    else:
        users = User.objects.all()
    
    # added this to check if url exists in the logs
    if  len(PageView.objects.filter(url=url)) < 1:
        # fail silently 
        return {'pre':"", 'next':"", 'pre_titles': "" , 'next_titles' : "" }
    n = int(n)

    @cache.region('to_from_url')
    def fetch_data(url, users, req_type):
        if type(users) == QuerySet:
            accesses = PageView.objects.filter(url=url)#,startTime__gte=from_msec,endTime__lte=to_msec)
        elif type(users) == list:
            accesses = PageView.objects.filter(user__in=users, url=url)#,startTime__gte=from_msec,endTime__lte=to_msec)
        else:
            accesses = PageView.objects.filter(user=users, url=url)#,startTime__gte=from_msec,endTime__lte=to_msec)

        pre = {}
        next = {}
        titles = {}
        for access in accesses:
            try:
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
            except:
                pass
            try:
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
            except:
                pass
            
        def sort_by_counts(count_dict):
            l = count_dict.items()
            l.sort(key=lambda x: -x[1])
            return l
        
        pre_sorted = sort_by_counts(pre)
        next_sorted = sort_by_counts(next)

        return { 'pre':pre_sorted[:7], 'next':next_sorted[:7], 'pre_titles': [ titles[x[0]] for x in pre_sorted[:7] ] , 'next_titles' : [ titles[x[0]] for x in next_sorted[:7] ] }

    return_results = fetch_data(url, users, req_type)
    return return_results


## INDEX PAGE
def get_homepage(request):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" }) 

    from_msec,to_msec = _unpack_from_to_msec(request)

    request_type = {'global':'all'}

    top_users = get_top_users(from_msec, to_msec, 10, request_type)    
    views_user = get_views_user(from_msec, to_msec, top_users[0]['user'])
    # eventually should probably cache get_most_recent_urls here or fix it to not sort the entire db every call

    return json_response({ "code":200, "results": [top_users, views_user] });


## TICKER PAGE
def get_ticker(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    request_type = request.GET['type'].strip()
    from_msec,to_msec = _unpack_from_to_msec(request)

    top_users = get_top_users(from_msec, to_msec, 10, request_type)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    top_hosts = get_top_hosts_compare(first_start,first_end,second_start,second_end, 10, request_type)
    profile_queries = get_profile_queries(request_type)
    #trending_urls = get_trending_urls(from_msec, to_msec, 10)

    return json_response({ "code":200, "results": [top_users, top_hosts, profile_queries] });


## USERS PAGE
def get_users_page(request):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" }) 

    request_type = {'global':'all'}

    from_msec,to_msec = _unpack_from_to_msec(request)

    top_users = get_top_users(from_msec, to_msec, 10, request_type)
    profile_queries = get_profile_queries(request_type)

    return json_response({ "code":200, "results": [top_users, profile_queries] });


## PROFILE PAGE
def get_profile(request):
    if not 'type' in request.GET:
        return json_response({ "code":404, "error": "get has no 'type' key" }) 

    request_type = {}
    request_type['user'] = request.GET['type'].strip()

    from_msec,to_msec = _unpack_from_to_msec(request)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    top_hosts = get_top_hosts_compare(first_start,first_end,second_start,second_end, 10, request_type)
    profile_queries = get_profile_queries(request_type)
    graphs = get_profile_graphs(from_msec, to_msec, request_type['user'])

    return json_response({ "code":200, "results": [graphs, top_hosts, profile_queries] });


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

    from_msec,to_msec = _unpack_from_to_msec(request)

    percent_logging = get_percent_logging(url, request_type)
    profile_queries = get_page_profile_queries(url, request_type)
    top_users = get_top_users_for_url(from_msec, to_msec, 10, url, request_type)
    graphs = get_pagestats_graphs(from_msec, to_msec, url, request_type)
    to_from_url = get_to_from_url(7, url, request_type)

    return json_response({ "code":200, "results": [graphs, top_users, profile_queries, to_from_url, percent_logging] });

## GRAPHS PAGE
def get_views_user_json(request, username):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" })

    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)

    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)

    def fetch_data(from_msec, to_msec, user):
	hits = _get_pages_for_user(user ,from_msec,to_msec)
	return [ defang_pageview(evt) for evt in hits ]

    results = fetch_data(from_msec_raw, to_msec_raw, user)

    return json_response({ "code":200, "results": results });


def get_hourly_daily_top_urls_user(request, username, n):
    n = int(n)
    inputUser = get_object_or_404(User, username=username)

    @cache.region('long_term')
    def fetch_data(user, n, baaaa):
        views = PageView.objects.filter(user=user)

        hrPts = dict([ (i, {}) for i in range(0,24) ])
        weekPts = dict([ (i, {}) for i in range(0,7) ])

        for view in views:
            weekday = datetime.datetime.fromtimestamp(view.startTime/1000).weekday()
            hour = datetime.datetime.fromtimestamp(view.startTime/1000).hour
            
            if view.url in hrPts[hour]:
                hrPts[hour][view.url] += 1
            else:
                hrPts[hour][view.url] = 1

            if view.url in weekPts[weekday]:
                weekPts[weekday][view.url] += 1
            else:
                weekPts[weekday][view.url] = 1

        lResult = []
        for x in range(7):
            phlat = weekPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2)
            lResult.append((x,phlat[:n]))

        rResult = []
        for x in range(24):
            phlat = hrPts[x].items()
            phlat.sort(key=lambda(k,v2):-v2)
            rResult.append((x,phlat[:n]))

        return [lResult,rResult]
    return_results = fetch_data(inputUser, n, "asdkjfhasd")
        
    return json_response({ "code":200, "results": return_results }) 


## FRIENDS PAGE
def get_following_views(request, username):
    if not 'from' in request.GET:
        return json_response({ "code":404, "error": "get has no 'from' key" }) 

    user = get_object_or_404(User, username=username)
    enduser = get_enduser_for_user(user)
    following = [friendship.to_friend for friendship in user.friend_set.all()]

    from_msec,to_msec = _unpack_from_to_msec(request)
    from_msec_rounded = round_time_to_day(from_msec)
    to_msec_rounded = round_time_to_day(to_msec)

    # potentially i can just not pass it the 'following' param hrmz
    @cache.region('long_term')
    def fetch_data(from_msec, to_msec, user, following):
        friends_results = []

        # add the request.user
        user_events = PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec)
        friends_results.append( {"username": enduser.user.username, "events": [ defang_pageview(evt) for evt in user_events ] } )
        
        # add friends
        for friend in following:
            #friend_user = get_object_or_404(User, username=friend.username)
            events = PageView.objects.filter(user=friend,startTime__gte=from_msec,endTime__lte=to_msec)
            friends_results.append( {"username": friend.username, "events": [ defang_pageview(evt) for evt in events ] } )
            
        #friends_results.sort(key=lambda x:(x["username"], x["username"]))
        return friends_results

    results = fetch_data(from_msec_rounded, to_msec_rounded, user, following)

    return json_response({ "code":200, "results": results });    

def get_top_hosts_comparison_friends(request, username, n):
    if not 'first_start' in request.GET:
        return json_response({ "code":404, "error": "get has no 'first_start' key" })

    user = get_object_or_404(User, username=username)

    following = [friendship.to_friend for friendship in user.friend_set.all()]
    n = int(n)

    first_start,first_end,second_start,second_end = _unpack_times(request)
    first_start = round_time_to_day(first_start)
    first_end = round_time_to_day(first_end)
    second_start = round_time_to_day(second_start)
    second_end = round_time_to_day(second_end)

    @cache.region('long_term')
    def fetch_data(following, first_star, first_end, second_start, second_end):
        times_per_url_first = _get_top_hosts_n(following,first_start,first_end)
        times_per_url_second = _get_top_hosts_n(following,second_start,second_end)

        def index_of(what, where):
            try:
                return [ h[0] for h in where ].index(what)
            except:
                print sys.exc_info()
                pass
            return None

        results = []

        for i in range(len(times_per_url_second)): ## iterate over the more recent dudes                  
            old_rank = index_of(times_per_url_second[i][0],times_per_url_first)
            if old_rank is not None:
                diff = - (i - old_rank)  # we want the gain not the difference     
                results.append(times_per_url_second[i] + (diff,) )
            else:
                results.append( times_per_url_second[i] )

        return results[0:n]

    return_results = fetch_data(following,first_start,first_end,second_start,second_end)

    return json_response({ "code":200, "results": return_results })



## DO NOT DELETE USED BY OLD PLUGIN
def get_top_friend_for_url(request, username):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    user = get_object_or_404(User, username=username)
    users = [friendship.to_friend for friendship in user.friend_set.all()]
    
    get_url = request.GET['url'].strip()

    barbar = "top friend for url" # to keep cache unique
    @cache.region('top_users_long_term')
    def fetch_data( url, username):
        results = []
        for user in users:
            number = PageView.objects.filter(user=user,url=url).count()
            results.append( {"user": user.username, "number": number } )

        results.sort(key=lambda x: -x["number"])
        return results[0:1]

    return_results = fetch_data(get_url, username)
    return return_results

def get_number_friends_logged_url(request, username):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    user = get_object_or_404(User, username=username)
    friends = [friendship.to_friend for friendship in user.friend_set.all()]

    get_url = request.GET['url'].strip()    

    @cache.region('top_users_long_term')
    def fetch_data(url, username):
        results = []
        number = 0
        for friend in friends:
            if PageView.objects.filter(user=friend,url=url).count() > 0:
                number += 1

        return number
    return_results = fetch_data(get_url, username)
    return return_results

def get_to_from_url_plugin(request, n):
    if not 'url' in request.GET:
        return json_response({ "code":404, "error": "get has no 'url' key" }) 

    from_msec_raw,to_msec_raw = _unpack_from_to_msec(request)
    to_msec_rounded = round_time_to_day(to_msec_raw)
    url = request.GET['url'].strip()

    # added this to check if url exists in the logs
    if  len(PageView.objects.filter(url=url)) < 1:
        # fail silently 
        return json_response({ "code":200, "results": {'pre':"", 'next':"", 'pre_titles': "" , 'next_titles' : "" } })
    n = int(n)

    @cache.region('to_from_url')
    def fetch_data(to_msec, url):
        accesses = PageView.objects.filter(url=url)#,startTime__gte=from_msec,endTime__lte=to_msec)
        pre = {}
        next = {}
        titles = {}
        for access in accesses:
            try:
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
            except:
                pass
            try:
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
            except:
                pass
            
        def sort_by_counts(count_dict):
            l = count_dict.items()
            l.sort(key=lambda x: -x[1])
            return l
        
        pre_sorted = sort_by_counts(pre)
        next_sorted = sort_by_counts(next)

        return { 'pre':pre_sorted[:7], 'next':next_sorted[:7], 'pre_titles': [ titles[x[0]] for x in pre_sorted[:7] ] , 'next_titles' : [ titles[x[0]] for x in next_sorted[:7] ] }

    return_results = fetch_data(to_msec_rounded, url)

    #hopefully this will be out of the cache
    if request.GET.has_key('username'):
        username = request.GET['username']
        friend_stats = {'top_friend': get_top_friend_for_url(request, username), 'num_friends': get_number_friends_logged_url(request, username) }
    
        return json_response({ "code":200, "results": return_results, "friend_stats": friend_stats })
        
    return json_response({ "code":200, "results": return_results })
