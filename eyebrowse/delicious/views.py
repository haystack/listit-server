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
from eyebrowse.json.views import uniq
from datetime import timedelta
import hashlib
from operator import itemgetter    
import json
from urllib2 import Request, urlopen, URLError

def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def _get_recent_urls_for_user(user):
    to_msec = int(time.time()*1000)
    from_msec = to_msec - 604800000 # past week
    return [evt['url'] for evt in 
            uniq(PageView.objects.filter(user=user,startTime__gte=from_msec,endTime__lte=to_msec).values(),
                 lambda x:x["url"],None)]

def _get_delicious_tags_for_url(url):
    time.sleep(5)
    url_hash = hashlib.md5(url.encode('utf8')).hexdigest()
    url = 'http://feeds.delicious.com/v2/json/urlinfo/' + url_hash
    req = Request(url)
    try:
        response = urlopen(req)
    except URLError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
    else:
        # everything is fine
        s = response.read()
        x = json.loads(s)
        if len(x):
            if x[0]['top_tags']:
                return x[0]['top_tags'].keys()

def _get_delicious_tags_for_user(user):
    urls = _get_recent_urls_for_user(user)
    return [_get_delicious_tags_for_url(url) for url in urls]


def _get_top_tfidf_tags_for_enduser(enduser, n, tags_for_page, all_tags, number_of_pages):
    tags = flatten([tags_for_page[url] for url in _get_recent_urls_for_user(enduser.user)])    
    enduser_tag_count = len(tags)    

    def freq_in_enduser_tags(tag):
        return tags.count(tag)

    def freq_in_all_pages(tag):
        #this will work as delicious will not return 2 of the same tags for one page
        return corpus.count(tag) 
    
    def tfidf(word): 
        tf = (freq_in_enduser_tags(word) / float(enduser_tag_count))
        idf = math.log(number_of_pages / freq_in_all_pages(tag))
        return tf * idf

    tfidf_tags = dict([(tag, tfidf(tag)) for tag in tags])
    return sorted(tfidf_tags.items(), key=itemgetter(1), reverse=True)[:n]


def tag_the_users():
    tags_for_page = get_delicious_corpus()
    all_tags = flatten(tags_for_page.values())
    number_of_pages = len(tags_for_page) #number of pages with tags

    for enduser in EndUser.objects.all():        
        # remove old tas
        [enduser.tags.remove(tag) for tag in enduser.tags.all()]
        # enduser.save() #maybe?
    
        tfidf_tags = _get_top_tfidf_tags_for_enduser(enduser, 10, tags_for_page, all_tags, number_of_pages)        
        print tfidf_tags
        for tag_name in tfidf_tags:
            tag, dummy = UserTag.objects.get_or_create(name=tag_name)
            enduser.tags.add(tag) 
        enduser.save()
            

def get_delicious_corpus():
    to_msec = int(time.time()*1000)
    from_msec = to_msec - 604800000 # past week
    
    # say your prayers -- returns a dict {url:[tag,tag2,tag3]},...
    return dict([ (page['url'], _get_delicious_tags_for_url(page['url'])) for page in 
                  uniq(PageView.objects.filter(startTime__gte=from_msec,endTime__lte=to_msec).values(),
                       lambda x:x["url"],None) ])
