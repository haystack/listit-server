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
    allWordDict = allWordDict
except:
    allWordDict = {}
    for note in mem:
        for word in nltk.word_tokenize(note.contents):
            if word not in allWordDict:
                allWordDict[word]=(0,0)
            allWordDict[word][0] += 1
    for note in notMem:
        for word in nltk.word_tokenize(note.contents):
            if word not in allWordDict:
                allWordDict[word]=(0,0)
            allWordDict[word][1] += 1

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
first_nonsymb_word_line = lambda txt: re.findall('^[^\w]*(\w+)', txt, re.MULTILINE)


def noteFeatures(note):
    global mem, notMem
    notevals = nvals(note)
    fs = {}
    noteWords = nltk.tokenize.WordPunctTokenizer().tokenize(note.contents)
    for feature in wFeatures.features:
        fname, fval = feature(notevals, noteWords)
        if fval != False:
            addFeature(fs, fname, fval)
#    for word in 
#    global allWordDict
#    for word in noteWords:
#        if word in allWordDict:
#            if (allWordDict[word][1] >= 6 or allWordDict[word][2] >= 6) and (
#                allWordDict[word][1] >= 3*allWordDict[word][2] or
#                allWordDict[word][2] >= 3*allWordDict[word][1]):
#                addFeature(fs, 'contains-word-%s'%(word), True)
## Boosted Neg to a solid 74.7% !!
    seenWords = {}
    for word in first_nonsymb_word_line(note.contents):
        word = word.lower() ## map all words to lowercase words
        if word not in seenWords:
            seenWords[word] = 0
        seenWords[word] += 1
    for word, count in seenWords.items():
        addFeature(fs,"HAS: %s"%(word), True)
#        addFeature(fs, "%s-%s-times"%(word, count), True)
#    for word in noteWords:
#        if wFeatures.word_is_verb(word) or word in wFeatures.stopWords:
#            addFeature(fs, 'contains-word', word)
#    for i in range(len(noteWords)-1): ## Bigrams?
#        addFeature(fs, "%s -^- %s"%(noteWords[i], noteWords[i+1]), True)
#    for word in noteWords:
#        if  word in wFeatures.actionWords:
#            addFeature(fs, "has-word: %s"%(word), True)
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
    pos_train = posArray[:len(posArray)/2]#int(2.0*len(posArray)/3.0)]
    pos_test = posArray[len(posArray)/2:]#int(2.0*len(posArray)/3.0):]
    neg_train = negArray[:len(negArray)/2]#int(2.0*len(negArray)/3.0)]
    neg_test = negArray[len(negArray)/2:]#int(2.0*len(negArray)/3.0):]
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

training_set = getTrainingSet(posTokens, negTokens, 15)#15)
                           
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
    model = nltk.MaxentClassifier.train(train_toks,encoding=BMFE,max_iter=15)
    mAcc = nltk.classify.util.accuracy(model, posTest)#[(noteFeatures(nn),'memory trigger') for nn in posTest])
    nmAcc = nltk.classify.util.accuracy(model, negTest)#[(noteFeatures(nn),'not') for nn in negTest])
    totTest = posTest
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
        for train_toks, posTest, negTest in training_set:
            model, mAcc, nmAcc, tAcc = buildModel(train_toks,posTest,negTest,cutoff)
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
        #print "Precision/PosPredictive Value: %s, Recall: %s"%(precallAverage[i][0],precallAverage[i][1])
        #print "Neg.PredictiveValue: %s, Specificity: %s"%(precallAverage[i][2],precallAverage[i][3])
        #print "Precision / Recall / True Neg Rate / Specificity"
        #print "%s / %s / %s / %s"%(precallAverageB[i][0],precallAverageB[i][1],precallAverageB[i][2],precallAverageB[i][3])
        print "F1 Score....: %s"%(2.0*precallAverage[i][0]*precallAverage[i][1]/(precallAverage[i][0]+precallAverage[i][1]))
        print "--------------------------------------"



evaluateCutoffs(training_set, [0])#,10])#,4])

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

def test(func):
    for i in range(0,10):
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

allWords = [(pair[0],pair[1][0],pair[1][1]) for pair in allWordDict.items()]
        
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
