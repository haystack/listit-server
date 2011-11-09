
import jv3.models as m
import django.contrib.auth.models as dm
import nltk

# takes all notes that have duplicate jids and determines whether
# they're textually different, .. 
def find_dupes(user=None):
    if user is None: user = dm.User.objects.filter(email='emax@csail.mit.edu')[0]
    mismatched = []
    for jid in [x[0] for x in user.note_owner.values_list('jid')]:
        if user.note_owner.filter(jid=jid).count() > 1 :
            t1,t2 = [x[0] for x in user.note_owner.filter(jid=jid).values_list('contents')]
            if not t1 == t2:
                print "jid ", jid, ' ids ', user.note_owner.filter(jid=jid).values_list('id')
                print "T1 : ", t1.replace('\n', ' '), len(t1)
                print "T2 : ", t2.replace('\n', ' '), len(t2)
                print "=========="
                mismatched.append(jid)
    return mismatched

# finds people who have dupes and their situation
def find_people_with_dupes(user_ids=None):
    users = dm.User.objects.all()
    if user_ids: users = dm.User.objects.filter(id__in=user_ids)
    result = []
    for u in users:
        # find discrepancies
        unique_jids = set([x[0] for x in u.note_owner.values_list('jid')])
        n_notes = len(set([x[0] for x in u.note_owner.values_list('id')]))
        foo = [u.note_owner.filter(jid=j).count() for j in unique_jids]
        foo = filter(lambda x : x > 1, foo)
        if len(foo) == 0: continue
        result.append( (u.id , max(foo), len(foo), len(foo)/(1.0*n_notes)) )                               
    return result    
