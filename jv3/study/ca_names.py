import nltk
from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
from jv3.utils import current_time_decimal
from django.utils.simplejson import JSONEncoder, JSONDecoder
from jv3.study.study import mean,median
from rpy2 import robjects as ro
from ca_datetime import note_date_count
from ca_util import *
from ca_sigscroll import *
from ca_load import *
from ca_names import *
import nltk.cluster as cluster
r = ro.r
import jv3
import random,sys,re
import numpy


## names 
_names = None
name_stop_list = ["web","page","les","tray"]

def note_names(note):
    from content_analysis import count_regex_matches
    global _names
    global name_stop_list
    if _names is None:
        _names = list(set([x.lower() for x in names.read() if len(x) > 2 and (x.lower() not in name_stop_list)]))
    rnames = [ "(^|\W+)%s($|\W+)" % nhit for nhit in [name for name in _names if name in note["contents"]]]
    if len(rnames) > 0:
        hits = [(n,count_regex_matches(n,note["contents"])) for n in rnames]
        #print hits
        hits = {"names": reduce(lambda x,y: x + y, [count_regex_matches(n,note["contents"]) for n in rnames])}
        return hits
    return {"names": 0}    
