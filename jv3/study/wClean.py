## For cleaning database: remove problematic notes
## ie. Tutorial notes, notes experiencing sync problems (repeated texts), etc
from jv3.utils import is_tutorial_note
from jv3.models import *

def clean_full():  ## Perform all cleaning functions
    clean_tutorial_notes()
    clean_noteorder()
    clean_repeat_notes(Note.objects.all()) ## Doesn't actually delete anything - ??

def kill_note(n):
    njid = n.jid
    nowner = n.owner
    note.delete()
    ActivityLog.objects.filter(owner=nowner,noteid=njid).delete()

def clean_tutorial_notes():
    i = 0
    for note in Note.objects.all():
        if is_tutorial_note(note.contents):
            kill_note(note)
            i+=1
    print "Deleted: ", i, " tutorial notes."

def clean_noteorder():
    i = 0
    for note in Note.objects.all():
        if note.jid == -1:
            kill_note(note)
            i+=1
    print "Deleted: ", i, " noteorder notes."

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
            print "Word1 is: ", maxP, "at", maxPC, "# of times repeated"
            ##input("Next?:")
            i += 1
    return i
    
def countUsers(lim):
    note_count = 0
    for user in u:
        count = clean_repeat_notes(Note.objects.filter(owner=user))
        note_count += count
    print note_count, " notes are over 300 repeats of 1 word." 


