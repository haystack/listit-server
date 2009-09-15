
from jv3.models import *
from django.utils.simplejson import JSONDecoder

search_cache = {}
search_query_cache = {}

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
                    queries.append(query["search"])
                    searches.append(al)
        elif al["action"] == 'clear-search':
            searches.append(al)

    search_cache[user.id] = searches
    search_query_cache[user.id] = queries

def get_searches(notes):
    global search_cache
    global search_query_cache

    for note in notes:
        if note["owner"].id not in search_cache:
            user_search(note["owner"])

    all_queries = []
    for user in search_query_cache:
        for query in search_query_cache[user]:
            all_queries.append(query)

    return all_queries

"""
    user_query_count = {}
    for user in search_query_cache:
        user_query_count[user] = {}
        for query in search_query_cache[user]:
            if query in all_queries:
                all_queries[query] += 1
            else:
                all_queries
"""
