## This is for Wolfe's 6.864 class project
## Design a Maximum Entropy (Log-linear model) to classify notes
## as belonging or not belonging to a particular class
## Classes: todo-reminder, reference, ext cog., journal/logging, 
## personal archival
## FEATURE SETS ## http://nltk.googlecode.com/svn/trunk/doc/api/nltk.classify-module.html
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
#import jv3.study.content_analysis as ca
#import jv3.study.ca_datetime as cadt
#import jv3.study.ca_sigscroll as cass
#import jv3.study.ca_load as cal
#import jv3.study.ca_plot as cap
#from jv3.study.ca_plot import make_filename
#import jv3.study.ca_search as cas
#import rpy2
#import rpy2.robjects as ro
#from jv3.study.study import *
from numpy import array
import random

#import jv3.study.note_labels as nl
#import jv3.study.keeping_labels as kl
#import jv3.study.intention as intent
import nltk
#import jv3.study.thesis_figures as tfigs
import jv3.study.wolfe.wMaxEntFeatures as wFeatures
#import jv3.study.wMaxEntUtils as wmU

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
    ## -- Ali not sling used in last run !!
    approvedRaters = ['Darren','emax','Wolfe','WolfePriOnly', 'Sling Lynch']#'Matt']#,'darren','Ali']
    for rating in filter(lambda x: x[1] in approvedRaters,allRatings):
        if rating[0] not in uniqueRatings:
            uniqueRatings[rating[0]] = rating
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
    pass
    #mem = mem
    #if mem == None:
    #    print "Recreating mem trig notes"
    #    mem, notMem = splitNotes('memory trigger')
except:
    pass
    #print "Creating mem trig notes"
    #mem, notMem = splitNotes('memory trigger')

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
    noteWords = nltk.tokenize.WordPunctTokenizer().tokenize(notevals['contents'])
    notePOS = nltk.pos_tag(noteWords)
    for feature in wFeatures.features:
        fname, fval = feature(notevals, noteWords)
#        if fval != False:  ## True vs True and False values??  both seem okay?
        addFeature(fs, fname, fval)
    goodChars = {u'\t': [1, 9],#                 u'\n': [132, 275],                 u' ': [1509, 2392],
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
                 u'\\': [0, 5],
                 u'|': [1, 34]}
    """
                 u'a': [613, 1097],u'b': [135, 252],
                 u'c': [300, 568],u'd': [275, 569],u'e': [924, 1743],
                 u'f': [156, 282],u'g': [156, 356],
                 u'h': [253, 664],u'i': [524, 1050],
                 u'l': [346, 674],u'm': [233, 472],
                 u'n': [558, 977],u'o': [659, 1223],
                 u'p': [193, 429],u'r': [542, 991],
                 u's': [462, 1013],u't': [690, 1419],u'u': [217, 508],
                 u'v': [79, 195],u'w': [156, 421],
                 u'x': [39, 54],u'y': [115, 271],
                 u'|': [1, 34]}
    """
    #"""
    seenChars = {}
    seenCharBG, lastChar = {},"START"
    for char in note['contents']:
        if char not in seenChars and char in goodChars:
            seenChars[char] = True
            addFeature(fs, "CHAR: %s"%(char), True)
    #"""
    ## First-word-in-line features == GOOD
    seenWords = {}
    goodWords = {'http':True,'get':True,'1':True,'to':True,'order':True,'need':True,'send':True,'the':True}
    for word in first_nonsymb_word_line(note['contents']):
        word = word.lower() ## map all words to lowercase words
        if word not in seenWords:
            seenWords[word] = 0
            addFeature(fs, "HAS: %s"%(word), True)
        seenWords[word] += 1
        pass    
    bestBigrams = [(':', 'JJ'),
                   ('NN', 'WDT'),
                   (':', '-NONE-'),
                   (':', 'DT'),
                   ('NN', 'NN'),
                   ('NNS', ','),
                   ('PRP$', 'JJ'),
                   ('START', 'NNP'),
                   ('JJ', 'NN'),
                   ('IN', 'NNP'),
                   ('NN', ':'),
                   ('VBN', 'NN'),
                   ('VBZ', 'JJ'),
                   ('VBP', 'JJ'),
                   ('NNP', 'IN'),
                   ('CD', 'NNS'),
                   ('.', 'JJ')]
    """
    bestBigrams = [('IN', 'NN'), # 36:30
                   (':', 'JJ'),  # 17:98
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
    """
#   goodPOSUG = [',','VBP','JJ','VBZ','#','NN','TO',':','NNP','VB','CC','-NONE-','IN']
    goodPOSUG = ['#',':','JJ','NNP','IN','.']
    posUG = {}
    posBG, prevTok = {}, ('','START') 
    ## Calculate bigram features
    
    for posTok in notePOS:#nltk.pos_tag(noteWords):
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
        prevTok = posTok
        pass
    
    goodPOSTrigrams = [(':', 'JJ', '.'), ('.', 'NN', ':'), ('JJ', '.', 'NN'), ('NN', ':', 'CD'), 
                       ('START', 'NN', ':'), #('NN', 'IN', 'NNP'), ##was tried to remove
                       (':', 'NN', ':'), 
                       ('NNP', 'NNP', 'NNP'),
                       ('NN', ':', 'NNS'),
                       (':', ':', 'NN'),#
                       ('NN', 'NNP', 'NNP'),#                        ('NN', 'NN', 'NN'), ## tried to remove
                       ('NN', ':', 'JJ'),
                       ('START', 'NNP', 'NNP'),
                       ('START', 'NN', 'NN'), 
                       ('NNP', 'NN', ':'),#
                       ('DT', 'NN', 'NN'),#
                       ('NN', 'NN', ':'), 
                       ('NNP', 'NNP', ':'),#
                       ('NNP', 'NNP', 'VBZ'), 
                       ('START', 'START', 'NNP')]
    ## All trigrams = bad!, some = GOOD
    posTG, oldestPOS, oldPOS = {}, ('','START'), ('','START')
    for posTok in notePOS:#nltk.pos_tag(noteWords):
        if (oldestPOS[1],oldPOS[1],posTok[1]) not in posTG and (oldestPOS[1],oldPOS[1],posTok[1]) in goodPOSTrigrams:
            posTG[(oldestPOS[1],oldPOS[1],posTok[1])] = True
            addFeature(fs, "3G_POS_%s_%s_%s"%(oldestPOS[1],oldPOS[1],posTok[1]), True)
        oldestPOS, oldPOS = oldPOS, posTok
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
    pos_train = posArray[:90]#:int(1.0*len(posArray)/2.0)]## 1/10 => 79% f2, 77/82
    pos_test = posArray[90:180]#int(1.0*len(posArray)/2.0):]
    neg_train = negArray[:90]#:int(1.0*len(negArray)/2.0)]
    neg_test = negArray[90:180]#int(1.0*len(negArray)/2.0):]  ## 1/5th and 4/5th good!
    training_setA = pos_train
    training_setA.extend(neg_train)
    return (training_setA, pos_test, neg_test)
    #return ((training_setA, pos_test, neg_test), (training_setB, pos_train, neg_train))

"""
40, 140 split:
Precision...: 0.846010674082
Recall......: 0.869285714286
True Neg....: 0.82205702456
Specificity.: 0.792380952381
F1 Score....: 0.857957484279

50, 130 split:
Precision...: 0.844229257622
Recall......: 0.869487179487
True Neg....: 0.821747253104
Specificity.: 0.789487179487
F1 Score....: 0.857146637265

80, 100 split normal

90,90 split
Precision...: 0.852045377726
Recall......: 0.86962962963
True Neg....: 0.824170512064
Specificity.: 0.801851851852
F1 Score....: 0.861132875361


130, 50 split (train/test for each cat)
Precision...: 0.845244366098
Recall......: 0.871333333333
True Neg....: 0.824041056107
Specificity.: 0.790666666667
F1 Score....: 0.858747060289
"""

def getTrainingSet(posTokens, negTokens, count=4):
    training_set = []
    for i in range(count):
        pairTokenSplit = splitTokens(posTokens, negTokens)
        training_set.append(pairTokenSplit)
#        training_set.append(pairTokenSplit[1])
    return training_set

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
    precallAverageB = [] # Slightly different method of compiling stats
    for index,cutoff in enumerate(cutoffs):
        print "Cutoff = ", cutoff
        posAcc,negAcc, totAcc = [],[],[]
        tpTOT, fpTOT, fnTOT, tnTOT = [],[],[],[]  ## tp percents
        prec,rec,spec,negP = [],[],[],[] # Precision/... percents for each set in training_set
        threadModels = []
        for train_toks, posTest, negTest in training_set:
            tMod = testmodel(train_toks, posTest, negTest, cutoffs[index])
            threadModels.append(tMod)
            tMod.start()
        for tModel in threadModels:           
            tModel.join() ## Wait for model to finish before compiling summary statistics
            model, mAcc, nmAcc, tAcc = tModel.getStats() #tModel.model, tModel.mAcc,tModel.nmAcc,tModel.tAcc
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
        print "Precision...: %s"%(precallAverageB[i][0])
        print "Recall......: %s"%(precallAverageB[i][1])
        print "True Neg....: %s"%(precallAverageB[i][2])
        print "Specificity.: %s"%(precallAverageB[i][3])
        print "F1 Score....: %s"%(2.0*precallAverage[i][0]*precallAverage[i][1]/(precallAverage[i][0]+precallAverage[i][1]))
        print "--------------------------------------"

## Actually runs model! - top level control!
modelA = None
allTok = []

def tryModel():
    global modelA, allTok
    posTokens, negTokens = createTokens(mem, 'memory trigger', notMem, 'not')  ##createMemTokens()
    train_toks, posTest, negTest = splitTokens(posTokens, negTokens)
    allTok.extend(train_toks)
    allTok.extend(posTest)
    allTok.extend(negTest)
    training_set = getTrainingSet(posTokens, negTokens, 30)#20)#15)
    evaluateCutoffs(training_set, [0])
    ## Build specific model to look at!
    modelA = buildModel(train_toks, posTest, negTest, 0) ## last param = cutoff
    print "\x07"

def inspectModel():
    global modelA
    if modelA == None:
        return
    modelA[0].show_most_informative_features(n=60, show='neg')
    dummyvar = input("Next?")
    modelA[0].show_most_informative_features(n=60, show='pos')
    

#print "Category: Memory Trigger"
#modelA = buildModel(train_toks, posTest, negTest, 0)
#modelB = buildModel(train_toks, posTest, negTest, 2)
#modelC = buildModel(train_toks, posTest, negTest, 9)
#modelD = buildModel(train_toks, posTest, negTest, 15)

#print "Category: Reference"
#rModel = buildModel(ref_train_toks, ref_posTest, ref_negTest, 9)

"""
dummyvar = input("Next?")
modelB = buildModel(train_toks, posTest, negTest, 0)
modelB[0].show_most_informative_features(n=60, show='neg')
modelB[0].show_most_informative_features(n=60, show='pos')
NB = nltk.NaiveBayesClassifier.train(allTok)
#NB.show_most_informative_features(n=100)
"""

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


"""
1/27/11 3:37am

t/f features
goodChars
first word in line
pos unigram
pos bigrams - top
pos trigrams


Precision...: 0.852441759482
Recall......: 0.870740740741
True Neg....: 0.825473961841
Specificity.: 0.802222222222
F1 Score....: 0.861822488014


With 'addition group 1' commented out:
Precision...: 0.849433569927
Recall......: 0.845555555556
True Neg....: 0.798549547391
Specificity.: 0.803333333333
F1 Score....: 0.848118267967

With all trigrams
Precision...: 0.848817534918
Recall......: 0.426296296296
True Neg....: 0.544633723363
Specificity.: 0.90037037037
F1 Score....: 0.544573461369

With pos Unigrams added:
Precision...: 0.844643145516
Recall......: 0.867037037037
True Neg....: 0.819241615521
Specificity.: 0.790740740741
F1 Score....: 0.856238635631

With 'Addition #2' in features list
Precision...: 0.861907543902
Recall......: 0.861481481481
True Neg....: 0.818358070701
Specificity.: 0.818888888889
F1 Score....: 0.862038077134

Removed lb_punct
Precision...: 0.863687118052
Recall......: 0.835185185185
True Neg....: 0.792711078387
Specificity.: 0.827037037037
F1 Score....: 0.849651675762

# Added pos 1+2 grams
Precision...: 0.852138970876
Recall......: 0.858888888889
True Neg....: 0.812893567474
Specificity.: 0.804444444444
F1 Score....: 0.855990616448


"""
