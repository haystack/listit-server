from django.contrib.auth.models import User
from jv3.models import Note,ActivityLog,Event
from nltk.corpus import names,wordnet,stopwords
from nltk.tokenize import WordTokenizer
import datetime,csv
from jv3.study.study import non_stop_consenting_users,non_stop_users
from jv3.utils import current_time_decimal,is_tutorial_note,is_study1_note_contents
import random,sys

def is_english(s):
    try:
        return s.encode('utf-8','ignore') == s
    except:
        pass
    return False

def activity_logs_for_note(n,action=None,days_ago=None):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values
    if days_ago is None:
        if action:
            alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"]))
            print ' returning %d ' % len(alv)
            return alv
        return _actlogs_to_values(ActivityLog.objects.filter(noteid=n["jid"],owner=n["owner"]))
    else:
        today_m
        sec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        if action:
            print "actlogs starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
            alv = _actlogs_to_values(ActivityLog.objects.filter(action=action,noteid=n["jid"],owner=n["owner"],when__gt=n_days_ago))
            print ' returning %d ' % len(alv)
            return alv
        return _actlogs_to_values(ActivityLog.objects.filter(noteid=n["jid"],owner=n["owner"],when__gt=n_days_ago))

def activity_logs_for_user(user,action=None,days_ago=None):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values
    if days_ago is None:
        #print "days ago is none"
        if action:
            return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user))
        return _actlogs_to_values(ActivityLog.objects.filter(owner=user))
    else:
        today_msec = current_time_decimal()
        n_days_ago = today_msec - days_ago*24*60*60*1000
        print "starting with %d // %s" % (n_days_ago,repr(datetime.datetime.fromtimestamp(n_days_ago/1000.0)))
        if action:
            return _actlogs_to_values(ActivityLog.objects.filter(action=action,owner=user,when__gt=n_days_ago))
        return _actlogs_to_values(ActivityLog.objects.filter(owner=user,when__gt=n_days_ago))        

all_pass = lambda x: True

def is_sigscroll_user(u):
    return ActivityLog.objects.filter(owner=u,action="significant-scroll").count() > 0

def filter_notes(ns,english_only=True,min_length=3):
    from content_analysis import q
    from jv3.study.study import GLOBAL_STOP
    stop_owner = [x for x in User.objects.filter(email__in=GLOBAL_STOP)]
    return [x for x in ns if
            x.owner not in stop_owner and
            x.contents and len(x.contents.strip()) >= min_length and # note is non blank
            int(x.jid) >= 0 and # jid is not magic note
            q(english_only, is_english(x.contents), True) and # english if english only
            not is_tutorial_note(x.contents) and # not a tutorial
            not is_study1_note_contents(x.contents) # not a study1 note
            ]


def random_notes(n=1000,consenting=True,english_only=True,user_filter=is_sigscroll_user):
    from jv3.study.content_analysis import _actlogs_to_values,_notes_to_values,q
    
    if consenting:
        users = [ u for u in non_stop_consenting_users() if user_filter(u) ]
    else:
        users = [ u for u in non_stop_users() if user_filter(u) ]
        
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
        #print "(%d,%d)"%(x["id"],y["id"])
        return ids.index(x["id"])-ids.index(y["id"])
    ns.sort(cmp=cmp)
    return ns

def _coerce_to_ints(ns):
    ints = []
    for n in ns:
        try:
            ints.append( int(n) )
        except:
            print sys.exc_info()
        pass
    return ints
        
def import_notes_csv(filename="/tmp/notes.csv", load_text_col=True):
    from jv3.study.content_analysis import _notes_to_values
    f = open(filename,'r')
    reader = csv.reader(f, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    nids = [];
    rows = []
    ntext = {}
    for row in reader:
        rows.append(row)
        if row[0] == 'nid' or len(row[0]) == 0:  continue
        nids.append(int(row[0])) ## load notes and text
        ntext[int(row[0])]=row[3] ## store text
    #nids = _coerce_to_ints(nids)
    ns = load_notes(nids)
    ## replace txt with contents
    if load_text_col:
        # replaces currnet note image from the db with what was in the spreadsheet
        # so if the note changed post export, then we'll be ok
        [ n.update({"contents":ntext[n["id"]]}) for n in ns ] 
    return (ns,rows)

def export_notes_csv(notes,filename="/tmp/notes.csv"):
    from jv3.study.content_analysis import _notes_to_values    
    f = open(filename, 'wb')
    writer = csv.writer(f, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    for n in notes:
        u = User.objects.filter(id=n["owner"])
        writer.writerow([n["id"],n["jid"],u[0].email,n["contents"].encode('utf-8','ignore')[:32767]])
    f.close()

def spreadsheet_fill_in_blanks(sheet,with_what=0):
    from content_analysis import q
    new_sheet = [ [ q(c == '', with_what, c) for c in row ] for row in sheet[1:] ]
    return [sheet[0]] + new_sheet         


def export_features(fkeys,features,notes=None,filename='/tmp/features.csv'):
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

    ## write pickles
    import pickle
    from jv3.study.ca_sigscroll import ca_caches
    FP = open("%s.pickle"%filename,"w")
    FP.write(pickle.dumps({"features":features,"fkeys":fkeys,"sigscroll_caches":ca_caches(),"notes":notes}))
    FP.close()

def get_extreme_notes(name, key_fn, nfvs, top_N=100, bot_N=100, randomized=True):
    ## takes the top and bottom N
    ## nfvs is dict {notei:{fv_i:val}, notej:{fv_i:val}}
    scores = [(nf,key_fn(nf)) for nf in nfvs]
    scores_top = [] + scores
    scores_bottom = [] + scores
    scores_top.sort(key=lambda x: x[1],reverse=True)
    scores_bottom.sort(key=lambda x: x[1],reverse=False)
    
    if not randomized:
        return { "%s_top" % name: [t[0] for t in scores_top[0:top_N]],
                 "%s_bottom" % name : [b[0] for b in scores_bottom[0:bottom_N]] }
    
    import random
    chosen_top = []
    chosen_bottom = []
    
    while len(chosen_top) < top_N:
        try :
            chosen_top.append( scores_top[random.randint(0,3*top_N)] )
        except:
            print sys.exc_info()
        pass
    while len(chosen_bottom) < bot_N:
        try :
            chosen_bottom.append( scores_bottom[random.randint(0,3*bot_N)] )
        except:
            print sys.exc_info()
        pass
    
    return { "%s_top" % name: [t[0] for t in chosen_top],
             "%s_bottom" % name: [ b[0] for b in chosen_bottom] }



def export_extreme_notes(extreme_dict, note_keys, note_features, filename="/tmp/extreme.csv"):

    ## extreme dict
    ## { "length_top" : [note,note,note ], "note_length_bottom": [note,note,note] }
    ## note_keys = nae of other features you want to include in each note being reported
    ## note_features = feateres you want to include

    import csv
    from jv3.study.content_analysis import _notes_to_values
    F = open(filename, 'wb')
    writer = csv.writer(F, dialect="excel", delimiter=',', quoting=csv.QUOTE_MINIMAL)
    keys = extreme_dict.keys()
    keys.sort()    
    # write headers
    writer.writerow( ["nid","jid","email","contents"] + note_keys ) ## adds features to 
    for k in keys:
        print "writing %s[%d]" % (k,len(extreme_dict[k]))
        writer.writerow([k])
        for n in extreme_dict[k]:
            u = User.objects.filter(id=n["owner"])            
            row = [n["id"],n["jid"],u[0].email,n["contents"].encode('utf-8','ignore')[:32767]]
            nf = note_features[n["id"]]
            for f in fkeys:
                row.append( nf.get(f) )
            writer.writerow(row)
        pass
    F.close()
    
        
    
