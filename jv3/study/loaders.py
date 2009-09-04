
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
from loaders import *

# reconstitute
recon = lambda n,d : [d[x] for x in n.keys()]

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
    

sigscroll_count_cache = {}
sigscroll_duration = lambda prev_count,ssevt: prev_count + ssevt["exitTime"] - ssevt["entryTime"]
sigscroll_count = lambda prev_count,ssevt: prev_count + 1

def sigscroll_reads(note,aggregation=sigscroll_count):
    print note.jid
    if sigscroll_count_cache.has_key(note.owner.id):
        return sigscroll_count_cache[note.owner.id].get(note.jid,0)

    print "computing sigscroll reads for user %s " % repr(note.owner)

    new_cache = {}
    for al in ActivityLog.objects.filter(action="significant-scroll",owner=note.owner):
        if al.search is None:
            continue
        for nv in JSONDecoder().decode(al.search)["note_visibilities"]:
            nvid = int(nv["id"])
            new_cache[nvid] = aggregation(new_cache.get(nvid,0),nv)

    global sigscroll_count_cache

    sigscroll_count_cache[note.owner.id] = new_cache

    return sigscroll_count_cache[note.owner.id].get(note.jid,0)


