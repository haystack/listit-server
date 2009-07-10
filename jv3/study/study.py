from jv3.utils import *
from django.contrib.auth.models import *
from jv3.models import *
from jv3.study.exporter import *
from django.utils.simplejson import JSONDecoder,JSONEncoder
from math import log
from datetime import date
import decimal

unidefang = lambda text: text.replace("\n","\\n").replace("\t"," ")
users = None
notes = None
problem = []

def non_stop_consenting_users(stoplist=None):
    if stoplist is None:
        stoplist = ['emax@csail.mit.edu', 'karger@mit.edu', 'kp@csail.mit.edu',
                    'gvargas@mit.edu', 'karger@csail.mit.edu', 'msbernst@mit.edu',
                    'wstyke@gmail.com']
    stopusers = map(lambda x : User.objects.filter(email=x), stoplist)
    stopusers = [u[0] for u in stopusers if len(u) > 0]
    return filter(lambda u: u not in stopusers, get_consenting_users());

def filter_stop_users(ulist):
    stopusers = map(lambda x : User.objects.filter(email=x),stoplist)
    stopusers = [u[0] for u in stopusers if len(u) > 0]
    return filter(lambda u: u not in stopusers, ulist);

def non_stop_users():
    stopusers = map(lambda x : User.objects.filter(email=x),stoplist)
    stopusers = [u[0] for u in stopusers if len(u) > 0]
    return filter(lambda u: u not in stopusers, User.objects.all())

def overall_non_deleted_note_counts_per_user(users=None):
    if users is None:
        users = User.objects.all()
    counts = {}
    for u in users:
        n_notes = len(jv3.models.Note.objects.filter(owner=u,deleted=False))
        counts[n_notes] = counts.get(n_notes,0)+1
    return counts

def notes_by_users_created_between(starttime_secs,endtime_secs,users=None):
    if users is None:
        users = non_stop_consenting_users()
    return Note.objects.filter(created__gte=int(starttime_secs*1000.0),created__lte=int(endtime_secs*1000.0),owner__in=users)

def notes_by_users_edited_between(starttime_secs,endtime_secs,users=None):
    if users is None:
        users = non_stop_consenting_users()
    return Note.objects.filter(edited__gte=int(starttime_secs*1000.0),edited__lte=int(endtime_secs*1000.0),owner__in=users)



def notes_by_users_posted_n_days_ago(users=None,ndays=7):
    start = int(time.mktime((datetime.datetime.today() - datetime.timedelta(ndays)).timetuple())*1000.0)
    if users is None:
        users = non_stop_consenting_users()
    return Note.objects.filter(created__gte=start,owner__in=users)

def users_whove_posted_at_least_since_n_days_ago(users=None,ndays=7):
    start = int(time.mktime((datetime.datetime.today() - datetime.timedelta(ndays)).timetuple())*1000.0)
    if users is None:
        users = non_stop_consenting_users()
    return set([x.owner for x in Note.objects.filter(created__gte=start,owner__in=users)])

def users_with_less_than_n_notes(n=0,users=None):
    if users is None:
        users = non_stop_consenting_users()
    return [u for u in users if u.note_owner.count() <= n]

def consenting_users_with_less_than_n_notes(n=0):
    users = non_stop_consenting_users()
    return [u for u in users if u.note_owner.count() <= n]

def users_active_during(start_secs,end_secs):
    return list(set( [a.owner for a in jv3.models.ActivityLog.objects.filter(when__gte=int(start_secs*1000.0),when__lte=int(end_secs*1000.0))]))

def relevant_notes(users=None):
    if users is None:
        users = non_stop_consenting_users();
    return Note.objects.filter(owner__in=users)

def doit(users=None):
    global notes
    global problem
    s  = ""
    if notes is None:
        notes = relevant_notes(users)    
    for n in notes:
        try:
            s += "%s\t%s\t%s\n" % (n.owner.email, note_created(n), unidefang(n.contents))
        except ValueError, x:
            problem.append(n.contents)
            print x            
    return s


def doit2():
    global notes
    global problem
    s  = ""
    if notes is None:
        notes = relevant_notes()    
    return make_spreadsheet(notes_statistics_given_notes(notes),col_headers=[x[0] for x in note_statistic_fns])


get_edits = lambda note_add_action:  jv3.models.ActivityLog.objects.filter(action__contains="note-edit",owner=note_add_action.owner,noteid=note_add_action.noteid)


def entropy(counts):
    ctotal = sum( [ x for x in counts.itervalues() ] )
    return sum([ counts[u]/(1.0*ctotal)*log( counts[u]/(1.0*ctotal) ) for u in counts.iterkeys()])

def maxentropy(ctotal):
    return sum([ 1.0/ctotal *log( 1.0/ctotal ) for u in range(ctotal ) ])

def reaccess_dow():
    adds = jv3.models.ActivityLog.objects.filter(action__contains="note-add",owner__in=non_stop_users())
    entropies = []
    for add in adds:
        edits_beyond_an_hour = filter( lambda x : abs(add.when-x.when) > 60*60  , get_edits(add))
        dow={}
        edit_count = 0
        for edit in edits_beyond_an_hour:
            edit_date = date.fromtimestamp(float(edit.when)/1000.0)
            dow[edit_date.weekday()] = dow.get(edit_date.weekday(),0) + 1
            edit_count = edit_count + 1
        if edit_count > 3:
            print "got more than 3 edits, entropy is %g: %s " % (entropy(dow),dow)
            entropies.append(entropy(dow)/maxentropy(7))
    return entropies

def reaccess_hod(): ## hour of day
    adds = jv3.models.ActivityLog.objects.filter(action__contains="note-add",owner__in=non_stop_users())
    entropies = []
    for add in adds:
        edits_beyond_an_hour = filter( lambda x : abs(add.when-x.when) > 60*60  , get_edits(add))
        hod={}
        edit_count = 0
        for edit in edits_beyond_an_hour:
            hour = time.localtime(float(edit.when)/1000.0)[3]
            hod[hour] = hod.get(hour,0) + 1
            edit_count = edit_count + 1
        if edit_count > 3:
            print "got more than 3 edits, entropy is %g: %s " % (entropy(hod),hod)
            entropies.append(entropy(hod)/maxentropy(24))
    return entropies

def get_chistudy_users():
    chistudy_user_emails = ["adwang@mit.edu","agirouard@gmail.com","alekseyp@mit.edu","alexander.bakst@alum.mit.edu","alya@mit.edu","belleb@mit.edu","brennanmoore@gmail.com","cadlerun@csail.mit.edu","ddugan@mit.edu","e_basha@mit.edu","ebakke@mit.edu","ecooper@mit.edu","eob@mit.edu","evafish926@yahoo.com","feather@mit.edu","francescamariesmith@gmail.com","glittle@gmail.com","gremio@csail.mit.edu","jamey.hicks@nokia.com","jbarilla@cs.princeton.edu","jdiaz@mit.edu","jkwerfel@mit.edu","jskrones@alum.mit.edu","jtheurer@mit.edu","jyoull@alum.mit.edu","kdrinkwa@mit.edu","kehinger@mit.edu","kp@csail.mit.edu","larsent@mit.edu","leo.sauermann@dfki.de","lindaliu@mit.edu","list.it@gwizdka.com","mark.adler@alum.mit.edu","mbrown@bcs.rochester.edu","mjp@mit.edu","moah@alum.mit.edu","mr_jim@verizon.net","ora.lassila@nokia.com","sacha@mit.edu","scott.ostler@gmail.com","thepeach@mit.edu","twdougan@gmail.com","vineet@csail.mit.edu","wesbrown@mit.edu","wickycui@hotmail.com","zakf@mit.edu"];
    chistudy_users = [User.objects.filter(email=email)[0] for email in chistudy_user_emails if len(User.objects.filter(email=email)) > 0]
    return chistudy_users


def get_chistudy_notes():
    newerthan=decimal.Decimal(repr(time.mktime(datetime.date(2008,8,25).timetuple())*1000))
    before=decimal.Decimal(repr(time.mktime(datetime.date(2008,9,13).timetuple())*1000))
    ## gets users who have in their most _recent_ consent agreed to couhes
    userset = get_chistudy_users()
    return jv3.models.Note.objects.filter(owner__in=userset, created__gt=newerthan, created__lt=before)

def reaccess_urls():
    decoder = JSONDecoder()
    
    def get_url(logobject):
        try:
            return decoder.decode(logobject.search)["viewing_url"]
        except TypeError,v:
            pass
        return None
    
    adds = jv3.models.ActivityLog.objects.filter(search__contains="viewing_url",action__contains="note-add",owner__in=non_stop_users())
    fractional_counts = []
    entropies = []
    maxentropies = []

    for a in adds:
        ## find edits
        ctotal = 0
        counts = {}
        edits = get_edits(a)
        for u in [get_url(x) for x in edits if get_url(x) is not None]:
            counts[u] = counts.get(u,0) + 1
            ctotal = ctotal + 1
        if ctotal > 3:
            print counts
            print ctotal
            entropies.append( entropy(counts)  )
            maxentropies.append(maxentropy(ctotal))

    print entropies
    print maxentropies
    return [entropies[i]/maxentropies[i] for i in range(len(entropies))] 

variance = lambda v: sum([ (i - sum(v)/len(v))**2 for i in v ])/(1.0*len(v))
mean = lambda v: sum(v)/len(v)

def number_of_edits_histogram():
    adds = jv3.models.ActivityLog.objects.filter(action__contains="note-add", owner__in=non_stop_consenting_users())
    re_edits = {}
    for a in adds:
        n_edits = len(get_edits(a))
        re_edits[n_edits] = re_edits.get(n_edits,0) + 1
    return re_edits

def deleted_notes():
    owned = Note.objects.filter(owner__in=non_stop_consenting_users())
    return [len(owned.filter(deleted=False)),len(owned.filter(deleted=True))]

def number_of_notes_histogram(users):
    counts = {}
    rawcount = []
    for u in users:
        n = len(Note.objects.filter(owner=u,deleted=False))
        counts[n] = counts.get(n,0) + 1
        rawcount.append(n)
    return notes,rawcount

def histogram_to_csv(bins):
    return "\n".join( [ "%d, %d" % g for g in bins.iteritems() ] )

def write_histogram_to_csv(bindata,filename):
    f = open(filename,'w')
    f.write(histogram_to_csv(bindata))
    f.close()
    

def median(numbers):
   "Return the median of the list of numbers."
   # Sort the list and take the middle element.
   n = len(numbers)
   copy = numbers[:] # So that "numbers" keeps its original order
   copy.sort()
   if n & 1:         # There is an odd number of elements
      return copy[n // 2]
   else:
      return (copy[n // 2 - 1] + copy[n // 2]) / 2

def users_reordering():
    switch = jv3.models.ActivityLog.objects.filter(action__contains="rerank-mode-switch")
    users = []
    [ users.append(x.owner) for x in switch if not x.owner in users ]
    return users

def mode_use_count():
    switch = jv3.models.ActivityLog.objects.filter(action__contains="rerank-mode-switch")
    modes = {}
    for x in switch:
        for mode in  x.noteText.split(","):
            modes[mode] = modes.get(mode,0) + 1;
    return modes

def mode_use_count2():
    switch = jv3.models.ActivityLog.objects.filter(action__contains="rerank-mode-switch")
    modes = {}
    for x in switch:
        mode = x.noteText
        modes[mode] = modes.get(mode,0) + 1;
    return modes

def rerank_result():
    return jv3.models.ActivityLog.objects.filter(action__contains="rerank-result")

def per_note_edit_duration(notes=None,edits=True,adds=True):
    if notes is None:
        notes = get_chistudy_notes()
    rows = []
    for n in notes:
        if note_is_probe_response(n):
            continue
        actlogs = jv3.models.ActivityLog.objects.filter(owner=n.owner)
        for i in range(1,len(actlogs)):
            a = actlogs[i]
            if not a.noteid == n.jid:
                continue
            last_a = actlogs[i-1]
            if adds and a.action == 'note-add' and last_a.action == 'notecapture-focus':
                rows.append([ n.owner.email, a.noteid, a.noteText, long(a.when) - long(last_a.when) ])
            if edits and a.action == 'note-save' and last_a.action == 'note-edit' and a.noteid ==last_a.noteid :
                rows.append([ n.owner.email, a.noteid, a.noteText, long(a.when) - long(last_a.when) ])
    return rows

def make_pned_spreadsheet(edits=True,adds=True):
    rows = per_note_edit_duration(None,edits,adds)
    for r in rows:
        r[2] = defang(r[2])
        r[1] = "%d"%r[1]
        r[3] = "%d"%r[3]
    return make_spreadsheet(rows)        

def reranked_notes():
    reranks = rerank_result()
    notes = {}
    decoder = JSONDecoder()
    nranked = []
    for r in reranks:
        rankings = decoder.decode(r.noteText)["rank"]
        for n in rankings.iterkeys():
            notes[n] = notes.get(n,0) + 1
        nranked.append(len(rankings))
    return notes,nranked

## 
