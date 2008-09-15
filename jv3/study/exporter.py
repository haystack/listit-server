
import django.contrib.auth.models as authmodels
import jv3.utils
import time,datetime
import jv3.models
import re

def printf(x):
    print x

def defang(x) :
    if x is not None:
        return x.replace('\n','\\n')
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
    if len(d) > 0: return time.ctime(long(d[0].when)/1000)
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
note_owner_id = lambda note: note.owner.id
note_deleted = lambda note: repr(bool(note.deleted))
note_created = lambda note: time.ctime(long(note.created)/1000)
note_modified = lambda note: time.ctime(long(note.edited)/1000)
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
        return v
    return repr(v)

note_statistic_fns = [
    ('guid',note_guid),
    ('jid',note_jid),
    ('user',note_owner_email),
    ('user_id',note_owner_id),
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
    rows = []
    for u in users:
        for n in jv3.models.Note.objects.filter(owner=u):
            rows.append( [ f[1](n) for f in stat_fns ] )
    return rows

       
#print notes(authmodels.User.objects.filter(email="emax@csail.mit.edu"))
#print make_spreadsheet(notes_statistics(),col_headers=[x[0] for x in note_statistic_fns])
   


