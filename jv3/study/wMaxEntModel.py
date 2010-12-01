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
import jv3.study.wMaxEntFeatures as wFeatures

def getNoteCat():
    noteData = intent.reada()
    ## of form: [#, rater name, #, noteid?, notetext, 
    ## most-likely-category, #- descword ** 5 for each cat]
    ## noteData[2] = user.id, noteData[3] = note.jid
    ## Specifically: noteData[4] => note text
    ## noteData[5] => highest rated category    
    return noteData

def get_unique_cat():
    ## Filters out multiple user ratings for same note
    uniqueNotes = []
    userDict = {}
    noteData = intent.reada()
    for item in noteData:
        if item[2] in userDict.keys():
            noteDict = userDict[item[2]]
            if item[3] not in noteDict.keys():
                userDict[item[3]] = True
                uniqueNotes.append(item)
        else: ## user doesn't have his own dict!
            userDict[item[2]] = {item[3]:True}
            uniqueNotes.append(item)
    return uniqueNotes


def splitNotes(category):
    getOwner = lambda x : User.objects.filter(id=x)[0] # turns id into owner
    noteData = get_unique_cat()
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


nvals = lambda note : tfigs.n2vals(note)
pos_word     = lambda word: nltk.pos_tag([word])[0][1]

def pos_word(word):
    return nltk.pos_tag([word])[0][1]

def word_is_verb(word):
    return pos_word(word) in ["VB","VBD","VBG","VBN","VBP","VBZ"]

def word_is_noun(word):
    return pos_word(word) in ["NN","NNS","NNP","NNPS"]

try:
    mem = mem
except:
    mem, notMem = splitNotes('memory trigger')

try:
    ref = ref
except:
    ref, notRef = splitNotes('reference')

mapping = {}
labels = ['memory trigger', 'not']

def addFeature(featureset, fname, fval):
    global mapping, labels
    featureset[fname] = fval
    if (fname, fval, labels[0]) not in mapping:
        for label in labels:
            mapping[(fname,fval,label)]=len(mapping)

reload(wFeatures)

def noteFeatures(note):
    notevals = nvals(note)
    fs = {}
    noteWords = nltk.word_tokenize(note.contents)
    for feature in wFeatures.features:
        fname, fval = feature(notevals, noteWords)
        addFeature(fs, fname, fval)
#    for word in noteWords:
#        if wFeatures.word_is_verb(word) or word in wFeatures.stopWords:
#            addFeature(fs, 'contains-word', word)
#    for i in range(len(noteWords)-1): ## Bigrams?
#        addFeature(fs, "w1:%s"%(noteWords[i]), "w2:%s"%(noteWords[i+1]))
#    for word in noteWords:
#        if wFeatures.word_is_verb(word):
#            addFeature(fs, "contains-word", word)
    return fs

def createTokens(notesA, labelA, notesB, labelB):
    posTokens = [(noteFeatures(note), labelA) for note in notesA]
    negTokens = [(noteFeatures(note), labelB) for note in notesB]
    return (posTokens, negTokens)

def createMemTokens():
    mem, notMem = splitNotes('memory trigger')
    return createTokens(mem, 'memory trigger', notMem, 'not')

def createRefTokens():
    ref, notRef = splitNotes('reference')
    return createTokens(ref, 'reference', notRef, 'not')

## Split pos/neg tokens into training set, and pos/neg test set
def splitTokens(posArray, negArray):
    import random as rr
    rr.shuffle(posArray)
    rr.shuffle(negArray)
    pos_train = posArray[:len(posArray)/2]
    pos_test = posArray[len(posArray)/2:]
    neg_train = negArray[:len(negArray)/2]
    neg_test = negArray[len(negArray)/2:]
    training_set = pos_train
    training_set.extend(neg_train)
    return (training_set, pos_test, neg_test)

posTokens, negTokens = createTokens(mem, 'memory trigger', notMem, 'not')  ##createMemTokens()
train_toks, posTest, negTest = splitTokens(posTokens, negTokens)

def getTrainingSet(posTokens, negTokens, count=4):
    training_set = []
    for i in range(count):
        training_set.append(splitTokens(posTokens,negTokens))
    return training_set

training_set = getTrainingSet(posTokens, negTokens, 15)
                           
#mapping = {}
#labels = ['reference', 'not']
#posRefTokens, negRefTokens = createTokens(ref, "reference", notRef, 'not')
#ref_train_toks, ref_posTest, ref_negTest = splitTokens(posRefTokens, negRefTokens)

#BMFE = nltk.BinaryMaxentFeatureEncoding(labels=labels,mapping=mapping)
#         Final          -0.43248        0.823
#Accuracy with mem trig & not mem trig = 0.879746835443 & 0.581081081081

#BMFE = nltk.BinaryMaxentFeatureEncoding.train(train_toks, count_cutoff=30)
#         Final          -0.52425        0.786            cutoff = 5
#Accuracy with mem trig & not mem trig = 0.918238993711 & 0.598765432099
#         Final          -0.55326        0.770            cutoff = 7
#Accuracy with mem trig & not mem trig = 0.895705521472 & 0.662162162162

#         Final          -0.56169        0.771            cutoff = 8
#Accuracy with mem trig & not mem trig = 0.867088607595 & 0.675675675676
#         Final          -0.55172        0.781
#Accuracy with mem trig & not mem trig = 0.917721518987 & 0.635294117647


#         Final          -0.56095        0.786            cutoff = 9
#Accuracy with mem trig & not mem trig = 0.83606557377 & 0.695945945946
#         Final          -0.56272        0.784
#Accuracy with mem trig & not mem trig = 0.867088607595 & 0.655405405405

#         Final          -0.56354        0.777            cutoff = 10
#Accuracy with mem trig & not mem trig = 0.89880952381 & 0.628378378378
#         Final          -0.53255        0.797
#Accuracy with mem trig & not mem trig = 0.911392405063 & 0.581081081081

#         Final          -0.55300        0.770            cutoff = 15
#Accuracy with mem trig & not mem trig = 0.925465838509 & 0.566037735849

#model = nltk.MaxentClassifier.train(train_toks,encoding=BMFE,labels=labels,max_iter=5)

#mAcc = nltk.classify.util.accuracy(model, posTest)#[(noteFeatures(nn),'memory trigger') for nn in posTest])
#nmAcc = nltk.classify.util.accuracy(model, negTest)#[(noteFeatures(nn),'not') for nn in negTest])
#print("Accuracy with mem trig & not mem trig = %s & %s" % (mAcc,  nmAcc))

def buildModel(train_toks, posTest, negTest, count_cutoff=0):
    BMFE = nltk.BinaryMaxentFeatureEncoding.train(train_toks, count_cutoff)
    model = nltk.MaxentClassifier.train(train_toks,encoding=BMFE,max_iter=5)
    mAcc = nltk.classify.util.accuracy(model, posTest)#[(noteFeatures(nn),'memory trigger') for nn in posTest])
    nmAcc = nltk.classify.util.accuracy(model, negTest)#[(noteFeatures(nn),'not') for nn in negTest])
    totTest = posTest
    totTest.extend(negTest)
    totAcc = nltk.classify.util.accuracy(model, totTest)
    #print "Cutoff = %s" % (count_cutoff) 
    #print("Accuracy with category & not category trig = %s & %s" % (mAcc,  nmAcc))
    return (model, mAcc, nmAcc, totAcc)


    

def evaluateCutoffs(training_set, cutoffs):
    average = lambda x:sum(x)/len(x)
    precision = lambda tp,fp: (1.0*tp)/(tp+fp)
    recall = lambda tp,fn:(1.0*tp)/(tp+fn)
    accArray = []
    precallAverage = [] # [[Precision, Recall], ... ]
    for index,cutoff in enumerate(cutoffs):
        print "Cutoff = ", cutoff
        posAcc,negAcc, totAcc = [],[],[]
        prec = [] # Precision counts for each set in training_set
        rec = []  # Recall counts for each set...
        for train_toks, posTest, negTest in training_set:
            model, mAcc, nmAcc, tAcc = buildModel(train_toks,posTest,negTest,cutoff)
            posAcc.append(mAcc)
            negAcc.append(nmAcc)
            totAcc.append(tAcc)
            tp, fp = mAcc, 1-nmAcc
            fn, tn = 1-mAcc, nmAcc
            prec.append(precision(tp,fp))
            rec.append(recall(tp,fn))
            pass
        accArray.append([average(posAcc), average(negAcc), average(totAcc)])
        precallAverage.append([average(prec), average(rec)])
        pass
    for i, acc in enumerate(accArray):
        print "Cutoff = %s => Average accuracy pos=%s, neg=%s, tot=%s"%(cutoffs[i],acc[0],acc[1],acc[2])
        print "Precision: %s, Recall: %s"%(precallAverage[i][0],precallAverage[i][1]) 
        print "F1 Score: %s"%(2.0*precallAverage[i][0]*precallAverage[i][1]/(precallAverage[i][0]+precallAverage[i][1]))
        print "--------------------------------------"



evaluateCutoffs(training_set, [0,4])

#print "Category: Memory Trigger"
#modelA = buildModel(train_toks, posTest, negTest, 0)
#modelB = buildModel(train_toks, posTest, negTest, 2)
#modelC = buildModel(train_toks, posTest, negTest, 9)
#modelD = buildModel(train_toks, posTest, negTest, 15)

#print "Category: Reference"
#rModel = buildModel(ref_train_toks, ref_posTest, ref_negTest, 9)

print "\x07"
      
dummyvar = input("Next?")
modelB = buildModel(train_toks, posTest, negTest, 0)
modelB[0].show_most_informative_features(n=40, show='neg')
modelB[0].show_most_informative_features(n=40, show='pos')


def judgeFeature(func, mem, notMem):
    posNeg= [[],[]]
    for mNote in mem:
        notevals = nvals(mNote)
        noteWords = nltk.word_tokenize(mNote.contents)
        posNeg[0].append(func(notevals, noteWords)[1])
    for nNote in notMem:
        notevals = nvals(nNote)
        noteWords = nltk.word_tokenize(nNote.contents)
        posNeg[1].append(func(notevals, noteWords)[1])
    print sum(posNeg[0]), " / ", sum(posNeg[1])
    try:
        print "High = describes mem notes more: ", sum(posNeg[0]) / (1.0*sum(posNeg[1]))
    except:
        print "Oops"
    
def judgeAllFeatures():
    for feat in wFeatures.features:
        judgeFeature(feat, mem, notMem)

def getListOfFirstWords(notes):
    dd = {}
    for nn in notes:
        firstWord = nltk.pos_tag([nltk.word_tokenize(nn.contents)[0]])[0]
        if firstWord[0] in dd:
            dd[firstWord[0]][1] += 1
        else:
            dd[firstWord[0]] = [firstWord[1], 1]
    rr = []    
    for key, pair in dd.items():
        rr.append((key, pair[1]))
    rr.sort(lambda x,y:cmp(x[1],y[1]))
    return rr
