## This is for Wolfe's 6.864 class project
## Design a Maximum Entropy (Log-linear model) to classify notes
## as belonging or not belonging to a particular class
## Classes: todo-reminder, reference, ext cog., journal/logging, 
## personal archival
## FEATURE SETS ## http://nltk.googlecode.com/svn/trunk/doc/api/nltk.classify-module.html

from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
from jv3.study.ca_plot import make_filename
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
import random

import jv3.study.note_labels as nl
import jv3.study.keeping_labels as kl
import jv3.study.intention as intent
import nltk
import jv3.study.thesis_figures as tfigs

def getNoteCat():
    noteData = intent.reada()
    ## of form: [#, rater name, #, noteid?, notetext, 
    ## most-likely-category, #- descword ** 5 for each cat]
    ## noteData[2] = user.id, noteData[3] = note.jid
    ## Specifically: noteData[4] => note text
    ## noteData[5] => highest rated category    
    return noteData

def splitNotes(category):
    getOwner = lambda x : User.objects.filter(id=x)[0] # turns id into owner
    noteData = getNoteCat()
    matches = filter(lambda x:x[5]==category, noteData)
    nonMatches = filter(lambda x:x[5]!=category, noteData)
    ## Turn list of category-note data into two list of notes
    matchNotes = map(lambda x:Note.objects.filter(owner=getOwner(x[2]), jid=x[3])[0], matches)
    nonMatchNotes = map(lambda x:Note.objects.filter(owner=getOwner(x[2]), jid=x[3])[0], nonMatches)
    return (matchNotes, nonMatchNotes)

def initMaxEntModel(encoding, weights):
    maxEntModel = nltk.MaxentClassifier(encoding, weights)
    return maxEntModel

def refClassifier():
    ## Ref and nonRef thingies
    refNotes, nonRefNotes = splitNotes('reference')
    labels = ['reference', 'nonref']
    ## 
    mapping, weights = getStdMapping()
    encoding = nltk.BinaryMaxentFeatureEncoding(labels, mapping)
    maxEntModel = initMaxEntModel(encoding, weights)

def nvals(note):
    return tfigs.n2vals(note)

def word_is_verb(word):
    is_verb = False
    for qq,pos in nltk.pos_tag(word):
        if pos in ["VB","VBD","VBG","VBN","VBP","VBZ"]:
            is_verb = True
            break
    return is_verb

mem, notMem = splitNotes('memory trigger')

mapping = {}
labels = ['memory trigger', 'not']

def addFeature(featureset, fname, fval):
    global mapping, labels
    featureset[fname] = fval
    if (fname, fval, labels[0]) not in mapping:
        for label in labels:
            mapping[(fname,fval,label)]=len(mapping)

def noteFeatures(note):
    notevals = nvals(note)
    featureset = {}
    ## Add questions to feature set!
    words = nltk.word_tokenize(note.contents)
#    for word in words: ## overfitting?
        #addFeature(featureset,"contains-word(%s)"%(word), True)
    ## Note Text Content
    first_word = words[0]
    first_word_verb = word_is_verb(first_word)
    if first_word_verb:
        addFeature(featureset, "first-word-is-verb", True)
        #addFeature(featureset, "first-verb-is(%s)"%(first_word), True)
    verb_count = ca.note_verbs(notevals)['note_verbs']
    addFeature(featureset, "contains-k-verbs(%s)"%(verb_count), True)
    note_words = ca.note_words(notevals)['note_words']
    for i in range(note_words-1,note_words+2):
        addFeature(featureset, "contains-k-words(%s)"%(max(i, 0)), True)
    note_lines = ca.note_lines(notevals)['note_lines']
    addFeature(featureset, "contains-k-lines(%s)"%(note_lines), True)
    note_urls = ca.note_urls(notevals)['note_urls']
    if note_urls > 0:
        addFeature(featureset, "contains->1-urls()", True)
        addFeature(featureset, "contains-k-urls(%s)"%(note_urls), True)
    ## 80%
    numbers = ca.numbers(notevals)['numbers']
    if numbers > 0:
        addFeature(featureset, "contains->0-numbers()", True)
    symDaysofweek = "yes" if (ca.daysofweek(notevals)['daysofweek'] > 0) else "no"
    addFeature(featureset, "contains-daysofweek(%s)"%(symDaysofweek), True)
    return featureset

def createTokens(notesA, labelA, notesB, labelB):
    train_toks = [(noteFeatures(note), labelA) for note in notesA]
    [train_toks.append((noteFeatures(note), labelB)) for note in notesB]
    return train_toks

def createMemTokens():
    mem, notMem = splitNotes('memory trigger')
    return createTokens(mem, 'memory trigger', notMem, 'not')
    

train_toks = createTokens(mem, 'memory trigger', notMem, 'not')  ##createMemTokens()
tt_sample = train_toks[200:400]
tt_sample.extend(train_toks[600:800])
BMFE = nltk.BinaryMaxentFeatureEncoding(labels=labels,mapping=mapping)
model = nltk.MaxentClassifier.train(tt_sample,encoding=BMFE,labels=labels,max_iter=3)
mAcc = nltk.classify.util.accuracy(model, [(noteFeatures(nn),'memory trigger') for nn in mem[:200]])
nmAcc = nltk.classify.util.accuracy(model, [(noteFeatures(nn),'not') for nn in notMem[280:480]])
print("Accuracy with mem trig & not mem trig = %s & %s" % (mAcc,  nmAcc))

model.show_most_informative_features(n=40)
dummyvar = input("Next?")
model.show_most_informative_features(n=40, show='pos')




