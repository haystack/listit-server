## Helper
def note_to_worddict(note):
    wordDict = {}
    for line in note.contents.split('\n'):
        for word in line.split(' '):
            if word == '' or word == ' ':
                continue
            if len(word) <= 3:
                continue
            if word not in wordDict:
                if note.deleted:
                    wordDict[word] = [1,0] ## [0,1]
                else:
                    wordDict[word] = [0,1] ## [1,0]
                pass
    return wordDict

def notes_to_dict(notes):
   ## wordDict keys are words, values are [#living notes, #dead notes] that contain this word 1+ times
    wordDict = {}
    ##bannedWords = {}  ## Don't keep track of words which are in any deleted notes...  ## HUGE SPEED INCREASE!
    for note in notes:
        tmpDict = note_to_worddict(note)
        for k,v in tmpDict.items():
            ##if k in bannedWords:
            ##    continue
            ##if v[1] >= 1:
            ##    bannedWords[k] = 1
            if k in wordDict.keys():
                wordDict[k][0] += v[0]
                wordDict[k][1] += v[1]
            else:
                wordDict[k] = [v[0],v[1]]
    return wordDict

## Returns array with entries [word, #living notes, #dead notes containing word]
def wordDict_to_array(wordDict):
    wordArr = []
    for k,v in wordDict.items():
        wordArr.extend([[k, v[0], v[1]]])
        pass
    return wordArr


## for comparing two elements of array created above
def wordItem_compare(a,b, type=''):
    ## Return 1 if a larger, 0 if equal, -1 if b larger
    frac = lambda a,b: float(a)/float(b)
    if a[2] == 0 and b[2] == 0:
        return 1 if a[1] > b[1] else -1 if b[1] > a[1] else 0
    if a[2] == 0:
        return 1
    if b[2] == 0:
        return -1
    ## Neither denominators are 0, so check comparisons
    if frac(a[1],a[2]) > frac(b[1],b[2]):
        return 1
    elif frac(a[1],a[2]) < frac(b[1],b[2]):
        return -1
    else:
        return 0
        

def wordArr_walkthru(wordArr):
    index = len(wordArr)
    while index >= 0:  ## Walk through all elements
        index -= 1
        print wordArr[index] 
        if index % 20 == 0:
            input("Next? ")
    print "---DONE---"

def make_word_arr(notes, walkthru=False):
    import datetime
    startTime = datetime.datetime.now()
    nDict = notes_to_dict(notes)
    print "Finished nDict, making array"
    nArr = wordDict_to_array(nDict)
    print "Finished nArr, sorting"
    nArr.sort(wordItem_compare)
    print "Finished Sorting: elapsed time: ", datetime.datetime.now() - startTime
    if walkthru:
        wordArr_walkthru(nArr)
    else:
        return nArr



def word_length_by_ver(notes, ver):
    lowD = [0,0]
    highD = [0,0]
    for note in notes:
        if note.jid == '-1' or note.version > 500 or len(note.contents)>10000 or len(note.contents) == 0:
            continue
        if note.version <= ver:
            lowD[0]+=1
            lowD[1]+=len(note.contents)
        else:
            highD[0]+=1
            highD[1]+=len(note.contents)
        pass
    print "Average length of notes over version ", ver, " is: ", float(highD[1])/highD[0] 
    print "Average length of notes under is: ", float(lowD[1])/lowD[0]


