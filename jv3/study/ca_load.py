from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
import datetime,csv
from jv3.study.study import non_stop_consenting_users,non_stop_users
from jv3.utils import current_time_decimal,is_tutorial_note,is_study1_note_contents

def activity_logs_for_note(n,action="note-edit",days_ago=None):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values
    if days_ago is None:
        alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"]))
        print ' returning %d ' % len(alv)
        return alv
    else:
        today_msec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        print "actlogs starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
        alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"],when__gt=n_days_ago))
        print ' returning %d ' % len(alv)
        return alv

def activity_logs_for_user(user,action="note-edit",days_ago=None):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values
    if days_ago is None:
        return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user))
    else:
        today_msec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        print "starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
        return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user,when__gt=n_days_ago))

def random_notes(n=1000,consenting=True,english_only=True):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values    
    if consenting:
        users = non_stop_consenting_users()
    else:
        users = non_stop_users()
    good_ids = [x[0] for x in Note.objects.filter(owner__in=users).values_list("pk","jid","contents") if
                len(x[2].strip()) > 0 and # note is non blank
                x[1] >= 0 and # jid is not magic note
                q(english_only, is_english(x[2]), True) and # english if english only
                not is_tutorial_note(x[2]) and # not a tutorial 
                not is_study1_note_contents(x[2]) # not a study1 note
               ]
    random.shuffle(good_ids)
    notes = Note.objects.filter(pk__in=good_ids[:n])
    print "returning %d notes " % len(notes)
    values = [v for v in _notes_to_values(notes)]
    random.shuffle(values)
    return values


def load_notes(ids):
    from jv3.study.content_analysis import _notes_to_values    
    print ids
    ns = [x for x in _notes_to_values(Note.objects.filter(pk__in=ids))]
    def cmp(x,y):
        print "(%d,%d)"%(x["id"],y["id"])
        return ids.index(str(x["id"]))-ids.index(str(y["id"]))
    ns.sort(cmp=cmp)
    return ns

def import_notes_csv(filename="/tmp/notes.csv"):
    from jv3.study.content_analysis import _notes_to_values
    f = open(filename,'r')
    reader = csv.reader(f, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    nids = [];
    for row in reader:
        if row[0] == 'nid':  continue
        nids.append(row[0])
    return load_notes(nids)

def export_notes_csv(notes,filename="/tmp/notes.csv"):
    from jv3.study.content_analysis import _notes_to_values    
    f = open(filename, 'wb')
    writer = csv.writer(f, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    for n in notes:
        u = User.objects.filter(id=n["owner"])
        writer.writerow([n["id"],n["jid"],u[0].email,n["contents"].encode('utf-8','ignore')[:32767]])
    f.close()

def export_features(fkeys,features,filename='/tmp/features.csv'):
    from jv3.study.content_analysis import _notes_to_values
    F = open(filename, 'wb')
    writer = csv.writer(F, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    # write headers
    writer.writerow( ["nid","jid","email","contents"] + fkeys )
    #
    for nid,nf in features.items():
        n = _notes_to_values(Note.objects.filter(pk=nid))[0]
        u = User.objects.filter(id=n["owner"])
        print n
        row = [n["id"],n["jid"],u[0].email,n["contents"].encode('utf-8','ignore')[:32767]]
        for f in fkeys:
            row.append( nf.get(f) )
        writer.writerow(row)
    F.close()
