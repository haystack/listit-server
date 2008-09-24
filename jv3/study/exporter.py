
import django.contrib.auth.models as authmodels
import jv3.utils
import time,datetime
import jv3.models
import re
from jv3.utils import levenshtein

def printf(x):
    print x

# def defang(x) :
#     if x is not None:
#         return x.replace('\n','\\n')
#     return None

def defang_unicode(s):
    if isinstance(s,unicode):
        return s.encode('utf-8','ignore')
    return s.decode('iso-8859-1','ignore')    

def defang(x) :
    if x is not None:
        x = defang_unicode(x)
        return x.replace('\n','\\n').replace('\t','')
    return None

TEST_STRING = """daisy daisy
give me your answer do,

i've gone crazy

all for the love of you

i dont need a stylish-marriage

i can't afford a carriage."""

## print "number of lines %d " % nlp_count_lines(TEST_STRING)
## print "avg word length %g " % nlp_average_word_length(TEST_STRING)

activity_logs_for_note = lambda n,action="note-edit": jv3.models.ActivityLog.objects.filter(action=action,owner=n.owner,noteid=n.jid)
delete_log_for_note = lambda n: jv3.models.ActivityLog.objects.filter(action="note-delete",owner=n.owner,noteid=n.jid)
note_n_edits = lambda note:len( activity_logs_for_note(note) )
note_n_saves = lambda note:len( activity_logs_for_note(note,action="note-save") )

def note_total_edit_time(note):
    nlogs = activity_logs_for_note(note)
    nlogs.sort(key=lambda log : log['id'])
    ## determine consecutiveness
    pass

def note_deleted_time(note):
    d = delete_log_for_note(note)
    if len(d) > 0: return makedate_usec(long(d[0].when))
    return None

def note_deleted_time_usec(note):
    d = delete_log_for_note(note)
    if len(d) > 0: return long(d[0].when)
    return None

def note_avg_edit_time(note):
    pass

## string statistics
str_n_words = lambda s: len( [l for l in s.split() if len(l.strip()) > 0] )
str_n_lines = lambda s: len([l for l in s.split('\n') if len(l.strip()) > 0])
str_n_urls = lambda s: len([ x.start for x in re.finditer('http:[\S]+',s)])

def str_is_probe_response(s):
    hits = [ e for e in re.finditer('note (\d+)', s, re.IGNORECASE) ]
    if len(hits) > 0: return hits[0].groups()[0]
    return False

def str_average_word_length(s):
    words = [l for l in s.split() if len(l.strip()) > 0]
    if len(words) > 0:
        return reduce(lambda x,y: x+y, [len(l) for l in words])/(1.0*len(words))
    return 0

## note statistics (that use string stats above)
note_guid = lambda note: note.id
note_jid = lambda note: note.jid
note_owner_email = lambda note: note.owner.email
note_owner_joindate = lambda note: makedate_usec(long(jv3.utils.get_newest_registration_for_user_by_email(note.owner.email).when))
user_joindate = lambda user: makedate_usec(long(jv3.utils.get_newest_registration_for_user_by_email(user.email).when))
note_owner_id = lambda note: note.owner.id
note_deleted = lambda note: repr(bool(note.deleted))
note_created = lambda note: makedate_usec(long(note.created))
note_modified = lambda note: makedate_usec(long(note.edited))
note_version = lambda note: repr(int(note.version))
note_contents = lambda note: defang(note.contents)
note_contents_length = lambda note: len(note.contents)

note_n_words = lambda note: str_n_words(note.contents)
note_n_lines = lambda note: str_n_lines(note.contents)
note_n_urls = lambda note: str_n_urls(note.contents)
note_is_probe_response = lambda note:str_is_probe_response(note.contents)
note_avg_word_length = lambda note:str_average_word_length(note.contents)

def note_lifetime(n):
    endtime = time.time()
    if n.deleted:
        d = delete_log_for_note(n)
        if len(d) > 0:
            endtime = long(d[0].when)/1000
    return endtime - long(n.created)/1000

def makestr(v):
    if isinstance(v,str):
        return defang(v)
    if isinstance(v,unicode):
        return defang(v)
    if isinstance(v,long):
        return "%d" % v
    return repr(v)

def makedate_usec(v):
    return time.strftime("%D %H:%M", time.localtime(v/1000.0))    

note_statistic_fns = [
    ('guid',note_guid),
    ('jid',note_jid),
    ('user',note_owner_email),
    ('user_id',note_owner_id),
    ('user_join_date',note_owner_joindate),
    ('deleted',note_deleted),
    ('contents',note_contents),
    ('created_time',note_created),
    ('modified_time',note_modified),
    ('version',note_version),
    ('is_probe_response',note_is_probe_response),
    ('length',note_contents_length),
    ('n_words',note_n_words),
    ('avg_word_length',note_avg_word_length),
    ('n_lines',note_n_lines),
    ('n_urls',note_n_urls),
    ('n_edit_select',note_n_edits),
    ('n_edit_save',note_n_saves),
    ('delete_time',note_deleted_time),
    ('lifetime',note_lifetime),
]

def make_spreadsheet(stat_rows, field_delim="\t", row_delim="\n", col_headers=None):
    ## col headers
    rows = []
    if col_headers:
        rows = [ field_delim.join(col_headers) ]
    ## rows
    rows = rows + [field_delim.join([makestr(col) for col in row]) for row in stat_rows ]
    return row_delim.join( rows )

def notes_statistics(users=None, cols=None, stat_fns=note_statistic_fns):
    if not users:
        users = authmodels.User.objects.all()
    rows = [[ f[0] for f in stat_fns ]]    
    for u in users:
        for n in jv3.models.Note.objects.filter(owner=u):
            rows.append( [ f[1](n) for f in stat_fns ] )
    return rows

def determine_hits(u,search):
    all_notes = jv3.models.Note.objects.filter(owner=u)
    all_notes = [ n for n in all_notes if n.created < search.when ]
    all_notes = [ n for n in all_notes if note_deleted_time_usec(n) is None or note_deleted_time_usec(n) > search.when ]
    if search.search is None : return [ int(n.jid) for n in all_notes ]
    return [int(n.jid) for n in all_notes if n.contents and n.contents.find(search.search) >= 0]

def search_statistics(users=None):
    if not users: users = authmodels.User.objects.all()
    rows = []
    unique_searches = []
    
    def replaceNone(s):
        if s is None:
            return ""
        return s.encode('iso-8859-1','ignore')
        
    for u in users:
        actions = [action for action in jv3.models.ActivityLog.objects.filter(owner=u,action='search')]
        actions.sort(key=lambda x : long(x.when))
        prev = None
        for a in actions: rows.append([u.email, a.action, makedate_usec(long(a.when)), replaceNone(a.search), ",".join(["%d" % d for d in determine_hits(u,a)])])
    return rows

def per_action_per_note(users=None):
    rows = []
    def replaceNone(s):
        if s is None:
            return ""
        return s.encode('iso-8859-1','ignore')

    if not users: users = authmodels.User.objects.all()
    for u in users:
        for n in jv3.models.Note.objects.filter(owner=u):
            for a in jv3.models.ActivityLog.objects.filter(owner=u,noteid=n.jid):
                rows.append([u.email, a.action, n.jid, makedate_usec(long(a.when)), replaceNone(a.noteText)])
        
    return rows

def find_alive_notes_at_d(u,probe_time_usec):
    notes = jv3.models.Note.objects.filter(owner=u)
    results = []
    for n in notes:
        deleted = note_deleted_time_usec(n)
        if not note_is_probe_response(n) and (long(n.created) <= probe_time_usec) and (deleted is None or deleted > probe_time_usec):
            results.append(n)

    return results

DAILY = 24*60*60*1000
TWICE_DAILY = 12*60*60*1000
HOURLY = 1*60*60*1000

SEPT_1 = 1220241600000
SEPT_17 = 1221624000000
SEPT_15 = 1221451200000

def per_user_notes_alive_per_day(users=jv3.utils.get_consenting_users(),start_usec=SEPT_1,end_usec=SEPT_17,skip_usec=DAILY):
    ## make column headers
    headers = ['username']
    s = start_usec
    while s < end_usec:
        headers.append(makedate_usec(s))
        s += skip_usec
        pass

    rows = []
    for u in users:
        row = [u.email]
        s = start_usec
        while s < end_usec:
            row.append(len(find_alive_notes_at_d(u,s)))
            s += skip_usec
        rows.append(row)
        
    return [headers] + rows

def per_user_still_using_after(users=jv3.utils.get_consenting_users(),date_usec=SEPT_15):
    rows = []
    for u in users:
        notes = jv3.models.Note.objects.filter(owner=u)
        rows.append([ u.email, len([ n for n in notes if long(n.created) > date_usec or long(n.edited) > date_usec ])])
    return rows

def per_note_edit_duration(users=jv3.utils.get_consenting_users(),edits=True,adds=True):
    rows = []
    for u in users:
        actlogs = jv3.models.ActivityLog.objects.filter(owner=u)        
        for i in range(1,len(actlogs)):
            a = actlogs[i]
            last_a = actlogs[i-1]
            if adds and a.action == 'note-add' and last_a.action == 'notecapture-focus':
                rows.append([ u.email, a.noteid, a.noteText, long(a.when) - long(last_a.when) ])
            if edits and a.action == 'note-save' and last_a.action == 'note-edit' and a.noteid ==last_a.noteid :
                rows.append([ u.email, a.noteid, a.noteText, long(a.when) - long(last_a.when) ])
        
    return rows

def per_action_per_user(users=jv3.utils.get_consenting_users()):
    rows = []
    def replaceNone(s):
        if s is None:
            return ""
        if isinstance(s,int) or isinstance(s,long) or isinstance(s,float):
            return repr(s)
        return s.encode('iso-8859-1','ignore')

    if not users: users = authmodels.User.objects.all()
    for u in users:
        for a in jv3.models.ActivityLog.objects.filter(owner=u):
            rows.append([u.email, makedate_usec(long(a.when)), a.action, replaceNone(a.noteid), replaceNone(a.noteText), replaceNone(a.search)])
        
    return rows


def client_usage_open_close(users=jv3.utils.get_consenting_users()):
    opens = {}
    rows = []
    for u in users:
        actlogs = jv3.models.ActivityLog.objects.filter(owner=u)
        for a in actlogs:
            if a.action == 'sidebar-open':
                opens[a.search] = long(a.when)
            if a.action == 'sidebar-close' and opens.has_key(a.search):
                rows.append([u.email, makedate_usec(opens[a.search]), makedate_usec(long(a.when)), long(a.when)-opens[a.search]])
                del opens[a.search]
    return rows


def client_usage_open_close_intervening_actions(users=jv3.utils.get_consenting_users()):
    rows = []
    for u in users:
        actlogs = jv3.models.ActivityLog.objects.filter(owner=u,action='sidebar-open')
        print "actlogs: %s " % repr(actlogs)
        for a in actlogs:
            closelog = jv3.models.ActivityLog.objects.filter(owner=u,action='sidebar-close',search=a.search)
            if len(closelog) == 0:
                ## fall back
                print "fall back for user %s " % u.email
                closelog = jv3.models.ActivityLog.objects.filter(owner=u,action='sidebar-open',when__gt=a.when)
                if len(closelog) == 0: print "couldnt even find a second sidebar open %s " % u.email
                continue
            
            closelog = closelog[len(closelog)-1]
            print "start %s end %s - %s " % (repr(float(a.when)),repr(float(closelog.when)),float(closelog.when)-float(a.when))
            note_add = jv3.models.ActivityLog.objects.filter(owner=u,action='note-add',when__lte=long(closelog.when),when__gte=long(a.when))
            note_save = jv3.models.ActivityLog.objects.filter(owner=u,action='note-save',when__lte=long(closelog.when),when__gte=long(a.when))
            note_del = jv3.models.ActivityLog.objects.filter(owner=u,action='note-delete',when__lte=long(closelog.when),when__gte=long(a.when))
            note_search = jv3.models.ActivityLog.objects.filter(owner=u,action='search',when__lte=long(closelog.when),when__gte=long(a.when))
            row = [u.email, makedate_usec(long(a.when)), makedate_usec(long(closelog.when)), long(closelog.when)-long(a.when), len(note_add), len(note_save), len(note_del), len(note_search)]
            print "row %s " % repr(row)
            rows.append(row)
    return rows


def probes_taken_by_user(users=jv3.utils.get_consenting_users(),probe_range=range(1,20)):
    rows = []
    for u in users:
        notes = jv3.models.Note.objects.filter(owner=u)
        by_probe = {}
        for n in notes:
            if note_is_probe_response(n) is not False and int(note_is_probe_response(n)) in probe_range:
                by_probe[int(note_is_probe_response(n))] = n.contents
        row = [ u.email, len(by_probe), user_joindate(u) ]
        row.append([ by_probe.get(x, "") for x in probe_range ])
        rows.append(row)
    return rows                
        
        
    
#print notes(authmodels.User.objects.filter(email="emax@csail.mit.edu"))
#print make_spreadsheet(notes_statistics(),col_headers=[x[0] for x in note_statistic_fns])
   


