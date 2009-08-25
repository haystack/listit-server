
import nltk
from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
from jv3.study.study import non_stop_consenting_users,non_stop_users
from jv3.study.exporter import activity_logs_for_note
from jv3.utils import current_time_decimal
from django.utils.simplejson import JSONEncoder, JSONDecoder
from rpy2 import robjects
import random
import sys

def random_notes_slow(n=1000,consenting=True):
    """ returns random subset of notes """
    if consenting:
        users = non_stop_consenting_users()
    else:
        users = non_stop_users()
        
    results = []
    keys = []
    notes = Note.objects.filter(owner__in=users)
    i = 0
    while len(results) < n and i < n+10000:
        note = notes[random.randint(0,notes.count()-1)]
        if note.id not in keys:
            keys.append(note.id)
            results.append(note)            
        i = i + 1
        print "%d " % len(results)
    return results

def random_notes(n=20000,created_before=None):
    results = []
    keys = []
    
    if created_before is None:
        notes = Note.objects.all()
    else:
        notes = Note.objects.filter(created__lte=created_before)
        
    count = notes.count()
    i = 0
    while len(results) < n and i < n+10000:
        note = notes[random.randint(0,count-1)]
        if note.id not in keys:
            keys.append(note.id)
            results.append(note)            
        i = i + 1
        #print "%g " % (len(results)*1.0/n)
    return results

all_pass = lambda x: True
striplow = lambda x: x.strip().lower()
stopword_low = [striplow(x) for x in stopwords.words()]
stopword = lambda x: x not in stopword_low

def update_dictionary(words,dictionary):
    # takes words
    for w in words:
        dictionary[w] = dictionary.get(w,0) + 1
    pass

def to_feature_vec(tokens,wordlist):
    fv = {}
    for t in tokens:
        if t in wordlist:
            idx = wordlist.index(t)
            fv[idx] = fv.get(idx,0)+1

    return fv

def vectify(notes, text=lambda x: x.contents, word_proc=striplow, word_filter=all_pass, lexicon=None, min_word_freq=2):
    tokenizer = WordTokenizer()
    notewords = lambda x : [ word_proc(x) for x in tokenizer.tokenize(n.contents) if word_filter(x) ]
    tokenized = [ notewords(n) for n in notes ]
    dictionary = {}    
    if lexicon is None:
        ## build lexicon, otherwise use dictionary passed in
        [ update_dictionary(tn,dictionary) for tn in tokenized ] 
        lexicon = [k for k in dictionary.keys() if dictionary[k] > min_word_freq]
        lexicon.sort(lambda x,y : dictionary[y] - dictionary[x])

    return lexicon,[to_feature_vec(tn,lexicon) for tn in tokenized],dictionary
    
# reconstitute
recon = lambda n,d : [d[x] for x in n.keys()]

# lm 

r = robjects.r

## context predictors 
lifetime_context = lambda x : [ float(current_time_decimal() - x.created)/1000.0 ]
lifetime_length_context = lambda x : [ float(current_time_decimal() - x.created)/1000.0, len(x.contents) ]
num_edits = lambda(note) : int(repr(activity_logs_for_note(note).count()))
sigscroll_count_cache = {}
sigscroll_duration = lambda prev_count,ssevt: prev_count + ssevt["exitTime"] - ssevt["entryTime"]
sigscroll_count = lambda prev_count,ssevt: prev_count + 1

def sigscroll_reads(note,aggregation=sigscroll_count):
   
    if sigscroll_cache.has_key(note.id):
        return sigscroll_cache[note.id]

    print "computing sigscroll reads for user %s " % repr(note.owner)

    new_cache = {}
    for al in ActivityLog.objects.filter(action="significant-scroll",owner=note.owner):
        for nv in JSONDecoder().decode(al.search)["note-visibilities"]:
            nvid = nv["id"]
            new_cache[nvid] = aggregation(new_cache.get(nvid,0),nv)

    global sigscroll_count_cache
    
    for k,v in new_cache.iteritems():
        sigscroll_count_cache[k] = v

    return sigscroll_count_cache[note.id]



def lm(notes=None,min_word_freq=3,labeler=num_edits,context_fn=lifetime_length_context,min_content_features_per_note=1,lexicon=None):

    if notes is None:
        full_notes = random_notes()

    terms,fvs,dicts = vectify(full_notes,min_word_freq=min_word_freq,lexicon=lexicon)
    filtered_notes = []
    filtered_fvs = []

    print "# of notes/fvs %d %d " % (len(full_notes),len(fvs))

    filtered_combo = [ (full_notes[ii],fvs[ii]) for ii in range(len(full_notes)) if len(fvs[ii]) > min_content_features_per_note ]

    notes = [ fc[0] for fc in filtered_combo ]
    fvs = [ fc[1] for fc in filtered_combo ]    

    print "reduced to %s " % len(fvs)
    print "terms(%d) : %s " % (len(terms),repr(terms))
    
    labels = apply(r.c, [labeler(n) for n in notes])    
    content_dim = len(terms)

    # final thing to return
    predictors = r.c()

    context_dim = 0

    for n_i in range(len(notes)):
        fv = fvs[n_i]
        note = notes[n_i]

        context_row = context_fn(note)
        context_dim = len(context_row)

        ## content features
        content_row=r.rep(0,times=content_dim)
        print fv
        for k,v in fv.iteritems():
            content_row[k]=v
        predictors = r.c(predictors,apply(r.c, context_row),content_row)

    ## reshape into a matrix plz
    mpredictors = r.t(r.matrix(predictors,ncol=len(notes),nrow=content_dim+context_dim))

    print mpredictors
    print labels

    fmla = robjects.Formula('yo ~ xo')
    fmla.environment['xo'] = mpredictors
    fmla.environment['yo'] = labels
    
    print "type of predicts %s " % repr(type( fmla.environment['xo'] ))
    print "type of labels %s " % repr(type( fmla.environment['yo'] ))
    
    result = None
    try :
        result = r.lm(fmla)
        print(r.summary(result))
    except :
        sys.exc_info();

    for ii in range(content_dim):
        print "%s:%g" % (terms[ii],r.coefficients(result)[ii+context_dim+1])
    
    return full_notes,notes,terms,labels,mpredictors,result
    
    
    
    


