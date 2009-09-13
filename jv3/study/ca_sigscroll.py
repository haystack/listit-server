
from jv3.models import *
from django.utils.simplejson import JSONEncoder, JSONDecoder
from django.contrib.auth.models import User

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

def note_ss(note,days_ago=None):
    from jv3.study.content_analysis import activity_logs_for_user
    global sigscroll_cache_days_ago
    global sigscroll_startend_cache
    global sigscroll_dur_totals_cache
    
    if sigscroll_startend_cache.has_key(note["owner"]) and days_ago == sigscroll_cache_days_ago:
        # cache hit, and we are reading the right data
        return {'sigscroll_counts': len(sigscroll_startend_cache[note["owner"]].get(note["id"],[])),
                'sigscroll_duration': sigscroll_dur_totals_cache[note["owner"]].get(note["id"],0) }
    
    # reset.
    if not days_ago == sigscroll_cache_days_ago:
        sigscroll_cache_days_ago = days_ago
        sigscroll_dur_totals_cache = {}
        sigscroll_startend_cache = {}

    ## recompute! owner specific
    owner_ss_dur = {}
    owner_startends = {} # new startend cache for owner
    # retrieve _all_ sigscrolls for this owner
    #print "-> actlogsforuser %d " % note["owner"]
    alogs = activity_logs_for_user(note["owner"],"significant-scroll",days_ago)
    #print "-> actlogsforuser %d " % alogs.count()
    for al_i in range(alogs.count()):
        al = alogs[al_i]
        #print "boop"
        if al["search"] is None:
            continue
        for nv in JSONDecoder().decode(al["search"])["note_visibilities"]:
            try :
                jid = int(nv["id"]) ## this returns the _jid_ not id!
                nvid = Note.objects.filter(owner=note["owner"],jid=jid)[0].id
                owner_ss_dur[nvid] = sigscroll_dur(owner_ss_dur.get(nvid,0),nv)
            ## update the startend
                if nv.has_key("exitTime") and nv.has_key("entryTime"):
                    ap = owner_startends.get(nvid,[])
                    if nv["entryTime"] == nv["exitTime"]:
                        ## this is to get around the bug in 0.4.5-7 which
                        ## results in (start,start) for no-scroll open-close, and search/idle
                        ap.append( (nv["entryTime"],long(al["when"])) )
                    else:
                        ap.append( (nv["entryTime"],nv["exitTime"]) )
                    owner_startends[nvid] = ap
            except:
                pass
                
    sigscroll_dur_totals_cache[note["owner"]] = owner_ss_dur
    sigscroll_startend_cache[note["owner"]] = dict( [ (nid,adjacent_filtered(views)) for nid,views in owner_startends.iteritems() ] )

    ## now compute the desired things    
    return {'sigscroll_counts': len(sigscroll_startend_cache[note["owner"]].get(note["id"],[])),
            'sigscroll_duration': sigscroll_dur_totals_cache[note["owner"]].get(note["id"],0) }

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
    #print ss_send_cache[n["owner"]]
    visitations = ss_send_cache[n["owner"]].get(n["id"],[])
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
                       title="%d[%d] (%s:%d) %s "% (n["id"],len(n["contents"]),n["owner"].email,_owner_count_notes(n["owner"]), n["contents"][:25].replace('\n',' ')),
                       ylabel="# of reaccess")


    

    
        
    
