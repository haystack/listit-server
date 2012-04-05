import sys, math



def wordCount(doc):
    return len(doc.split(None))


def freq(word, doc):
    return doc.split(None).count(word)


def tf(word, doc):
    wc = wordCount(doc)
    if wc == 0:
        return 0
    else:
        return (freq(word, doc) / float(wc))


def numDocsContaining(word, documentList):
    count = 0
    for document in documentList:
       	if freq(word, document) > 0:
            count += 1
    return count


def idf(word, docList):
    return math.log(len(docList) / numDocsContaining(word, docList))

cache_idf = {}
def tfidf(word, document, documentList):
    global cache_idf
    if word not in cache_idf:
        cache_idf[word] = idf(word, documentList)
    return (tf(word, document) * cache_idf[word])




def getUniqueWords(noteList):
    uniqueWords = {}
    for note in noteList:
        for word in note.contents.split(None):
            if word not in uniqueWords:
                uniqueWords[word] = 0
            uniqueWords[word] += 1
    return uniqueWords

def getAllTFIDF(uniqueWordDict, noteList):
    """ Return map from word to list of note / tfidf values that word appears in """
    contentList = [n.contents for n in noteList]
    wordToNoteTFIDF = {}
    for word in uniqueWordDict.keys():
        wordToNoteTFIDF[word] = []
        for note in noteList:
            tfidf_val = tfidf(word, note.contents, contentList)
            if tfidf_val != 0:
                wordToNoteTFIDF[word].append((note.id, tfidf_val))
    return wordToNoteTFIDF

# Alive + Deleted notes (lots of deleted test notes messing my sample up)
#wsu = getUniqueWords(wsn)
#wst = getAllTFIDF(wsu, wsn) 

# Alive Notes Only
#wwua = ta.getUniqueWords(wsn.filter(deleted=0))
#wsta = ta.getAllTFIDF(wwua, wsn.filter(deleted=0))

def listTermVals(tfidf_evaluator):
    lst = []
    for k,v in wst.items():
        tfidfs = [val[1]**2 for val in v]
        val = tfidf_evaluator(tfidfs)
        if val:
            lst.append((k, val))
    lst.sort(lambda x,y: cmp(y[1], x[1]))
    return lst

mean = lambda x: 1.0 * sum(x) / len(x)

def minNoteCount(lst, minCount=4):
    result = False
    if len(lst) >= minCount:
         result = mean(lst)
    return result

qq = {}
for nn in Note.objects.filter(owner__in=[dk, em, kf]):
    try: # Unique note-save times (no counting one time multiple times)
        qq[nn.created] = set([t.when for t in ActivityLog.objects.filter(owner=nn.owner, action='note-save', noteid=nn.jid).values('when')])
    except:
        pass 

editAge = [] # Age of edited note when edit occured.
for created, editedList in qq.items():
    for editedTime in editedList:
        editAge.append(editedTime['when'] - created)


