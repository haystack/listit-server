## For cleaning database: remove problematic notes
## ie. Tutorial notes, notes experiencing sync problems (repeated texts), etc

from jv3.utils import is_tutorial_note
from jv3.models import *

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

def rid_of_edits_that_dont_change_note():
    from django.contrib.auth.models import User

    kill_list_alids = []
    errors = []
    for u in User.objects.all():
        user_kill = []
        try :
            edits_per_jid= dict([(jid,[(alid,text)])  for jid,alid,text in u.activitylog_set.filter(action="note-add").values_list('noteid','id','noteText')])
            # we have to believe they're consecutive
            alog_edits = u.activitylog_set.filter(action='note-edit').order_by('when').values_list('id','noteid','noteText')
            for alid,jid,noteText in alog_edits:
                v = edits_per_jid.get(jid,[])
                v.append( (alid,noteText) )
                edits_per_jid[jid] = v
                
            for jid,editpairs in edits_per_jid.iteritems():
                noteText = editpairs[0][1]
                for epair in editpairs[1:]:
                    alid,newText = epair
                    if noteText == newText:   # nothing's changed,kill
                        user_kill.append(alid)
                    else:
                        noteText = newText
                    pass
                pass
            print "edits to kill for %s : %d " % (u.email,len(user_kill))
            kill_list_alids = kill_list_alids + user_kill
        except :
            import traceback,sys            
            errors.append(u)
            print sys.exc_info()
            traceback.print_tb(sys.exc_info()[2])
    # ActivityLog.objects.filter(id__in=kill_list_alids).delete()

    print "ERRORS %d : %s",(len(errors),repr(errors))
    return ActivityLog.objects.filter(id__in=kill_list_alids)
                
        


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


