## This is for Wolfe's 6.864 class project
## Design a Maximum Entropy (Log-linear model) to classify notes
## as belonging or not belonging to a particular class
## Classes: todo-reminder, reference, ext cog., journal/logging, 
## personal archival

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
import ntlk

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

def getStdMapping():
    ## Returns (mapping, weights)
    ## how to get mapping?
    
    
    
    ## Choose weights randomly
    weights = [0]*10 ## change this to how ever many features there are!


def refClassifier():
    ## Ref and nonRef thingies
    refNotes, nonRefNotes = splitNotes('reference')
    labels = ['reference', 'nonref']
    ## 
    mapping, weights = getStdMapping()
    encoding = nltk.BinaryMaxentFeatureEncoding(labels, mapping)
    maxEntModel = initMaxEntModel(encoding, weights)



## 
#In [147]: BMFE.train([({'fname0':0,'fname1':1},'ref')])
#Out[147]: <nltk.classify.maxent.BinaryMaxentFeatureEncoding object at 0x7517110>

#In [149]: BMFE.train([({'fname0':0,'fname1':1},'ref')])
#Out[149]: <nltk.classify.maxent.BinaryMaxentFeatureEncoding object at 0x7517250>

#In [151]: BMFE.labels()
#Out[151]: ['1', '2']

#In [152]: mapp = {('fname0','fval0','nonref'):0,('fname','fval','ref'):1}

#In [153]: BMFE = nltk.BinaryMaxentFeatureEncoding(['1','2'], mapp)


# mapp = {('fname0','fval0','nonref'):'nonref',('fname','fval','ref'):'ref'}
# BMFE = nltk.BinaryMaxentFeatureEncoding(labels=['ref','nonref'], mapping=mapp)
# BMFE.labels() --> Out[165]: ['ref', 'nonref']
# BMFE.train(train_toks=[({'fname0':'fval0'},"ref")])

# BMFE.labels() --> ['ref', 'nonref']
# BMFE.length() --> 2


## FEATURE SETS ## http://nltk.googlecode.com/svn/trunk/doc/api/nltk.classify-module.html
## Training Set: List of (featuredict, label) tuples !

## Feature Set: dict mapping from "feature name to feature value"

defaultMapping = {("contains-word",'email',True):0}

def note_features(note):
    featureset = {}
    ## Add questions to feature set like:
    for word in note.contents.split(' '):
        featureset["contains-word(%s)" % word] = True 
    ## more!
    return featureset


## What is mapping?:  dict like:               {(featurename, featurevalue, label):index}
## ex: featurename = contains-word(foobar)
## ex: featurevalue  = True
## ex: label = category or not...


## Training tokens: List of tuples of (feature dict,string  label)
## ie: train_toks = [({featureset}, "reference"), ... ]




