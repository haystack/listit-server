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
import nltk.cluster as cluster
r = ro.r
import jv3
import random,sys,re
import numpy

# ternary
c = lambda vv : apply(r.c,vv)
q=lambda a,b,c: (b,c)[not a]

# lm 
r = ro.r

## PREPROCESSING ##################################################
## tokenize
all_pass = lambda x: True
striplow = lambda x: x.strip().lower()
stopword_low = [striplow(x) for x in stopwords.words()]
stopword = lambda x: x not in stopword_low

## takes a _single_note_ or a queryset
_notes_to_values = lambda note: note.values('id','owner','contents',"jid","created","deleted","edited")

_note_instance_to_value = lambda note: {'id':note.id, 'owner':note.owner, 'contents': note.contents,
                                          'jid':note.jid, 'created':long(note.created), 'deleted':note.deleted,
                                          'edited':long(note.edited)}
_actlogs_to_values = lambda actlog: actlog.values("id","action","owner","when","client","noteid","search","noteText")

eliminate_regexp = lambda regexp,s: "".join(re.compile(regexp).split(s))
eliminate_urls = lambda s: eliminate_regexp("https?://[^\s]*",s)
str_n_urls = lambda s : count_regex_matches("(https?://[^\s]*)|((^|\W+)(\w[\d\w]+\.){2,5}\w{2,3})($|\W)",s)
str_n_emails = lambda s: count_regex_matches("(^|\W)[\w\d]+\@(\w[\w\d]+\.)+\w{2,3}($|\W)",s)

_re_cache = {}
def count_regex_matches(res,s):
    import re
    global _re_cache
    exp = None
    if _re_cache.get(res,None):
        exp = _re_cache[res]
    else:
        exp = re.compile(res)
    hits = 0
    hit = exp.search(s)
    while hit:
        s = s[hit.end():]
        hits = hits + 1
        hit = exp.search(s)
    return hits

def update_dictionary(words,dictionary):
    for w in words:
        dictionary[w] = dictionary.get(w,0) + 1
    pass

def to_feature_vec(tokens,wordlist):
    fv = {}
    for t in tokens:
        if t in wordlist:
            fv[t] = fv.get(t,0)+1
    return fv

def notes_to_bow_features(notes, text=lambda x: eliminate_urls(x["contents"]), word_proc=striplow, word_filter=all_pass, lexicon=None,
                          lexicon_size_limit=float('Inf'), min_word_freq=0):
    tokenizer = WordTokenizer()
    notewords = lambda x : [ word_proc(x) for x in tokenizer.tokenize(text(n)) if word_filter(x) ]
    tokenized_notes = dict( [ (n["id"],notewords(n)) for n in notes ] )
    dictionary = {}    
    if lexicon is None:
        ## build lexicon, otherwise use dictionary passed in
        [ update_dictionary(tn,dictionary) for nid,tn in tokenized_notes.iteritems() ]
        lexicon = [k for k in dictionary.keys() if dictionary[k] > min_word_freq]
        lexicon.sort(lambda x,y : dictionary[y] - dictionary[x])
        if lexicon_size_limit < float('Inf'):
            lexicon = lexicon[:lexicon_size_limit]
        pass
    ## print tokenized_notes 
    return (dict( [(nid, to_feature_vec(notewords,lexicon)) for nid,notewords in tokenized_notes.iteritems()] ),lexicon,dictionary)


    
# reconstitute
recon = lambda n,d : [d[x] for x in n.keys()]


## FEATURE COMPUTERS ##################################################################################
## given a note, returns features of that note

note_days_till_deletion = lambda x: {"days_till_deletion": q(x["deleted"],int(float(x["edited"] - x["created"])/(3600*1000.0*24)),-1)}
note_lifetime = lambda note : {'note_lifetime_s': float((q(note["deleted"],long(note["edited"]),current_time_decimal()) - long(note["created"]))/1000.0)}
note_owner = lambda note: {'note_owner': repr(note["owner"])}
note_length = lambda x : {'note_length':len(x["contents"])}
note_words = lambda x : {'note_words':len(nltk.word_tokenize(eliminate_urls(x["contents"])))}
note_edits = lambda(note) : {'note_edits':len(activity_logs_for_note(note,"note-edit"))}
note_did_edit = lambda(note) : {'note_did_edit': note_edits(note) > 0}
note_deleted = lambda(note) : {'note_deleted': q(note["deleted"],True,False)}
note_urls = lambda note: {'note_urls': str_n_urls(note["contents"])}
note_phone_numbers = lambda x: {'phone_nums':count_regex_matches("(^|\s+)([0-9]( |-)?)?(\(?[0-9]{3}\)?|[0-9]{3})( |-)?([0-9]{3}( |-)?[0-9]{4}|[a-zA-Z0-9]{7})($|\s+)",x["contents"])}
note_emails = lambda note: {'email_addrs':str_n_emails(note["contents"])}

## addresses?
## dates/times

def note_pos_features(note):
    POS = ["CC","CD","DT","EX","FW","IN","JJ","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
    counts = dict([ (x, 0) for x in POS ])
    for k,pos in nltk.pos_tag(nltk.word_tokenize(note["contents"])):
        if pos in POS:
            counts[pos] = counts[pos]+ 1
    return counts

_names = None
name_stop_list = ["web","page","les","tray"]
def note_names(note):
    global _names
    global name_stop_list
    if _names is None:
        _names = list(set([x.lower() for x in names.read() if len(x) > 2 and (x.lower() not in name_stop_list)]))
    rnames = [ "(^|\W+)%s($|\W+)" % nhit for nhit in [name for name in _names if name in note["contents"]]]
    if len(rnames) > 0:
        hits = [(n,count_regex_matches(n,note["contents"])) for n in rnames]
        print hits
        hits = {"names": reduce(lambda x,y: x + y, [count_regex_matches(n,note["contents"]) for n in rnames])}
        return hits
    return {"names": 0}    

## now feature compilation stuff
default_note_feature_fns = [
    note_lifetime,
    note_owner,
    note_length,
    note_words,
    note_deleted,
    note_names,
    note_urls,
    note_emails,
    note_ss,
    note_phone_numbers,
    note_date_count,
    note_edits,
    note_days_till_deletion
]

content_features = [
    note_names,
    note_phone_numbers,
    note_urls,
    note_date_count,
    note_emails,
    note_pos_features
]                                                          

def notes_to_features(notes,include_bow_features=True,bow_parameters={},note_feature_fns=default_note_feature_fns):
    # generates feature vectors like this:
    # [ "notepkid": { "f1" : 12398 , "f2" : 102938, ... } ... ]
    lexicon = None
    lexicon_freq = None

    # preprocess notes
    for n in notes: n["contents"] = n["contents"].strip().lower()
    
    if include_bow_features:
        note_fvs,lexicon,lexicon_freq = notes_to_bow_features(notes,**bow_parameters)
    else:
        note_fvs = dict( [ (tn["id"],{}) for tn in notes ] )

    for n in notes:
        print "generating %s:%s " % (n["id"],n["contents"])
        [ note_fvs[n["id"]].update( ff(n) ) for ff in note_feature_fns ]
        #for ff in note_feature_fns:
        #    print ff
        #    note_fvs[n["id"]].update( ff(n) )


    # get all keys
    keys = {}
    [ keys.update(fv) for fv in note_fvs.values() ]
    keys = keys.keys()
    return keys,note_fvs

def kmeans_note_fvs(keys,nfvs,n=10,metric=cluster.euclidean_distance):
    # turn fvs into vectors
    vectors = []
    for n in nfvs:
        vectors.append( numpy.array([ n.get(k,0) for k in keys ]) )
    clusterer = cluster.KMeansClusterer(n, metric)
    clusterer.cluster(vectors, True)
    return clusterer


# def context_frame(notes):
#     features = {
#         "owner" : r.factor(apply(r.c, [ int(note['owner']) for note in notes])),
#         "lifetime": apply(r.c, [ note_lifetime(x) for x in notes ]),
#         "length": apply(r.c, [ note_length(x) for x in notes ]),
#         "urls" : apply(r.c, [ note_urls(x) for x in notes ])
#     };                                  
#     return features


def hist_ss(notes,days_ago=None):
    if type(notes[0]) == Note:   notes = _notes_to_values(notes)
    raws = [sigscroll_reads(n,days_ago=days_ago) for n in notes]
    return (r.hist(apply(r.c,raws)),raws)

def print_random_events(n=25000):
    import jv3.study.study as study
    from jv3.utils import is_consenting_study2
    stop_users = User.objects.filter(email__in=study.GLOBAL_STOP)
    good_event_ids = [x[0] for x in Event.objects.all().exclude(owner__in=stop_users).values_list("pk")]
    random.shuffle(good_event_ids)
    for e in Event.objects.filter(pk__in=good_event_ids[:n]):
        print e.entityid
    pass


h = lambda counts: r.hist(apply(r.c, counts),breaks=r.c(r.seq(0,50,1),10000),plot=False )

def mode(counts):
    cts = {}
    [cts.update({k:cts.get(k,0)+1}) for k in counts]
    v = cts.items()
    v.sort(key=lambda x:x[1],reverse=True)
    return v[0][0]

def s(counts):
    print "min:%g max:%g mode:%g mean:%g median:%g var:%g" % (min(counts),max(counts),mode(counts),mean(counts),median(counts),var(counts))
    return (min(counts),max(counts),mode(counts),mean(counts),median(counts),var(counts))

def feature_hists(keys,fvs):
    ## takes fvs and performs a stats on each of them
    import jv3.study.ca_plot as cap
    for k in keys:
        try:
            print k
            counts = [float(features[k]) for nid,features in fvs.iteritems()]
            s(counts)
            print cap.hist(counts,breaks=r.c(r.seq(min(counts)-1,50,(50-min(counts)-1)/50.0),100,250,max(500,max(counts))+1),filename='%s.png' % k,title=k)
        except ValueError,ve:
            print sys.exc_info()        



def var(v):
    ev = mean(v)
    return sum([(x-ev)**2 for x in v ])/(1.0*len(v)-1)

def f2dt_factors(features,keys=None):
    # compute keys (if we don't have them already)
    ktype = {}
    import sys
    for row in features:
        keys = reduce( lambda x,y: x.union(y), [ set([k]) for k in row.keys() ])
        [ ktype.update( { k : type(v) } ) for k,v in row.items() ]

        
    dtdict = {} # to become the datatable
    for k in keys:
        dtdict[k] = []
        blank_item = q(ktype[k] == str, '<blank>', 0)
        for row in features:
            dtdict[k].append( row.get(k, blank_item ) )
        dtdict[k] = q(ktype[k] in [int,float], c(dtdict[k]), r.factor(c(dtdict[k])))
        print (k,q(ktype[k] in [int,float], 'regular','factor'))

    return r["data.frame"](r.list(**dtdict))

def _convert_to_float(t):
    try:
        return float(t)
    except:
        #print sys.exc_info()
        pass
    return 0.0

def f2dt_float(features,keys=None,missing_fillin=0):
    # turns a feature vector into an r list, 
    for row in features:
        keys = reduce( lambda x,y: x.union(y), [ set([k]) for k in row.keys() ])
    dtdict = {} # to become the datatable
    for k in keys:
        dtdict[k] = []
        for row in features:
            dtdict[k].append( _convert_to_float(row.get(k, missing_fillin)) )
        dtdict[k] = c(dtdict[k])
    return r["data.frame"](r.list(**dtdict))

