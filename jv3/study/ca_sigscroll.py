
from django.utils.simplejson import JSONEncoder, JSONDecoder

## signifiant scroll stuff ##
sigscroll_cache_days_ago = None
sigscroll_count_cache = {}
sigscroll_dur_totals_cache = {}
sigscroll_startend_cache = {}

def ca_caches():
    return {"sigscroll_cache_days_ago":sigscroll_cache_days_ago,
            "sigscroll_count_cache":sigscroll_count_cache,
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

def note_ss(note,days_ago=None):
    print "notess"
    from jv3.study.content_analysis import activity_logs_for_user
    global sigscroll_cache_days_ago
    global sigscroll_startend_cache
    global sigscroll_count_cache
    global sigscroll_dur_totals_cache
    
    if sigscroll_count_cache.has_key(note["owner"]) and days_ago == sigscroll_cache_days_ago:
        # cache hit, and we are reading the right data
        return {'sigscroll_counts': sigscroll_count_cache[note["owner"]].get(note["jid"],0),  'sigscroll_duration': sigscroll_dur_totals_cache[note["owner"]].get(note["jid"],0) }
    
    # reset.
    if not days_ago == sigscroll_cache_days_ago:
        sigscroll_cache_days_ago = days_ago
        sigscroll_count_cache = {}
        sigscroll_dur_totals_cache = {}

    ## recompute! owner specific
    owner_ss_count = {}
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
            nvid = int(nv["id"])
            owner_ss_count[nvid] = sigscroll_count(owner_ss_count.get(nvid,0),nv)
            owner_ss_dur[nvid] = sigscroll_dur(owner_ss_dur.get(nvid,0),nv)

            if nv.has_key("exitTime") and nv.has_key("entryTime"):
                ap = owner_startends.get(nvid,[])
                ap.append( (nv["entryTime"],nv["exitTime"]) )
                owner_startends[nvid] = ap                       
                
    sigscroll_count_cache[note["owner"]] = owner_ss_count
    sigscroll_dur_totals_cache[note["owner"]] = owner_ss_dur
    sigscroll_startend_cache[note["owner"]] = owner_startends

    ## now compute the desired things    
    return {'sigscroll_counts': sigscroll_count_cache[note["owner"]].get(note["jid"],0),
            'sigscroll_duration': sigscroll_dur_totals_cache[note["owner"]].get(note["jid"],0) }


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


    
