
import nltk
from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
from jv3.study.study import non_stop_consenting_users,non_stop_users
from jv3.study.exporter import str_n_urls
from jv3.utils import current_time_decimal,is_tutorial_note
from django.utils.simplejson import JSONEncoder, JSONDecoder
from rpy2 import robjects as ro
import nltk.cluster as cluster
r = ro.r
import jv3
import random,sys,re
import numpy

# ternary
q=lambda a,b,c: (b,c)[not a]

# lm 
r = ro.r

## PREPROCESSING ##################################################
## tokeniz
all_pass = lambda x: True
striplow = lambda x: x.strip().lower()
stopword_low = [striplow(x) for x in stopwords.words()]
stopword = lambda x: x not in stopword_low

_notes_to_values = lambda note: note.values('id','owner','contents',"jid","created","deleted","edited")
_actlogs_to_values = lambda actlog: actlog.values("id","action","owner","when","client","noteid","search","noteText")

eliminate_urls = lambda s: " ".join(re.compile("http://[^\s]*").split(s))

def activity_logs_for_note(n,action="note-edit",days_ago=None):
    import datetime
    if days_ago is None:
        alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"]))
        print ' returning %d ' % len(alv)
        return alv
    else:
        today_msec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        print "actlogs starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
        alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"],when__gt=n_days_ago))
        print ' returning %d ' % len(alv)
        return alv

def activity_logs_for_user(user,action="note-edit",days_ago=None):
    import datetime
    if days_ago is None:
        return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user))
    else:
        today_msec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        print "starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
        return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user,when__gt=n_days_ago))

def random_notes(n=1000,consenting=True):
    if consenting:
        users = non_stop_consenting_users()
    else:
        users = non_stop_users()
    good_ids = [x[0] for x in Note.objects.filter(owner__in=users).values_list("pk","jid","contents") if x[1] >= 0 and not is_tutorial_note(x[2])]
    random.shuffle(good_ids)
    notes = Note.objects.filter(pk__in=good_ids[:n])
    print "returning %d notes " % len(notes)
    return _notes_to_values(notes)

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

note_lifetime = lambda note : {'note_lifetime_s': float((q(note["deleted"],long(note["edited"]),current_time_decimal()) - long(note["created"]))/1000.0)}
note_owner = lambda note: {'note_owner': repr(note["owner"])}
note_length = lambda x : {'note_length':len(x["contents"])}
note_words = lambda x : {'note_words':len(nltk.word_tokenize(eliminate_urls(x["contents"])))}
note_edits = lambda(note) : {'note_edits':len(activity_logs_for_note(note,"note-edit"))}
note_did_edit = lambda(note) : {'note_did_edit': note_edits(note) > 0}
note_deleted = lambda(note) : {'note_deleted': q(note["deleted"],True,False)}
note_urls = lambda note: {'note_urls': str_n_urls(note["contents"])}

def note_pos_features(note):
    POS = ["CC","CD","DT","EX","FW","IN","JJ","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
    counts = dict([ (x, 0) for x in POS ])
    for k,pos in nltk.pos_tag(nltk.word_tokenize(note["contents"])):
        if pos in POS:
            counts[pos] = counts[pos]+ 1
    return counts

_names = None
def note_names(note):
    global _names
    if _names is None:   _names = [x.lower() for x in names.read()]
    return {'names': len([ x for x in nltk.word_tokenize(note["contents"]) if x in _names ])}
    
## signifiant scroll stuff ##
sigscroll_cache_days_ago = None
sigscroll_count_cache = {}
sigscroll_dur_cache = {}
sigscroll_count = lambda prev_count,ssevt: prev_count + 1

def sigscroll_dur(prev_count,ssevt):
    if ssevt.has_key("exitTime") and ssevt.has_key("entryTime"):
        return prev_count + (ssevt["exitTime"] - ssevt["entryTime"])/60000.0
    return prev_count

def note_ss(note,days_ago=None):
    global sigscroll_cache_days_ago
    global sigscroll_count_cache
    global sigscroll_dur_cache
    
    if sigscroll_count_cache.has_key(note["owner"]) and days_ago == sigscroll_cache_days_ago:
        # cache hit, and we are reading the right data
        return {'sigscroll_counts': sigscroll_count_cache[note["owner"]].get(note["jid"],0),  'sigscroll_duration': sigscroll_dur_cache[note["owner"]].get(note["jid"],0) }
    # reset.
    if not days_ago == sigscroll_cache_days_ago:
        sigscroll_cache_days_ago = days_ago
        sigscroll_count_cache = {}
        sigscroll_dur_cache = {}        
    ## recompute!
    new_count = {}
    new_dur = {}
    for al in activity_logs_for_user(note["owner"],"significant-scroll",days_ago): 
        if al["search"] is None:
            continue
        for nv in JSONDecoder().decode(al["search"])["note_visibilities"]:
            nvid = int(nv["id"])
            new_count[nvid] = sigscroll_count(new_count.get(nvid,0),nv)
            new_dur[nvid] = sigscroll_dur(new_dur.get(nvid,0),nv)
    sigscroll_count_cache[note["owner"]] = new_count
    sigscroll_dur_cache[note["owner"]] = new_dur
    return {'sigscroll_counts': sigscroll_count_cache[note["owner"]].get(note["jid"],0),
            'sigscroll_duration': sigscroll_dur_cache[note["owner"]].get(note["jid"],0) }

## now feature compilation stuff
default_note_feature_fns = [
    note_lifetime,
    note_owner,
    note_length,
    note_words,
    note_deleted,
    note_names,
    note_urls,
    note_ss,
]

#    note_edits,


def notes_to_features(notes,include_bow_features=True,bow_parameters={},note_feature_fns=default_note_feature_fns):
    # generates feature vectors like this:
    # [ "notepkid": { "f1" : 12398 , "f2" : 102938, ... } ... ]
    lexicon = None
    lexicon_freq = None
    if include_bow_features:
        note_fvs,lexicon,lexicon_freq = notes_to_bow_features(notes,**bow_parameters)
    else:
        note_fvs = dict( [ (tn["id"],{}) for tn in notes ] )

    for n in notes:
        print "generating %s:%s " % (n["id"],n["contents"])
        [ note_fvs[n["id"]].update( ff(n) ) for ff in note_feature_fns ]

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

