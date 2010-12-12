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
import jv3.study.wMaxEntUtils as wmU

from threading import Thread

average = lambda x:sum(x)/len(x)
precision = lambda tp,fp: (1.0*tp)/(tp+fp) ## Pos Predictive Value
recall = lambda tp,fn:(1.0*tp)/(tp+fn)     ## Sensitivity
negPred = lambda tn, fn: (1.0*tn)/(tn+fn)
specificity = lambda tn,fp: (1.0*tn)/(tn+fp)


class testmodel(Thread):
    def __init__(self, train_toks, posTest, negTest, count_cutoff):
        Thread.__init__(self)
        self.done = False
        self.train_toks = train_toks
        self.posTest = posTest
        self.negTest = negTest
        self.count_cutoff = count_cutoff
    def getStats(self):
        return [self.model, self.mAcc, self.nmAcc, self.tAcc]
    def run(self):
        ## What you want thread to do
        model,mAcc,nmAcc,tAcc = buildModel(self.train_toks, self.posTest, self.negTest, self.count_cutoff)
        self.model = model
        self.mAcc = mAcc
        self.nmAcc = nmAcc
        self.tAcc = tAcc
        self.done = True

"""
def splitNotes(category):
    getOwner = lambda x : User.objects.filter(id=x)[0] # turns id into owner
    ratData = get_unique_cat()
    #noteData = intent.eliminate_duplicate_ratings_of_the_same_note_by_the_same_coder(intent.reada())
#    ratData = intent.reada()
    matches = filter(lambda x:x[5]==category, ratData)
    nonMatches = filter(lambda x:x[5]!=category, ratData)
    ## Turn list of category-note data into two list of notes
    matchNotes = map(lambda x:Note.objects.filter(id=x[0])[0], matches)
    nonMatchNotes = map(lambda x:Note.objects.filter(id=x[0])[0], nonMatches)
    uMatches = []
    uNonMatches = []
    nmDict = {}
    for note in nonMatchNotes: # 262
        if note.id not in nmDict and note not in matchNotes:# and note not in uMatches:
            uNonMatches.append(note)
            nmDict[note.id] = True
    mDict = {}
    for note in matchNotes: # 282
        if note.id not in mDict:# and note not in nonMatchNotes:# 206
            uMatches.append(note)
            mDict[note.id] = True
    return (uMatches, uNonMatches)
"""
def splitNotes(category):
    uniqueRatings = {} # k,v = noteid,rating -- get only 1 rating of each note
    allRatings = intent.reada()
    approvedRaters = ['Darren','emax','Wolfe','WolfePriOnly', 'Sling Lynch']#'Matt']#,'darren','Ali']
    for rating in filter(lambda x: x[1] in approvedRaters,allRatings):
        if rating[0] not in uniqueRatings:
            ndt[note[0]] = rating
    cat,notCat = [], []
    for k,v in uniqueRatings.items(): ## k = noteid, v=rating
        if v[5] == category:
            cat.append(Note.objects.filter(id=k)[0])
        else:
            notCat.append(Note.objects.filter(id=k)[0])
    return (cat, notCat)

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
pos_word = lambda word: nltk.pos_tag([word])[0][1]

def pos_word(word):
    return nltk.pos_tag([word])[0][1]

def word_is_verb(word):
    return pos_word(word) in ["VB","VBD","VBG","VBN","VBP","VBZ"]

def word_is_noun(word):
    return pos_word(word) in ["NN","NNS","NNP","NNPS"]

try:
    mem = mem
    if mem == None:
        print "Recreating mem trig notes"
        mem, notMem = splitNotes('memory trigger')
except:
    print "Creating mem trig notes"
    mem, notMem = splitNotes('memory trigger')

#try:
#    allWordDict = allWordDict
#except:
#    allWordDict = {}
#    for note in mem:
#        for word in nltk.word_tokenize(note.contents):
#            if word not in allWordDict:
#                allWordDict[word] = [0,0]
#            allWordDict[word][0] += 1
#    for note in notMem:
#        for word in nltk.word_tokenize(note.contents):
#            if word not in allWordDict:
#                allWordDict[word]=[0,0]
#            allWordDict[word][1] += 1

try:
    ref = ref
except:
    ref, notRef = splitNotes('reference')

mapping = {}
labels = ['memory trigger', 'not']

def addFeature(featureset, fname, fval):
    #global mapping, labels
    featureset[fname] = fval
    if (fname, fval, labels[0]) not in mapping:
        for label in labels:
            mapping[(fname,fval,label)]=len(mapping)

reload(wFeatures)
first_nonsymb_word_line = lambda txt: re.findall('^[^\w]*(\w+)', txt, re.MULTILINE)

def noteFeatures(note):
    global mem, notMem
    notevals = nvals(note)
    fs = {}
    noteWords = nltk.tokenize.WordPunctTokenizer().tokenize(note.contents)
    notePOS = nltk.pos_tag(noteWords)
    for feature in wFeatures.features:
        fname, fval = feature(notevals, noteWords)
#        if fval != False:
        addFeature(fs, fname, fval)
        pass
    ## SILLY SILLY SILLY 
    goodChars = {u'\t': [1, 9],
                 u'\n': [132, 275],
                 u' ': [1509, 2392],
                 u'&': [3, 42],
                 u'*': [4, 18],
                 u',': [32, 132],
                 u'-': [77, 238],
                 u'.': [121, 486],
                 u'/': [78, 541],
                 u'0': [56, 249],
                 u'1': [64, 166],
                 u'2': [50, 174],
                 u'3': [39, 116],
                 u'4': [28, 108],
                 u'5': [33, 106],
                 u'6': [25, 80],
                 u'7': [16, 85],
                 u'8': [29, 90],
                 u'9': [22, 107],
                 u':': [65, 167],
                 u'=': [0, 47],
                 u'P': [26, 66],
                 u'Q': [0, 27],
                 u'\\': [0, 5],
                 u'|': [1, 34]}
    """ GOOD REMOVAL !!!
                 u'a': [613, 1097],
                 u'b': [135, 252],
                 u'c': [300, 568],
                 u'd': [275, 569],
                 u'e': [924, 1743],
                 u'f': [156, 282],
                 u'g': [156, 356],
                 u'h': [253, 664],
                 u'i': [524, 1050],
                 u'l': [346, 674],
                 u'm': [233, 472],
                 u'n': [558, 977],
                 u'o': [659, 1223],
                 u'p': [193, 429],
                 u'r': [542, 991],
                 u's': [462, 1013],
                 u't': [690, 1419],
                 u'u': [217, 508],
                 u'v': [79, 195],
                 u'w': [156, 421],
                 u'x': [39, 54],
                 u'y': [115, 271],
                 u'|': [1, 34]}
    """
    seenChars = {}
    for char in note.contents:
        if char not in seenChars and char in goodChars:
            seenChars[char] = True
            addFeature(fs, "CHAR: %s"%(char), True)
    ## First-word-in-line feature
    """
    seenWords = {}
    goodWords = {'http':True,'get':True,'1':True,'to':True,'order':True,'need':True,'send':True,'the':True}
    for word in noteWords:#first_nonsymb_word_line(note.contents):
        word = word.lower() ## map all words to lowercase words
        if word not in seenWords:
            seenWords[word] = 0
            addFeature(fs, "HAS: %s"%(word), True)
        seenWords[word] += 1
        pass
    """
    ## look for any line with a DT leading it
    # First Word
    #if len(notePOS) != 0:
    #    addFeature(fs, "1st_word: %s"%(notePOS[0][0]),True)
    #    addFeature(fs, "1st_pos: notePOS[0][1], True)
    bestBigrams = [('IN', 'NN'),
                   (':', 'JJ'),
                   (':', 'NNP'),
                   (':', '-NONE-'),
                   (':', 'DT'),
                   ('NN', 'NN'),
                   ('NNS', ','),
                   ('DT', 'NN'),
                   ('NN', 'IN'),
                   ('START', 'NNP'),
                   ('NNP', ':'),
                   ('JJ', 'NN'),
                   ('NN', 'NNP'),
                   ('IN', 'NNP'),
                   ('NN', ':'),
                   ('VBP', 'JJ'),
                   ('NNP', 'IN'),
                   ('CD', 'NNS'),
                   ('NN', 'NNS')]
#    goodPOSUG = ['IN','NNP',':','JJ','#']#,'VBN','VB',',']
    goodPOSUG = [',','VBP','JJ','VBZ','#','NN','TO',':','NNP','VB','CC','-NONE-','IN']
    posUG = {}
    posBG, prevTok = {}, ('','START') 
    ## Calculate bigram features
    for posTok in nltk.pos_tag(noteWords):
        ## Unigrams
        if posTok[1] not in posUG and posTok[1] in goodPOSUG:
            posUG[posTok[1]] = True
            addFeature(fs, "1G_POS_%s"%(posTok[1]), True)
        ## Bigrams
        if (prevTok[1],posTok[1]) not in bestBigrams:
            prevTok = posTok
            continue
        if (prevTok[1],posTok[1]) not in posBG:
            posBG[(prevTok[1],posTok[1])] = True
            addFeature(fs, "2G_POS_%s_%s"%(prevTok[1], posTok[1]), True)
        pass
    goodPOSTrigrams = [(':', 'JJ', '.'), ('.', 'NN', ':'), ('JJ', '.', 'NN'), ('NN', ':', 'CD'),
                       ('NN', 'IN', 'NNP'), ('START', 'NN', ':'), (':', 'NN', ':'), ('NNP', 'NNP', 'NNP'),
                        ('NN', 'NNP', 'NNP'), ('NN', 'NN', 'NN'), ('NN', ':', 'JJ'), ('START', 'NNP', 'NNP'),
                        ('START', 'NN', 'NN'), ('NN', 'NN', ':'), ('NNP', 'NNP', 'VBZ'), ('START', 'START', 'NNP')]
    ## All trigrams = bad!
    posTG, oldestPOS, oldPOS = {}, ('','START'), ('','START')
    for posTok in nltk.pos_tag(noteWords):
        if (oldestPOS[1],oldPOS[1],posTok[1]) not in posTG and (oldestPOS[1],oldPOS[1],posTok[1]) in goodPOSTrigrams:
            posTG[(oldestPOS[1],oldPOS[1],posTok[1])] = True
            addFeature(fs, "3G_POS_%s_%s_%s"%(oldestPOS[1],oldPOS[1],posTok[1]), True)
        oldestPOS, oldPOS = oldPOS, posTok
    
### POS TRIGRAMS !!
### POS Trigrams !!
#    posTG = {}
#    prevTGB = ['','START_TAG_2']
#    prevTGA = ['','START_TAG_1#    for posTok in nltk.pos_tag(noteWords):
#        if prevTGB[1] not in posTG:
#            posTG[prevTGB[1]] = {prevTGA[1]:[posTok[1]]}
#        elif prevTGA[1] not in posTG[prevTGB[1]]:
#            posTG[prevTGB[1]][prevTGA[1]] = [posTok[1]]
#        else:
#            posTG[prevTGB[1]][prevTGA[1]].append(posTok[1])
#        prevTGB = prevTGA
#        prevTGA = posTok
#    for firstPOS, secondPosDicts in posTG.items():
#        for secondPOS, thirdPosArr in secondPosDicts.items():
#            for thirdPOS in thirdPosArr:
#                addFeature(fs, "PTG_%s_%s_%s"%(firstPOS, secondPOS, thirdPOS),True)
    return fs

class makeTokens(Thread):
    def __init__(self, note, label):
        Thread.__init__(self)        
        self.note = note
        self.label = label
    def getStats(self):
        return [self.nf, self.label]
    def run(self):
        self.nf = noteFeatures(self.note)

def TESTcreateTokens(notesA, labelA, notesB, labelB):
    tempA, tempB = [], []
    for note in notesA:
        mTok = makeTokens(note, labelA)
        tempA.append(mTok)
        mTok.start()
    for note in notesB:
        mTok = makeTokens(note, labelB)
        tempB.append(mTok)
        mTok.start()
    posTokens, negTokens = [],[]
    for mt in tempA:
        mt.join()
        posTokens.append(mt.getStats())
    for mt in tempB:
        mt.join()
        negTokens.append(mt.getStats())
#    posTokens = [(noteFeatures(note), labelA) for note in notesA]
#    negTokens = [(noteFeatures(note), labelB) for note in notesB]
    return (posTokens, negTokens)

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
    pos_train = posArray[:80]#:int(1.0*len(posArray)/2.0)]## 1/10 => 79% f2, 77/82
    pos_test = posArray[80:180]#int(1.0*len(posArray)/2.0):]
    neg_train = negArray[:80]#:int(1.0*len(negArray)/2.0)]
    neg_test = negArray[80:180]#int(1.0*len(negArray)/2.0):]  ## 1/5th and 4/5th good!
    training_setA = pos_train
    training_setA.extend(neg_train)
    return (training_setA, pos_test, neg_test)
    #return ((training_setA, pos_test, neg_test), (training_setB, pos_train, neg_train))

posTokens, negTokens = createTokens(mem, 'memory trigger', notMem, 'not')  ##createMemTokens()
train_toks, posTest, negTest = splitTokens(posTokens, negTokens)
allTok = []
allTok.extend(train_toks)
allTok.extend(posTest)
allTok.extend(negTest)


def getTrainingSet(posTokens, negTokens, count=4):
    training_set = []
    for i in range(count):
        pairTokenSplit = splitTokens(posTokens, negTokens)
        training_set.append(pairTokenSplit)
#        training_set.append(pairTokenSplit[1])
    return training_set

training_set = getTrainingSet(posTokens, negTokens, 20)#15)

def buildModel(train_toks, posTest, negTest, count_cutoff=0):
    BMFE = nltk.BinaryMaxentFeatureEncoding.train(train_toks, count_cutoff)
    model = nltk.MaxentClassifier.train(train_toks,encoding=BMFE,max_iter=15)
    mAcc = nltk.classify.util.accuracy(model, posTest)
    nmAcc = nltk.classify.util.accuracy(model, negTest)
    totTest = []
    totTest.extend(posTest)
    totTest.extend(negTest)
    totAcc = nltk.classify.util.accuracy(model, totTest)
    #print "Cutoff = %s" % (count_cutoff)
    #print("Accuracy with category & not category trig = %s & %s" % (mAcc,  nmAcc))
    return (model, mAcc, nmAcc, totAcc)

def evaluateCutoffs(training_set, cutoffs):
    global mem, notMem
    average = lambda x:sum(x)/len(x)
    precision = lambda tp,fp: (1.0*tp)/(tp+fp) ## Pos Predictive Value
    recall = lambda tp,fn:(1.0*tp)/(tp+fn)     ## Sensitivity
    negPred = lambda tn, fn: (1.0*tn)/(tn+fn)
    specificity = lambda tn,fp: (1.0*tn)/(tn+fp)
    accArray = []
    precallAverage = [] # [[Precision, Recall], ... ]
    precallAverageB = []
    for index,cutoff in enumerate(cutoffs):
        print "Cutoff = ", cutoff
        posAcc,negAcc, totAcc = [],[],[]
        tpTOT = [] ## tp percents
        fpTOT = []
        fnTOT = []
        tnTOT = []
        prec = [] # Precision percents for each set in training_set
        rec = []  # Recall percents for each set..
        spec = []
        negP = []
        threadModels = []        
        for train_toks, posTest, negTest in training_set:
            tMod = testmodel(train_toks, posTest, negTest, cutoffs[index])
            threadModels.append(tMod)
            tMod.start()
        for tModel in threadModels:           
#        for train_toks, posTest, negTest in training_set:
            tModel.join()
            model, mAcc, nmAcc, tAcc = tModel.getStats() #tModel.model, tModel.mAcc,tModel.nmAcc,tModel.tAcc
#buildModel(train_toks,posTest,negTest,cutoff)
            posAcc.append(mAcc)
            negAcc.append(nmAcc)
            totAcc.append(tAcc)
            tp, fp = mAcc*len(mem), (1-nmAcc)*len(notMem)
            fn, tn = (1-mAcc)*len(mem), nmAcc*len(notMem)
            tpTOT.append(tp)
            fpTOT.append(fp)
            fnTOT.append(fn)
            tnTOT.append(tn)
            ## now tp,fp,fn,tn are counts
            prec.append(precision(tp,fp))
            rec.append(recall(tp,fn))
            spec.append(specificity(tn,fp))
            negP.append(negPred(tn,fn))
            pass
        accArray.append([average(posAcc), average(negAcc), average(totAcc)])
        precallAverage.append([average(prec), average(rec), average(negP),average(spec)])
        precallAverageB.append([precision(sum(tpTOT),sum(fpTOT)),recall(sum(tpTOT),sum(fnTOT)),
                                negPred(sum(tnTOT),sum(fnTOT)), specificity(sum(tnTOT),sum(fpTOT))])
        pass
    for i, acc in enumerate(accArray):
        print "Cutoff......: %s"%(cutoffs[i])
#        print "Cutoff = %s => Average accuracy pos=%s, neg=%s, tot=%s"%(cutoffs[i],acc[0],acc[1],acc[2])
        print "Precision...: %s"%(precallAverageB[i][0])
        print "Recall......: %s"%(precallAverageB[i][1])
        print "True Neg....: %s"%(precallAverageB[i][2])
        print "Specificity.: %s"%(precallAverageB[i][3])
        print "F1 Score....: %s"%(2.0*precallAverage[i][0]*precallAverage[i][1]/(precallAverage[i][0]+precallAverage[i][1]))
        print "--------------------------------------"



evaluateCutoffs(training_set, [0])


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
modelB[0].show_most_informative_features(n=60, show='neg')
modelB[0].show_most_informative_features(n=60, show='pos')
NB = nltk.NaiveBayesClassifier.train(allTok)
#NB.show_most_informative_features(n=100)


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
        return  sum(posNeg[0]) / (1.0*sum(posNeg[1]))
    except:
        return -1
    
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

def test(func,a=0,b=10,step=1):
    for i in range(a,b,step):
        print i
        judgeFeature(lambda a,b:func(a,b,i),mem,notMem)





contains_and = lambda notevals, words: ("contains_&", count_re('[\&]', notevals['contents']) > 0)

#allWordDict = {}
#for note in wm.mem:
#    for word in nltk.word_tokenize(note.contents):
#        if word not in allWordDict:
#            allWordDict[word] = 0
#        allWordDict[word] += 1

#for note in wm.notMem:
#    for word in nltk.word_tokenize(note.contents):
#        if word not in allWordDict:
#            allWordDict[word] = 0
#        allWordDict[word] += 1

#allWords = [(pair[0],pair[1][0],pair[1][1]) for pair in allWordDict.items()]
        
def getParts(model):
    ## TP,FN,FP,TN
    modelParts = [[],[],[],[]]
    for note in mem:
        feat = noteFeatures(note)
        if model.classify(feat) == 'not':
            modelParts[1].append(note)
        else:
            modelParts[0].append(note)
    for note in notMem:
        feat = noteFeatures(note)
        if model.classify(feat) == 'not':
            modelParts[3].append(note)
        else:
            modelParts[2].append(note)
    return modelParts

def lookAt(parts):
    pp=parts
    for i in range(len(pp[1])):
        print pp[1][i].contents
        print '------------------------------------------------------------'
        if (i%10==0):
            time.sleep(3)



def analyzeRater(name,modelB):
    category='memory trigger'
    ndt={}
    nd=intent.reada()
    for note in filter(lambda x: x[1] == name,nd):
        if note[0] not in ndt: # noteid key, note value
            ndt[note[0]] = note
    cat, notCat = [], []
    notCat = []
    for k,v in ndt.items():
        if v[5] == category:
            cat.append(Note.objects.filter(id=v[0])[0])
        else:
            notCat.append(Note.objects.filter(id=v[0])[0])
    nfCat = [(noteFeatures(note),category) for note in cat]
    nfNot = [(noteFeatures(note),'not') for note in notCat]
    allNF = []
    allNF.extend(nfCat)
    allNF.extend(nfNot)
    totAcc = nltk.classify.util.accuracy(modelB, allNF)
    print "Total Accuracy of model at predicting", name, "'s ratings is:", totAcc
    return totAcc

"""
MaxEnt - trained on me,max,dar,matt
Wolfe:  . 85.7%
Emax:   . 82.4%
Darren: . 87.4%
Matt:   . 75.9%

Emmanuel. 66.6%
Sling Lynch: 84.1%
Ali:    . 70.3%

analyzeRater('Wolfe',wm.modelB[0]);analyzeRater('emax',wm.modelB[0]);analyzeRater('Darren',wm.modelB[0])
analyzeRater('Matt',wm.modelB[0]); analyzeRater('Sling Lynch',wm.modelB[0]);analyzeRater('Ali',wm.modelB[0])


MaxEnt - trained on me,max,Dar,Sling
Wolfe       . 83.0%, 87.7%
emax        . 82.4%, 
Darren      . 84.7%
Sling Lynch . 79.4%

Matt        . 87.6%
Ali         . 72.0%


analyzeRater('Wolfe',NB);analyzeRater('emax',NB);analyzeRater('Darren',NB)
analyzeRater('Sling Lynch',NB);analyzeRater('Matt',NB);analyzeRater('Ali',NB)

NB model:  nltk.classify.util.accuracy(wm.NB,wm.allTok) =>  0.79655172413793107

In [1143]: nltk.classify.util.accuracy(wm.NB,wm.posTest)=>  0.79473684210526319
In [1144]: nltk.classify.util.accuracy(wm.NB,wm.negTest)=>  0.97894736842105268


Wolfe       . 86.4%
emax        . 80.5%
Darren      . 86.3%
Sling Lynch . 80.3%

Matt        . 75.9%
Ali         . 77.1%



"""


