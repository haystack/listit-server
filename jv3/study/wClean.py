## For cleaning database: remove problematic notes
## ie. Tutorial notes, notes experiencing sync problems (repeated texts), etc

from jv3.utils import is_tutorial_note

def clean_tutorial_notes():
    i = 0
    for note in Note.objects.all():
        if is_tutorial_note(note.contents):
            note.delete()
            i+=1
    print "Deleted: ", i, " notes."


## Delete all note-order (jid=-1) notes?? Maybe we want these for analysis though...
## Just don't want them muddling up version average, etc...
def clean_noteorder():
    pass
    
        

## Detect/delete notes with text that's been repeated
def clean_repeat_notes(notes):
    i = 0
    for note in notes:
        txt = note.contents
        if len(txt) == 0:
            continue
        ## Detect if a word repeats
        phraseDict = {}
        maxP = ''
        maxPC = 0
        for phrase in txt.split(' '):
            if len(phrase) < 2:
                continue
            if phrase in phraseDict:
                phraseDict[phrase] += 1
            else:
                phraseDict[phrase] = 0
            if phraseDict[phrase] > maxPC:
                maxPC = phraseDict[phrase]
                maxP = phrase
        if maxPC > 400:
            ##print note.contents
            print "Word1 is: ", maxP
            ##input("Next?:")
            i += 1
    return i
    
def countUsers(lim):
    note_count = 0
    for user in u:
        count = clean_repeat_notes(Note.objects.filter(owner=user))
        note_count += count
    print note_count, " notes are over 300 repeats of 1 word." 


