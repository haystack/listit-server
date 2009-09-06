
from django.utils.simplejson import JSONEncoder, JSONDecoder

## signifiant scroll stuff ##
sigscroll_cache_days_ago = None
sigscroll_count_cache = {}
sigscroll_dur_totals_cache = {}
sigscroll_startend_cache = {}


sigscroll_count = lambda prev_count,ssevt: prev_count + 1
def sigscroll_dur(prev_count,ssevt):
    if ssevt.has_key("exitTime") and ssevt.has_key("entryTime"):
        return prev_count + (ssevt["exitTime"] - ssevt["entryTime"])/60000.0
    return prev_count

send_visitation_durations = lambda x: reduce(lambda x,y: x+y, [ end-start for start,end in x ])
def inter_visitation_duration(x):
    return lambda x: reduce(lambda x,y: x+y, [ end-start for start,end in x ])

def note_ss(note,days_ago=None):
    from jv3.study.content_analysis import activity_logs_for_user
    global sigscroll_cache_days_ago
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
    for al in activity_logs_for_user(note["owner"],"significant-scroll",days_ago): 
        if al["search"] is None:
            continue
        for nv in JSONDecoder().decode(al["search"])["note_visibilities"]:
            nvid = int(nv["id"])
            owner_ss_count[nvid] = sigscroll_count(owner_ss_count.get(nvid,0),nv)
            owner_ss_dur[nvid] = sigscroll_dur(owner_ss_dur.get(nvid,0),nv)

            if nv.has_key("exitTime") and nv.has_key("entryTime"):
                ap = owner_startends.get(nvid,[])
                ap.append( (nv["exitTime"],nv["entryTime"]) )
                owner_startends[nvid] = ap                       
                
    sigscroll_count_cache[note["owner"]] = owner_ss_count
    sigscroll_dur_totals_cache[note["owner"]] = owner_ss_dur
    sigscroll_startend_cache[note["owner"]] = owner_startends

    ## now compute the desired things
    
    
    return {'sigscroll_counts': sigscroll_count_cache[note["owner"]].get(note["jid"],0),
            'sigscroll_duration': sigscroll_dur_totals_cache[note["owner"]].get(note["jid"],0) }
