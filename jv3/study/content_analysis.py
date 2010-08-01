import nltk
from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
from jv3.utils import current_time_decimal,days_in_msecs
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
import jv3.study.ca_plot as cap
from django.db.models.query import QuerySet

DATABASE_SNAPSHOT_TIME = 1252468800000 # september 9, 2009

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
_actlogs_to_values = lambda actlog: [x for x in actlog.values("id","action","owner","when","client","noteid","search","noteText")]

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


def notes_to_bow_features(notes,
                          text=lambda x: eliminate_urls(x["contents"]),
                          word_proc=striplow, 
                          word_filter=all_pass,
                          lexicon=None,
                          lexicon_size_limit=float('Inf'),
                          min_word_freq=0):
    
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


## FEATURE COMPUTERS ##################################################################################
## given a note, returns features of that note

# values version
def note_lifetime(note):
    ndt = get_note_deletion_time(note)
    if ndt is not None and ndt > 0:
        return {'note_lifetime': ( (1.0*ndt - long(note["created"]))/(3600*1000) ) }
    return {'note_lifetime':-1}

def time_since_join(u):
    return (DATABASE_SNAPSHOT_TIME - apply(min, [x[0] for x in Note.objects.filter(owner=u).values_list("created")] ))/(24*3600*1000)

def time_of_activity(u):
    createds = [x[0] for x in Note.objects.filter(owner=u).values_list("created")]
    return (float(apply(max, createds) - apply(min, createds))) /(24.0*3600*1000)
        
#note_lifetime = lambda note : {'note_lifetime_s': float((q(note["deleted"],  long(note["edited"] - DATABASE_SNAPSHOT_TIME, -1))/1000.0)}
#nte_days_till_deletion = lambda x: {"days_till_deletion":  q(x["deleted"],int( (get_note_deletion_time(x) - x["created"])/(3600*1000.0*24) ),-1)}

#note_lifetime = lambda note : {'note_lifetime_s': float((q(note["deleted"],  long(note["edited"] - DATABASE_SNAPSHOT_TIME, -1))/1000.0)}
note_owner = lambda note: {'note_owner': repr(note["owner"])}
note_length = lambda x : {'note_length':len(x["contents"])}
#note_words = lambda x : {'note_words':len(nltk.word_tokenize(eliminate_urls(x["contents"])))}

DOWS=["mon","monday","tue","tuesday","wed","wedmesday","thu","thurs","thursday","fri","friday","sat","saturday","sun","sunday"]

MONTHS=["jan","january",
        "feb","february",
        "mar","march",
        "apr", "april",
        "may", "jun","june",
        "jul","july",
        "aug","august",
        "sep","sept",
        "september",
        "oct","october",
        "nov","november",
        "dec","december"]


make_feature = lambda k,v: {k:v}

note_words = lambda x : make_feature('note_words',len([ w for w in re.compile('\s').split(x["contents"]) if len(w.strip())>0]))
note_lines = lambda x : make_feature('note_lines',len([ w for w in re.compile('\n').split(x["contents"]) if len(w.strip())>0]))
note_words_sans_urls = lambda x : make_feature('note_words_sans_urls',note_words(x)['note_words']-note_urls(x)['note_urls'])


# note_edits = lambda(note) : make_feature('note_edits',len(activity_logs_for_note(note,"note-save")))

user_to_edits = {}
def note_changed_edits(note):
    if note["owner_id"] not in user_to_edits:
        user_to_edits[note["owner_id"]] = note_edits_for_user(User.objects.filter(id=note["owner_id"])[0])
    #print "total edits > 0 ", len([x for x in reduce(lambda x,y:x+y,user_to_edits[note["owner_id"]].values()) if x['editdist'] > 0])
    #print "total edits for user ", len([x for x in reduce(lambda x,y:x+y,user_to_edits[note["owner_id"]].values())])
    #[{"touches" : len(user_to_edits[note["owner_id"]].get(note["jid"],[])), "edits" : len([x for x in user_to_edits[note["owner_id"]].get(note["jid"],[]) if x["editdist"] > 0]) }]
    return make_feature('note_edits', len([x for x in user_to_edits[note["owner_id"]].get(note["jid"],[]) if x["editdist"] > 0]))

             
    
    
note_did_edit = lambda(note) : make_feature('note_did_edit', note_edits(note) > 0)
note_deleted = lambda(note) : make_feature('note_deleted', q(note["deleted"],True,False))
note_urls = lambda note: make_feature('note_urls', str_n_urls(note["contents"]))
note_phone_numbers = lambda x: make_feature('phone_nums',count_regex_matches("(^|\s+)([0-9]( |-)?)?(\(?[0-9]{3}\)?|[0-9]{3})( |-)?([0-9]{3}( |-)?[0-9]{4}|[a-zA-Z0-9]{7})($|\s+)",x["contents"]))
note_emails = lambda note: make_feature('email_addrs',str_n_emails(note["contents"]))
numbers = lambda note: make_feature('numbers',count_regex_matches("(^|\s+)(\d+)($|\s+)",note["contents"]))
NUMBERS=["one","two","three","four","five","six","seven","eight","nine","ten","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety","hundred"]
wordnumbers = lambda note: make_feature('wordnumbers',sum([count_regex_matches("(^|\s+)%s($|\s+)" % x,note["contents"]) for x in NUMBERS]))
daysofweek = lambda note: make_feature('daysofweek',sum([count_regex_matches("(^|\s+)%s($|\s+)" % x,note["contents"]) for x in DOWS]))
months = lambda note: make_feature('months',sum([count_regex_matches("(^|\s+)%s($|\s+)" % x,note["contents"]) for x in MONTHS]))
nonword_mix = lambda note: make_feature('numword_mix',count_regex_matches("(^|\s+)(.*\d.*)($|\s+)",note["contents"]))
note_punctuation = lambda note:make_feature('note_punct', count_regex_matches("[\.\,\'\:\;\?]", note["contents"]) )

def note_verbs(note):
    return make_feature('note_verbs', reduce(lambda x,y: x+y, [count for pos,count in note_pos_features(note).items() if pos in ["VB","VBD","VBG","VBN","VBP","VBZ"]]))    
def note_verbs_over_length(note):
    return make_feature('note_verbs_over_length', note_verbs(note)["note_verbs"]*1.0/note_words(note)["note_words"]  )
def names_over_length(note):
    return make_feature('note_names_over_length', note_names(note)["names"]*1.0/note_words(note)["note_words"]  )
def dte_over_length(note):
    return make_feature('dte_over_length', note_date_count(note)["date_time_exprs"]*1.0/note_words(note)["note_words"]  )
def urls_over_length(note):
    return make_feature('urls_over_length', note_urls(note)["note_urls"]*1.0/note_words(note)["note_words"]  )
def todos_over_length(note):
    return make_feature('todos_over_length', count_regex_matches("(^|\s|@)((todo)|(to do)|(to-do))(\s|$)",note["contents"] )*1.0/note_words(note)["note_words"] )

## addresses?
## dates/times

def note_pos_features(note):
    POS = ["CC","CD","DT","EX","FW","IN","JJ","LS","MD","NN","NNS","NNP","NNPS","PDT","POS","PRP","PRP$","RB","RBR","RBS","RP","SYM","TO","UH","VB","VBD","VBG","VBN","VBP","VBZ","WDT","WP","WP$","WRB"]
    counts = dict([ (x, 0) for x in POS ])
    for k,pos in nltk.pos_tag(nltk.word_tokenize(note["contents"])):
        if pos in POS:
            counts[pos] = counts[pos]+ 1
    return counts

def average_edit_distance(n):
    import nltk.metrics.distance as d
    edits = [ e["noteText"] for e in activity_logs_for_note(n) if e["action"] == "note-save"]  ##//ActivityLog.objects.filter(noteid=n["id"],action="note-edit").order_by("when").values_list("noteText")
    distances = []
    if len(edits) > 1:
        #print "edits: %s " % repr(edits)
        for i in range(0,len(edits)-1):
            if edits[i] is None or edits[i+1] is None:
                continue
            distances.append( d.edit_distance( edits[i], edits[i+1] ) )
        if len(distances) > 0:
            return make_feature("edit_distance",median(distances))
    return make_feature('edit_distance',MISSING)

## now feature compilation stuff

punkt =  nltk.tokenize.PunktSentenceTokenizer()
note_sentences = lambda n : make_feature( "note_sentences" , len(punkt.tokenize(n["contents"])) )

all_fns = [
    note_lifetime,
    average_edit_distance,
    note_length,
    note_words,
    note_deleted,
    note_names,
    note_urls,
    note_emails,
    note_ss,
    note_phone_numbers,
    note_date_count,
    note_changed_edits,
    note_pos_features,
    note_sentences
]

default_note_feature_fns = [
    note_phone_numbers,    
    note_lifetime,
    note_changed_edits,    
    note_words,
    note_urls,
    note_names,
    note_emails,
    note_date_count,
    note_deleted,
    note_pos_features,
    note_sentences
]

content_features = [
    note_names,
    numbers,
    nonword_mix,
    note_punctuation,
    note_words,    
    note_phone_numbers,
    note_urls,
    note_date_count,
    note_emails,
    daysofweek,
    months,
    wordnumbers,
    note_date_count
]                                                          

#    note_pos_features,

def notes_to_features(notes,include_bow_features=False,bow_parameters={},note_feature_fns=default_note_feature_fns):
    # generates feature vectors like this:
    # [ "notepkid": { "f1" : 12398 , "f2" : 102938, ... } ... ]
    lexicon = None
    lexicon_freq = None

    # preprocess notes
    if type(notes) == QuerySet: notes = _notes_to_values(notes)
    for n in notes:  n["contents"] = n["contents"].strip().lower()
    
    if include_bow_features:
        note_fvs,lexicon,lexicon_freq = notes_to_bow_features(notes,**bow_parameters)
    else:
        note_fvs = dict( [ (tn["id"],{}) for tn in notes ] )

    for n in notes:
        #print "generating %s:%s " % (n["id"],n["contents"])
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
    for row in features.values():
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

def f2dt_float(features,keys=None,missing_fillin=0):
    # one user or a bunch? 
    # turns a feature vector into an r list,
    if keys is None:
        keys = set([])
        for row in features.values():
            keys = keys.union(reduce( lambda x,y: x.union(y), [ set([k]) for k in row.keys() ]))
        
    dtdict = {} # to become the datatable
    for k in keys:
        dtdict[k] = []
        for row in features:
            dtdict[k].append( _convert_to_float(row.get(k, missing_fillin)) )
        dtdict[k] = c(dtdict[k])
    return (dtdict,r["data.frame"](r.list(**dtdict)))


def f2dt_factors_notes(keys, features):
    # compute keys (if we don't have them already)
    ktype = {}
    import sys
    
    for row in features.values():
        [ ktype.update( { k : type(v) } ) for k,v in row.items() ]
    dtdict = {} # to become the datatable
    
    for k in keys:
        dtdict[k] = []
        blank_item = q(ktype[k] == str, '<blank>', 0)
        for row in features.values():
            dtdict[k].append( row.get(k, blank_item ) )
        dtdict[k] = q(ktype[k] in [int,float], c(dtdict[k]), r.factor(c(dtdict[k])))
        print (k,q(ktype[k] in [int,float], 'regular','factor'))

    return (dtdict,r["data.frame"](r.list(**dtdict)))

def f2dt_float_notes(notesfeatures,keys,missing_fillin=0):
    # one user or a bunch? 
    # turns a feature vector into an r list,
    dtdict = {} # to become the datatable
    for k in keys:
        dtdict[k] = []
        for noteid,notefeatures in notesfeatures.iteritems():
            dtdict[k].append( _convert_to_float(notefeatures.get(k, missing_fillin)) )
        dtdict[k] = c(dtdict[k])
    return (dtdict,r["data.frame"](r.list(**dtdict)))

def _convert_to_float(t):
    try:
        return float(t)
    except:
        #print sys.exc_info()
        pass
    return 0.0

def pairwise_feature_correlation(nk,nfv):
    ff,ffr = f2dt_float_notes(nfv,nk) ## float features
    cors = []
    for k1 in ff.keys():
        for k2 in ff.keys():
            eco = r('cor.test')(ff[k1],ff[k2])
            print "comparing %s to %s : " % (k1,k2)
            cors.append( (k1,k2,eco[3][0],eco[2][0],eco[1][0],eco[0][0]) )

    return cors

def pairwise_lm(nk,nfv):
    ## debug!!
    ff,ffr = f2dt_float_notes(nfv,nk) ## float features
    cors = []
    for k1 in ff.keys():
        for k2 in ff.keys():
            eco = r('cor.test')(ff[k1],ff[k2])
            print "comparing %s to %s : " % (k1,k2)
            ro.globalEnv['x'] = 123
            ro.globalEnv['y'] = 123
            lmresult = r('lm(y~x)')
            lmsummary = r('summary(lm(y~x))')
            cors.append( (k1,k2,eco[3][0],eco[2][0],eco[1][0],eco[0][0]) )

    return cors

# reconstitute
recon = lambda n,d : [d[x] for x in n.keys()]

notes_owned = lambda oemail,notevals : [ x for x in notevals if x["owner"].email == oemail ]
notes_owned_deleted = lambda oemail,notevals : [ x for x in notevals if x["owner"].email == oemail and not x["deleted"] ]
notes_owned_not_deleted = lambda oemail,notevals : [ x for x in notevals if x["owner"].email == oemail and x["deleted"] ]

## by owner

# "active" users : who have a minimum of 15 non-stop notes (tutorial + 5)


def filter_users_for_active(users=None,users_emails=None,threshold=DATABASE_SNAPSHOT_TIME - days_in_msecs(7) ):
    if users_emails:
        users = User.objects.filter(email__in=users_emails)
    actions = ['significant-scroll','notecapture-focus','note-edit','note-save','note-add']
    active_owners = set( [ x["owner"] for x in ActivityLog.objects.filter( owner__in=users,
                                                                           action__in=actions, when__gt=threshold).values("owner") ])
    return list(User.objects.filter(id__in=active_owners))    

def get_users_who_kept_more_than_X_percent(notevals,fraction=0.8,min_notes=30):
    owners_emails = set(list([ n["owner"].email for n in notevals ]))
    owners_emails = [n.email for n in filter_users_for_active(users_emails=owners_emails)]
    o2n = [(oe,len(notes_owned(oe,notevals))) for oe in owners_emails]
    o2n = dict(filter( lambda x: x[1] >= min_notes, o2n ))
    print "len(owners_emails): %d -> %d " % (len(owners_emails),len(o2n))
    owners_emails = o2n.keys()
    return [(o,len(notes_owned(o,notevals)),(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))))
            for o in owners_emails if (1.0*len(notes_owned_not_deleted(o,notevals))/len(notes_owned(o,notevals))) >= fraction]    

def get_users_who_deleted_more_than_X_percent(notevals,fraction=0.8,min_notes=30):
    owners_emails = set(list([ n["owner"].email for n in notevals ]))
    owners_emails = [n.email for n in filter_users_for_active(users_emails=owners_emails)]
    o2n = [(oe,len(notes_owned(oe,notevals))) for oe in owners_emails]
    o2n = dict(filter( lambda x: x[1] >= min_notes, o2n ))
    print "len(owners_emails): %d -> %d " % (len(owners_emails),len(o2n))
    owners_emails = o2n.keys()
    return [(o,len(notes_owned(o,notevals)),(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))))
            for o in owners_emails if (1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))) >= fraction]    
    
def notes_per_user(notevals,filter_people_less_than_N=16):
    ## filter_notevals
    ## measures deleted and non deleted
    owners_emails = set(list([ n["owner"].email for n in notevals ]))
    owners_emails = [n.email for n in filter_users_for_active(users_emails=owners_emails)]
    o2n = [(oe,len(notes_owned(oe,notevals))) for oe in owners_emails]
    o2n = dict(filter( lambda x: x[1] > filter_people_less_than_N, o2n ))
    print "len(owners_emails): %d -> %d " % (len(owners_emails),len(o2n))
    owners_emails = o2n.keys()

    #print [(o,len(notes_owned(o,notevals)),(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals)))) for o in owners_emails if (1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))) > 0.8]
        
    return {
        "notes": [len(notes_owned(o,notevals)) for o in owners_emails],
        "deleted": [len(notes_owned_deleted(o,notevals)) for o in owners_emails],
        "notdeleted": [len(notes_owned_not_deleted(o,notevals)) for o in owners_emails],
        "percent_kept": [(1.0*len(notes_owned_not_deleted(o,notevals))/len(notes_owned(o,notevals))) for o in owners_emails],
        "percent_deleted": [(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))) for o in owners_emails]
     }

def notes_per_user_normalized(notevals,filter_people_less_than_N=16):
    ## filter_notevals
    ## measures deleted and non deleted
    owners_emails = set(list([ n["owner"].email for n in notevals ]))
    owners = filter_users_for_active(users_emails=owners_emails)
    owners_emails = [n.email for n in owners]
    o2n = [(oe,len(notes_owned(oe,notevals))) for oe in owners_emails]
    o2n = dict(filter( lambda x: x[1] > filter_people_less_than_N, o2n ))
    owners_emails = o2n.keys()

    #print [(o,len(notes_owned(o,notevals)),(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals)))) for o in owners_emails if (1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))) > 0.8]
    timeactives = dict( [ (oe, time_of_activity(User.objects.filter(email=oe)[0])) for oe in owners_emails ] )
    return {
        "notes_normalized": [len(notes_owned(o,notevals))/timeactives[o] for o in owners_emails],
        "notes": [len(notes_owned(o,notevals)) for o in owners_emails],
        "deleted": [len(notes_owned_deleted(o,notevals)) for o in owners_emails],
        "notdeleted": [len(notes_owned_not_deleted(o,notevals)) for o in owners_emails],
        "percent_kept": [(1.0*len(notes_owned_not_deleted(o,notevals))/len(notes_owned(o,notevals))) for o in owners_emails],
        "percent_deleted": [(1.0*len(notes_owned_deleted(o,notevals))/len(notes_owned(o,notevals))) for o in owners_emails]
     }



# 
def hist_notes_per_user(npu=None,breaks=[0,20,30,40,50,60,70,80,90,100,150,200,500],notevals=None):
    print "NUMBER OF OWNERS: %d " % len(npu["notes"])

    total = len(npu["notes"])
    print total
    if not npu:
        npu = notes_per_user(notevals)

    print "%%%%%%%%%%%%%%"
    print npu["percent_kept"]
    print "%%%%%%%%%%%%%%"

    cap.hist2(npu["notes"],breaks=breaks,filename="/var/www/listit-study/n.png",
              xlab="# notes",
              title="Number of notes created by users",
              ylab="Users (out of %d)" % total)              
#              ylim=r.c(0,total))
    
    cap.hist2(npu["deleted"],breaks=breaks,filename="/var/www/listit-study/n-deleted.png",
              xlab="# deleted",
              title="Number of notes deleted",
              ylab="Users (out of %d)" % total)
#              ylim=r.c(0,total))
    
    cap.hist2(npu["notdeleted"],breaks=breaks,filename="/var/www/listit-study/n-not-deleted.png",
              xlab="Number of notes kept",
              title="Number of notes kept",
              ylab="Users (out of %d)" % total)
#              ylim=r.c(0,total))
    
    cap.hist2(npu["percent_kept"],
              breaks=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0],filename="/var/www/listit-study/n-percentage-kept.png",
              xlab="% kept",
              title="Percentage of notes kept",
              ylab="Users (out of %d)" % total)              
#              ylim=r.c(0,total))
    
    cap.hist2(npu["percent_deleted"],
              breaks=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0],filename="/var/www/listit-study/n-percentage-deleted.png",
              breaklabels=["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70-80%","80-90%","90-100%"],
              xlab="% deleted",
              title="Percentage of notes deleted",
              ylab="Users (out of %d)" % total)              
#              ylim=r.c(0,total))
    
def hist_number_of_words(nfvs):
    total = len(nfvs)
    nwords = [x['note_words'] for x in nfvs.values() ]
    stats = s(nwords)
    cap.hist2( nwords,
              breaks=[0,1,5,10,20,30,40,50,100,200,500,1000,2000,5000,10000],
              filename="/var/www/listit-study/n-words.png",
              xlab="number of words",
              title="words per note [df:%d] (min:0, max:%g, mean:%g, median:%g, var:%g)" % (total-1,stats[1],stats[2],stats[3],stats[4]),
              ylab="Notes (out of %d)" % total  )
    cap.loghist( nwords,
              breaks=[0,1,5,10,20,30,40,50,100,200,500,1000,2000,5000,10000],
              filename="/var/www/listit-study/n-logwords.png",
              xlab="number of words",
              title="words per note [df:%d] (min:0, max:%g, mean:%g, median:%g, var:%g)" % (total-1,stats[1],stats[2],stats[3],stats[4]),
              ylab="Notes (out of %d)" % total  )

    
#def feature_by_owner(notevals,feature_name):
#    owners = list(set([n["owner"] for n in notevals]))
#    for o in owners:


def hist_edit_distance(nfs):
    total = len(nfs)
    ndist = [n["edit_distance"] for n in nfs.values()]
    stats = s(ndist)
    cap.loghist( ndist,
              breaks=[0,1,5,10,20,30,40,50,100,200,500,1000,10000],
              filename="/var/www/listit-study/edit-distances.png",
              xlab="edit distance (chars)",
              title="edit distance[%d] (min:0, max:%g, mean:%g, median:%g, var:%g)" % (total-1,stats[1],stats[2],stats[3],stats[4]),
              ylab="edits (out of %d)" % total  )
    
    
def hist_edits(nfs):
    total = len(nfs)
    ndist = [n["note_edits"] for n in nfs.values()]
    stats = s(ndist)
    cap.hist2( ndist,
              breaks=[0,1,5,10,20,30,40,50,100,200,500,1000,10000],
              filename="/var/www/listit-study/n-edits.png",
              xlab="# of edits per note",
              title="note edits[%d] (min:0, max:%g, mean:%g, median:%g, var:%g)" % (total-1,stats[1],stats[2],stats[3],stats[4]),
              ylab="notes (out of %d)" % total  )    
    
def show_notes(ns,nfs,ncfilter=all_pass,nffilter=all_pass,filename=None):
    wins = []
    for n in ns:
        nf = nfs[n["id"]]
        if ncfilter(n) and nffilter(nf):
            wins.append(n)

    f = None
    if filename:  f=open(filename,'a')
            
    for n in wins:
        print """============================================================"""
        print n["contents"]
        if f: f.writelines(["""\n============================================================\n""" , n["contents"]])
        
    if f:f.close()
        

## NOTE FEATURE UTILITIES
   
def subset_test(notevals,nf,nctest=all_pass,nftest=all_pass):
    test_pass = [ n for n in notevals if nctest(n) and nftest(nf[n["id"]]) ]
    pass_ids = [ n["id"] for n in test_pass ]
    return (test_pass,
            dict([ (nid,nf) for (nid,nf) in nf.items() if nid in pass_ids ]))

def subset_values(notevals,nf,key,nctest=all_pass,nftest=all_pass):
    return [nf[key] for nid,nf in subset_test(notevals,nf,nctest,nftest)[1].iteritems()]

def note_edits_for_user(u):
    import jv3.utils
    by_jid = {}
    edits_by_jid = {}
    for edit in u.activitylog_set.filter(action__in=['note-add','note-edit','note-save']).values():
        noteedits = by_jid.get(edit['noteid'],[])
        noteedits.append( edit )
        by_jid[edit['noteid']] = noteedits
    
    for jid,edits in by_jid.iteritems():
        edits.sort(key=lambda x: float(x['when']))
        converted_edits = []
        for edit in edits:
            if edit['action'] == 'note-add' : continue
#            print edit["when"]," edit: ", edit["action"], edit["noteid"],
            if edit['action'] == 'note-save' and last["action"] == 'note-edit' :
#                 if edit['noteText'] is None: print "note-save noteText is none"
#                 if last['noteText'] is None: print "note-add noteText is none"
#                print "__", jv3.utils.levenshtein(last['noteText'] if last["noteText"] is not None else "" ,edit['noteText'] if edit["noteText"] is not None else ""),
                converted_edits.append( { "when" : last["when"],
                                     "howlong": edit["when"] - last["when"],
                                     "initial": last["noteText"] if last["noteText"] is not None else "",
                                     "final": edit["noteText"] if edit["noteText"] is not None else "",
                                     "editdist": jv3.utils.levenshtein(last['noteText'] if last["noteText"] is not None else "" ,edit['noteText'] if edit["noteText"] is not None else "")
                                     })
            last = edit
        edits_by_jid[jid]=converted_edits
    return edits_by_jid
                    

        
        
    

# def kill_note_Edits():
#     from django.contrib.auth.models import User
#     kill_list_alids = []
#     errors = []
#     for u in User.objects.all():
#         user_kill = []
#         try :
#             edits_per_jid= dict([(jid,[(alid,text)])  for jid,alid,text in u.activitylog_set.filter(action="note-add").values_list('noteid','id','noteText')])
#             # we have to believe they're consecutive
#             alog_edits = u.activitylog_set.filter(action__in='note-edit').order_by('when').values_list('id','noteid','noteText')
#             for alid,jid,noteText in alog_edits:
#                 v = edits_per_jid.get(jid,[])
#                 v.append( (alid,noteText) )
#                 edits_per_jid[jid] = v
                
#             for jid,editpairs in edits_per_jid.iteritems():
#                 noteText = editpairs[0][1]
#                 for epair in editpairs[1:]:
#                     alid,newText = epair
#                     if noteText == newText:   # nothing's changed,kill
#                         user_kill.append(alid)
#                     else:
#                         noteText = newText
#                     pass
#                 pass
#             print "edits to kill for %s : %d " % (u.email,len(user_kill))
#             kill_list_alids = kill_list_alids + user_kill
#         except :
#             import traceback,sys            
#             errors.append(u)
#             print sys.exc_info()
#             traceback.print_tb(sys.exc_info()[2])
#     # ActivityLog.objects.filter(id__in=kill_list_alids).delete()

#     print "ERRORS %d : %s",(len(errors),repr(errors))
#     return kill_list_alids
                

    
