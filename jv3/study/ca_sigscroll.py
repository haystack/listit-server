
from jv3.models import *
from django.utils.simplejson import JSONEncoder, JSONDecoder
from django.contrib.auth.models import User
import sys,json,time

## signifiant scroll stuff ##
sigscroll_cache_days_ago = None
sigscroll_dur_totals_cache = {}
sigscroll_startend_cache = {}

def ca_caches():
    return {"sigscroll_cache_days_ago":sigscroll_cache_days_ago,
            "sigscroll_dur_totals_cache":sigscroll_dur_totals_cache,
            "sigscroll_startend_cache":sigscroll_startend_cache }            

sigscroll_count = lambda prev_count,ssevt: prev_count + 1

def sigscroll_dur(prev_count,ssevt):
    if ssevt.has_key("exitTime") and ssevt.has_key("entryTime"):
        return prev_count + (ssevt["exitTime"] - ssevt["entryTime"])/60000.0
    return prev_count

send_visitation_durations = lambda note_visitations: [ end-start for start,end in note_visitations ]

def inter_visitation_duration(x):
    return lambda x: reduce(lambda x,y: x+y, send_visitation_durations(x))

def adjacent_filtered(views):
    ## takes [(t1,t2),(....).....]
    ## filters adjacent dudes [(1,2),(2,3)] -> [(1,3)]
    ## totally uncool.
    result = []
    if len(views) < 2:
        return views
    cur = views[0]
    for v in views[1:]:
        if v[0] == cur[1]:
            cur = (cur[0],v[1])
        else:
            result.append(cur)
            cur = v
    result.append(cur)
    return result


def get_ss_revisitations_for(n):
    if n["owner_id"] not in __sigscroll_cache_owners:
    # if n["id"] not in __sigscroll_startend_cache_flat:
        note_ss(n)
        __sigscroll_cache_owners.append(n["owner_id"])
    return __sigscroll_startend_cache_flat.get(n["id"],None)
    
__sigscroll_startend_cache_flat = {}
__sigscroll_cache_owners = []
def note_ss(note,filter_top=False):
    from jv3.study.content_analysis import activity_logs_for_user
    from jv3.study.ca_load import jid2nidforuser
    global __sigscroll_startend_cache_flat
    SSCF = __sigscroll_startend_cache_flat

    def compute_duration(note):
        def dur(send):
            if type(send) == tuple: return send[1]-send[0]
            return send        
        xd = SSCF.get(note["id"],[])
        if len(xd) > 1:
            return reduce(lambda x,y: dur(x)+dur(y),xd)
        elif len(xd) == 1:
            return dur(xd[0])
        return -1
    
    if note["id"] in SSCF :
        return {'sigscroll_counts': len(SSCF.get(note["id"],[])), 'sigscroll_duration': compute_duration(note) }

    ## populate for this uer
    alogs = activity_logs_for_user(note["owner_id"],None)
    
    # if len(alogs) == 0:
    #     ## means we have no activitylogs for that user
    #     from jv3.study.content_analysis import _notes_to_features
    #     SSCF.update( [ (n["id"],[]) for n in [_notes_to_values(x) for x in Note.objects.filter(owner=n["owner_id"])] ] )
    #     return

    debug__all_nids = []
    
    next_is_top = True    
    toplist_jids = [] # things to block
    alogs.sort(key=lambda x: x["when"])
    print "activity logs", len(alogs)
    for al_i in range(len(alogs)):
        print al_i
        al = alogs[al_i]        
        if al["action"] == 'sidebar-open':
            next_is_top = True
            continue
        if not al["action"] == "significant-scroll":
            continue
        if al["search"] is None: 
            print "skipping"
            continue
        al["search"] = json.loads(al["search"])        
        if next_is_top:
            toplist_jids = [long(nv["id"]) for nv in al["search"]["note_visibilities"]]
            ##print "TOPLIST :: %s " % repr(toplist_jids)
            next_is_top = False 
        for nv in al["search"]["note_visibilities"]: 
            try :
                jid = int(nv["id"]) ## this returns the _jid_ not id!
                debug__all_nids.append(jid)
                ## omit nots that are at the top of the list
                if filter_top and jid in toplist_jids:
                    print "filter top and jid in toplist continuing"
                    continue                
                nid = jid2nidforuser(al["owner"],jid)  ## convert to NID (guaranteed unique)
                if nv.has_key("exitTime") and nv.has_key("entryTime"):
                    ap = SSCF.get(nid,[])
                    if nv["entryTime"] == nv["exitTime"]:
                        print " case 1 ",jid
                        ## this is to get around the bug in 0.4.5-7 which
                        ## results in (start,start) for no-scroll open-close, and search/idle
                        ap.append( (nv["entryTime"],long(al["when"])) )
                    else:
                        print "case 2 "
                        ap.append( (nv["entryTime"],nv["exitTime"]) )
                    SSCF[nid] = ap
            except:
                print "noncritical warn %s " % repr(sys.exc_info())
                pass
            
        ## filter all the newdudes
    print SSCF
    SSCF.update( dict([ (nid,adjacent_filtered(views)) for nid,views in SSCF.iteritems() ]) ) # if (nid in new_dudes) ] ) )

    print "all debug__all_nids",len(set(debug__all_nids))
    return {'sigscroll_counts': len(SSCF.get(note["id"],[])),'sigscroll_duration': compute_duration(note) }

def count_dur_per_note_per_user(durs=sigscroll_dur_totals_cache):
    return [ (owner,[ dur for note,dur in durs[owner].iteritems()]) for owner in durs.keys() ]

def number_of_revisitations_per_note_per_user(startends=sigscroll_startend_cache):
    # relies on running note_ss first
    assert len(startends) > 0, "need some startends!"
    return [ (owner,[ len(revisitation_vector) for note,revisitation_vector in startends[owner].iteritems()]) for owner in startends.keys()]

def nonzero_dur(vs,min_thresh=1):
    return [visit for visit in vs if len(visit) == 2 and (visit[1] - visit[0] >= min_thresh)]
    
def number_of_revisitations_per_user(startends=sigscroll_startend_cache,revisitation_filter=nonzero_dur):
    # relies on running note_ss first
    assert len(startends) > 0, "need some startends!"
    return [ (owner,reduce(lambda x,y: x+y, [ len(revisitation_filter(revisitation_vector)) for note,revisitation_vector in notations.iteritems() ])) for owner,notations in startends.iteritems() if len(notations) > 0 ]

def select_dudes_to_revisit(notevals,ss_send_cache=sigscroll_startend_cache,N=40):
    notes = {}
    for owner in ss_send_cache.keys():
        for nid,nvisits in ss_send_cache[owner].items():
            notes[nid] = notes.get(nid,0)+len(nvisits)
    notes_by_revisit = notes.keys()
    notes_by_revisit.sort( lambda xid,yid: notes[yid] - notes[xid] )
    for nid in notes_by_revisit[0:N]:
        print "revisit : %d, %d " % (nid, len([n for n in notevals if n["id"] == nid]))
        
        ##assert len([n for n in notevals if n["id"] == nid]) == 1, "foo bar, %d " % len([n for n in notevals if n["id"] == nid])
        hits = [n for n in notevals if n["id"] == nid]
        if len(hits) == 1:
            plot_revisitations_for_note([n for n in notevals if n["id"] == nid ][0],ss_send_cache,
                                        filename="/var/www/listit-study/revisits/revisit_dude_%d_%d.png" % (notes_by_revisit.index(nid),nid))
        else:
            print "skipping %d (%d)" % (nid,len(hits))

def _owner_count_notes(owner):
    if type(owner) == User:
        return owner.note_owner.all().count()
    if type(owner) == long:
        return User.objects.filter(id=owner)[0].note_owner.all().count()
    return None
    
def plot_revisitations_for_note(n,ss_send_cache=sigscroll_startend_cache,filename='/tmp/revisit.png'):
    import jv3.study.ca_plot as cap
    #print ss_send_cache[n["owne"]]
    visitations = ss_send_cache[n["owner_id"]].get(n["id"],[])
    granularity = lambda t: int(t/(24*3600.0*1000.0))
    maxt = -1
    y = {}
    first_visit = min([ s[0] for s in visitations ])
    #print visitations
    for s,e in visitations:
        t = granularity(s-first_visit)
        y[t] = y.get(t,0) + 1
        maxt = max(maxt,t)

    for ti in range(maxt):
        if ti not in y:  y[ti] = 0
        pass
    
    return cap.scatter(y.items(),filename=filename,
                       title="%d[%d] (%s:%d) %s "% (n["id"],len(n["contents"]),n["owner_id"].email,_owner_count_notes(n["owner_id"]), n["contents"][:25].replace('\n',' ')),
                       ylabel="# of reaccess")


    

    
def test_coverage(owner_id):
    owner = User.objects.filter(id=owner_id)[0]
    st = time.time()
    sig_notes = set([long(n["jid"]) for n in owner.note_owner.all().values() if get_ss_revisitations_for(n) is not None])
    print "---ss----",time.time()-st
    st = time.time()
    
    alog_test = set([long(al["noteid"]) for al in owner.activitylog_set.values() if al["noteid"] is not None])
    print "---al----",time.time()-st
    st = time.time()
    
    note_test = set([long(n.jid) for n in owner.note_owner.all()])
    print "---nid----",time.time()-st

    return len(sig_notes),len(note_test),len(alog_test),len(sig_notes.intersection(alog_test)),len(sig_notes.intersection(note_test)),len(alog_test.intersection(note_test)),owner.note_owner.filter(deleted=True).count()

def find_safe_users(userset):
    alog_note_ratios = []
    sig_alog_ratios=[]
    def test_user(u):
        print u
        sig,notes,alogs,x,y,a,d = test_coverage(u.id)
        alog_note_ratios.append( alogs/(1.0*notes) )
        print alogs/(1.0*notes),
        sig_alog_ratios.append(sig/(1.0*alogs))
        print sig/(1.0*alogs),
        print sig/(1.0*alogs) > 0.9
        return sig/(1.0*alogs) > 0.9
    return [u for u in userset if test_user(u)],alog_note_ratios,sig_alog_ratios


        
    
    
    
