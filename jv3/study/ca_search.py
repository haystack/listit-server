
from jv3.models import *
from django.utils.simplejson import JSONDecoder

search_cache = {}
search_query_cache = {}
all_searches = []
all_queries = []

def user_search(user,days_ago=None):
    from jv3.study.content_analysis import activity_logs_for_user
    global search_cache
    global search_query_cache

    alogs = activity_logs_for_user(user,None,days_ago)

    searches = []
    queries = []
    for al_i in range(len(alogs)):
        al = alogs[al_i]
        if al["action"] == 'search':
            try:
                query = JSONDecoder().decode(al["search"])
            except:
                continue
            if type(query) == dict:
                if 'search' in query:
                    # no empty searches pls
                    if len(query["search"].strip()) > 0:
                        queries.append(query["search"])
                        searches.append(al)
        elif al["action"] == 'clear-search':
            searches.append(al)

    search_cache[user.id] = searches
    search_query_cache[user.id] = queries


def get_searches(users):
    global search_cache
    global search_query_cache
    global all_searches
    global all_queries

    for user in users:
        user_search(user)

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
