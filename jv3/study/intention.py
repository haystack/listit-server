
import sys,os
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.diagnostic_analysis as da
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas
import jv3.study.wFunc as wF
from jv3.study.study import *
from jv3.study.thesis_figures import n2vals
from numpy import array
import jv3.study.content_analysis as ca
import codecs,json,csv
from django.utils.simplejson import JSONEncoder, JSONDecoder
import rpy2,nltk,rpy2.robjects
import jv3.study.note_labels as nl
import jv3.study.aov_utils as au
#r = ro.r <-- changed this by logging into mvk for a few seconds
## This was breaking note_intent site

r = rpy2.robjects.r
ro = rpy2.robjects
r = ro.r
c = lambda vv : apply(r.c,vv)
notepool = [2983,92830,9283,19283,8923,1982,3892,19293,74,5939,9583,2787,374,849,982,849,2313]
N = 250

cats = ["memory trigger","reference","external cognition", "journal/activity log", "posterity"]
columns = ['coder','owner_id','jid','contents','primary']+cats

primary = ['external cognition', 'journal/activity log','memory trigger','posterity','reference']
levels = ['1- no', '2- unlikely', '3- could be', '4- likely', '5- definitely']

def get_column_index(name): return columns.index(name)
def augmented_get_column_index(name):
    return columns.index(name)+1 # with note id as 0
aci = augmented_get_column_index

## two methods to get note intention - just the primary cat or secondaries >= 3
def get_note_intention_just_primary(arows,nid):
    ff = nltk.FreqDist([row[aci('primary')] for row in filter(lambda x : x[0] == nid,arows)])
    return ff.max()

def get_note_intention_anything_over_thresh(arows,nid,thresh=4):
    hits = [row for row in filter(lambda x : x[0] == nid,arows)]
    return list(set( reduce(lambda x,y:x+y, [[c for c in cats if levels.index(arow[aci(c)]) >= thresh-1] for arow in hits], []) + [arow[aci('primary')]] ))

## set it here ##
get_note_intention = get_note_intention_just_primary
#get_note_intention = get_note_intention_anything_over_thresh
get_note_role = get_note_intention

def read(filename=None):
   csv.field_size_limit(1000000000)
   f0 = "%s/%s" % (settings.STUDY_INTENTION_DIR, "index.csv" if filename is None else filename )
   datas = []
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      [datas.append(r) for r in rdr]
      F.close()
   return datas[1:]

def _write(datas):
    import csv,settings,time
    csv.field_size_limit(1000000000)
    f0 = "%s/%s" % (settings.STUDY_INTENTION_DIR,"index.csv")
    f1 = "%s/%s" % (settings.STUDY_INTENTION_DIR,"index-%d-%d-%d%d.csv" % (time.localtime().tm_year,
                                                                          time.localtime().tm_mon,
                                                                          time.localtime().tm_mday,
                                                                          time.localtime().tm_hour))
    for f in [f0,f1]:
        F = open(f,'w')
        wtr = csv.writer(F)      
        row_keys = columns
        def check_type(s):
            if isinstance(s,basestring):
                return s.encode('ascii','ignore')
            return s
        wtr.writerow(columns)
        [ wtr.writerow([check_type(x) for x in data]) for data in datas ]
        F.close()
        pass
    pass

def _get_all_note_ids():
    return [ int(x["id"]) for x in nl.read()["notes"] ]

def _get_random_note_ids(notepool_to_start=None):
    import random
    notepool = _get_all_note_ids() if notepool_to_start is None else notepool_to_start
    print "sampling ", N, " from ", len(notepool)
    return random.sample(notepool,min(len(notepool),N))

# --------------------- views ------------------------------------     
def get_notes(request,maximize_infrequent=True):
    note_pool = None
    if maximize_infrequent:
        note_pool = choose_underrepresented()
        print "underrpresented ", len(note_pool)

    selected = _get_random_note_ids(note_pool)
    selected.sort()
    print 'SELECTED ', selected[0:25]
    print Note.objects.filter(id=selected[0]).values()
    ss = [x for x in Note.objects.filter(id__in=selected).values('owner_id','jid','contents')]
    return HttpResponse(json.dumps(ss),"text/json")

def tally_votes(rows):
    import nltk
    # return r.sort( r.table( r.factor(c([x[0] for x in rows]) ) ) )
    return nltk.FreqDist([x[0] for x in rows])

def choose_underrepresented():  # used by view code up above
    ns = _get_all_note_ids()
    augmented = reada()
    augmented_tally = tally_votes(augmented)
    xu = [nid for nid in ns if (nid not in augmented_tally.keys()) or (augmented_tally[nid] == 1)]
    for xid in xu:
        print xid,"-",augmented_tally.get(xid,0)
    return xu

def post_intention(request):
    rpd = request.raw_post_data
    print "rpd ", rpd, type(rpd)
    newsintentions = JSONDecoder().decode(rpd)['results'] # json.loads(request.raw_post_data)
    d = read()
    for ni in newsintentions:
        print ni
        r = []
        for c in columns:  r.append(ni.get(c,None))
        d.append(r)
    _write(d)
    return HttpResponse("{}","text/json")    

# ------------------- intention analysis -------------------------

def _get_all_intention_ids():
    return set([ int(x[0]) for x in reada() ])

def reada(filename="index.csv"):
    csv.field_size_limit(1000000000)  ##problem, Error: field larger than field limit (131072)
    ## http://lethain.com/entry/2009/jan/22/handling-very-large-csv-and-xml-files-in-python/
    foor=read(filename)
    gci = get_column_index
    # augment with noteid to make augmented 
    return [ [Note.objects.filter(owner=x[gci('owner_id')],jid=x[gci('jid')])[0].id] + x for x in foor if not x[gci('primary')] == '-no idea-']

## how many do we have for each note ?

def build_fleiss(arows, n_raters=2): # augmented rows
    # |primary| x |primary| array
    # row per note, column per rater.... we'll see how this goes!
    n_skipped = 0
    rater_names = [ 'rater_%s' % i for i in xrange(n_raters) ]
    scores_by_rater = [ r.c() ]*n_raters
    print scores_by_rater
    notes = list(set([x[0] for x in arows]))
    for noteid in notes:
        hits = filter(lambda r : r[0] == noteid, arows)
        distinct_coders = set([h[aci('coder')] for h in hits])
        if len(distinct_coders) < n_raters:
            print "skipping note ", noteid, " because had raters ", len(distinct_coders)
            n_skipped = n_skipped + 1
            continue;
        # choose two
        coders = random.sample(distinct_coders,n_raters)
        for coder_i in xrange(len(coders)):
            primary = filter(lambda r: r[aci('coder')] == coders[coder_i], hits)[0][aci('primary')]
            scores_by_rater[coder_i] = r.c(scores_by_rater[coder_i], primary)
    return ro.DataFrame(dict(zip(rater_names, scores_by_rater)))


    
    
def _collect_all_ratings(arows,threshold='4- likely'):#'3- could be'):
    # primary is redundant since it will be set
    good_levels = levels[levels.index(threshold):]
    results = []
    # print 'good levels', good_levels
    # for r in arows:
    #     print r
    #     print [ c for c in cats ] 
    #     results.append([ c for c  in cats if r[aci(c)] in good_levels ])
    # return reduce(lambda x,y: x+y, results, [])
    return reduce(lambda x,y: x+y, [ [ c for c in cats if r[aci(c)] in good_levels ] for r in arows ], [])

def build_max_fleiss(arows, n_raters=2): # augmented rows
    # |primary| x |primary| array
    # row per note, column per rater.... we'll see how this goes!
    n_skipped = 0
    rater_names = [ 'rater_%s' % i for i in xrange(n_raters) ]
    scores_by_rater = [ r.c() ]*n_raters
    notes = list(set([x[0] for x in arows]))
    for noteid in notes:
        hits = filter(lambda r : r[0] == noteid, arows)
        distinct_coders = set([h[aci('coder')] for h in hits])        
        if len(distinct_coders) < n_raters:
            print "skipping note ", noteid, " because had raters ", len(distinct_coders)
            n_skipped = n_skipped + 1
            continue;
        # choose two

        coders = random.sample(distinct_coders,n_raters)
        cat_freqdist = nltk.FreqDist(_collect_all_ratings(filter(lambda r: r[aci('coder')] in coders, hits)))
        for coder_i in xrange(len(coders)):
            coded = filter(lambda r: r[aci('coder')] == coders[coder_i], hits)[0]
            options = [(cat,cat_freqdist[cat]) for cat in _collect_all_ratings([coded])]
            options.sort(key=lambda x:-x[1])
            best_cat = options[0][0]
            print "best cat",options," -- ",best_cat, " - (",cat_freqdist
            scores_by_rater[coder_i] = r.c(scores_by_rater[coder_i],best_cat)
    return ro.DataFrame(dict(zip(rater_names, scores_by_rater)))

def eliminate_duplicate_ratings_of_the_same_note_by_the_same_coder(arows):
    #  we do this horrible thing to get rid of duplicates by the same coder
    toret =  (dict([( str(x[aci('coder')])+'-note-'+str(x[0]),x) for x in arows])).values()
    print toret
    return toret

# this is broken - needs to be fixed to incorporate the 
# def primary_correlation_table(arows):
#     catdist = {}
#     prifreq = {}
#     #  we do this horrible thing to get rid of duplicates by the same coder
#     n_notes = len(set([x[0] for x in arows if not x[aci('primary')] == '-no idea-']))
#     arows = eliminate_duplicate_ratings_of_the_same_note_by_the_same_coder(arows)
#     print "n notes ", n_notes
#     for primary in cats:
#         hits = filter(lambda r: r[aci('primary')] == primary,arows)
#         prifreq[primary] = len(set([x[0] for x in hits]))/(1.0*n_notes) # unique notes in 
#         notes = set([x[0] for x in hits])  # notes that have primary category primary
#         secondary_ratings = nltk.FreqDist([])
#         for n in notes:
#             nhits = filter(lambda r:r[0] == n,hits)
#             secondary_ratings = secondary_ratings + nltk.FreqDist(filter(lambda c: not c == primary, _collect_all_ratings(nhits)))
#         catdist[primary] = [(x,y/(1.0*len(notes))) for x,y in secondary_ratings.iteritems()]
#     return catdist,prifreq

def secondary_flat_correlation(arows):  # takes .aread()
    catdist = {}
    catfreq = {}
    catnumber = {}
    notes = set([x[0] for x in arows if not x[aci('primary')] == '-no idea-'])
    arows = eliminate_duplicate_ratings_of_the_same_note_by_the_same_coder(arows)
    n_notes = len(notes)
    print "n notes ", n_notes
    for cat in cats:
        # first collect all rows that have cat c
        cat_ratings = filter(lambda r: cat in _collect_all_ratings([r]),arows)
        cat_notes = set([x[0] for x in cat_ratings])
        n_cat_notes = len(cat_notes)
        catfreq[cat] = n_cat_notes/(1.0*n_notes)
        catnumber[cat] = n_cat_notes
        secondary_ratings = nltk.FreqDist([])
        for n in cat_notes:            
            n_ratings = filter(lambda r:r[0] == n,arows)
            # take union over everyone's votes FOR THAT NOTE but only count them once
            new_tags = list(set(filter(lambda c: not c == cat, _collect_all_ratings(n_ratings)))) # count singly.
            secondary_ratings = secondary_ratings + nltk.FreqDist(new_tags)
        catdist[cat] = [(x,y/(1.0*n_cat_notes)) for x,y in secondary_ratings.iteritems()]

    # estimate tags per note

    note_ratings = lambda n : filter(lambda r:r[0] == n,arows)
    note_tags_union = lambda n : set(_collect_all_ratings(note_ratings(n)))

    tags_per_note = sum([len(note_tags_union(n)) for n in notes]) / (1.0*n_notes)
    
    return catdist,catnumber,catfreq,tags_per_note,n_notes

def get_notes_of_cat(arows,cat):
    # takes aread() and "memory trigger", usses secondary ratings flat
    cat_ratings = filter(lambda r: cat in _collect_all_ratings([r]),arows)
    return set([x[0] for x in cat_ratings])

def get_nls_for_note(nid,nlread=None):
    # nlread = nl.read()
    if nlread is None: nlread = nl.read()
    N = filter(lambda n_: n_["id"] == str(nid), nlread["notes"])
    if len(N) == 0:
        print "nothing found for ",nid
        return None
    N = N[0]
    return [N[field] for field in nlread["label_fields"]]

def get_nl_dist_for_cats(arows):
    nlread = nl.read()
    freqs = dict([ (cat, nltk.FreqDist()) for cat in cats ] )
    ntotals = dict([(cat,0) for cat in cats])
    for cat in cats:
        for n in get_notes_of_cat(arows,cat):
            freqs[cat] = freqs[cat] + nltk.FreqDist(get_nls_for_note(n,nlread))
        ntotals[cat] = ntotals[cat] + len(get_notes_of_cat(arows,cat))

    # now do some printing

    for cat in cats:
        xx = [(t,y) for t,y in freqs[cat].iteritems()]
        xx.sort(key=lambda tagfreq:-tagfreq[1])
        print cat,"---",xx,"\nPERCENTAGES",[(t,y/(1.0*ntotals[cat])) for t,y in xx],"\n\n"
        
    return freqs,ntotals[cat] #,[(cat,dict([ (tag,y/(1.0*ntotals[cat])) for tag,y in freqs[cat].iteritems() ])) for cat in cats]

owner_orm = lambda oid : User.objects.filter(id=oid)[0]
note_orm = lambda nid : Note.objects.filter(id=nid)[0]
default_features = [ca.note_words, ca.note_lines]

def _gfanalyze(notes,feature_list,fset_names=None):
    if fset_names is None:  fsetnames = [ ('feature_%d' % i) for i in xrange(len(feature_list))]    
    features = []
    for feat in feature_list:  features.append([feat(n).values()[0] for n in notes])
    print "means: ",[mean(x) for x in features]
    print "vars: ",[ca.var(x) if len(x) > 1 else "ZEROLENGTH" for x in features ]
    print "max: ",[max(x) for x in features]
    print "min: ",[min(x) for x in features]

    # try:
    #     for result in features:
    #         print "-------------",fset_names[features.index(result)], "-------------------"
    #         print r.stem(c([log(x+1)/log(2) for x in result]))
    # except:
    #     print sys.exc_info();    
    
    return features

def _gfcompare(fl1,fl2,fset_names = None):
    if fset_names is None:  fset_names = [ ('feature_%d' % i) for i in xrange(len(fl1))]    
    rets = {}
    for fset_i in xrange(len(fl1)):
        # print "testing",fset_names[fset_i]
        toret = r('t.test')(c(fl1[fset_i]),c(fl2[fset_i]))
        rets[fset_names[fset_i]] = toret
    return rets

def tp(ttest,label=None):
    if label is not None: print label,"-------------------------"
    for x in xrange(8):
        print ttest[x]

note_ratings = lambda n,arows: filter(lambda r:r[0] == n,arows)
owners = lambda arows: set([x[aci('owner_id')] for x in arows])
notes = lambda arows: set([x[0] for x in arows if not x[aci('primary')] == '-no idea-'])

def get_features_of_cat(arows,feature_list=None):
    # makes a nice table of statistics ~~
    if feature_list is None: feature_list = default_features
    # baseline - let's find the stats of all the owners of the notes
    owners = set([x[aci('owner_id')] for x in arows])
    owners = filter(lambda oid: owner_orm(oid) not in cal.RESEARCHERS,owners)
    notes_of_owners = reduce(lambda x,y:x+y,[[n for n in owner_orm(o).note_owner.all().values()] for o in owners])

    print "----------------------------------------------------------------------ALL -----------------------------------"
    fsetnames = ['words','lines']
    group_features = _gfanalyze(notes_of_owners,feature_list,fsetnames)

    # now partition by cats?
    notes = set([x[0] for x in arows if not x[aci('primary')] == '-no idea-'])
    cat_test = {}
    for cat in cats:
        print "--------------:",cat,":-----------------------------"
        cat_notes = Note.objects.filter(id__in=[ n for n in notes if cat in _collect_all_ratings( note_ratings(n,arows) ) ]).values()
        cat_features = _gfanalyze(cat_notes,feature_list,fsetnames)
        cat_test[cat] = _gfcompare(cat_features,group_features,fsetnames)
        
    return notes_of_owners,cat_test

import math
def entropy(freqdist):
    probs = [freqdist.freq(l) for l in freqdist]
    ent = -sum([p * math.log(p,2) for p in probs])
    return ent

def agreements(arows):
    import nltk
    s = ''
    aci = augmented_get_column_index
    coders = list(set([x[aci('coder')] for x in arows]))
    notes = list(set([x[0] for x in arows]))
    results = []
    for nid in notes:
        hits = filter(lambda r : r[0] == nid, arows)
        if len(hits) == 1: continue
        primaries = [x[aci('primary')] for x in hits]
        intent_dist = nltk.FreqDist(primaries)
        ent = entropy(intent_dist)
        results.append(ent)
        if ent > 0.5:
            s+=" ".join(["-----------\n",hits[0][aci('contents')], "\n", str(intent_dist), "\n"])
    return results,s

def get_feature_for_note(nid,feature_name,coerce_fn=lambda x: float(x)):
    nlread = nl.read()
    N = filter(lambda n_: n_["id"] == str(nid), nlread["notes"])
    if len(N) == 0 or feature_name not in nlread['note_fields'] + nlread['feature_fields'] + nlread['label_fields']:
        ## debug
        # if len(N) == 0:
        #             print "warning unknown note computing ", nid, feature_name
        #         else:
        #             print "unknown feature name, trying to compute ", feature_name
        
        #print "result .... ", Note.objects.filter(id=nid).count(), nl.feature_named(feature_name,Note.objects.filter(id=nid).values()[0])
        return nl.compute_feature_named(feature_name,Note.objects.filter(id=nid).values()[0])

    N = N[0]
    return coerce_fn(N[feature_name])

####################################################################
## anovas for note roles
## e.g.,
## fmla = aov(arows,'note_length')
## x,y,z = plotTukeyHSD(fmla)

def aov_old(arows, feature_name, formula = "%s ~ cat + participant"):
    fla = formula % feature_name
    fmla = ro.Formula(fla)
    env = fmla.environment
    feats = r.c()
    owners = r.c()
    cats = r.c()
    for row in arows:
        rf = get_feature_for_note(row[0],feature_name)
        if rf is None: continue
        feats = r.c(feats,rf)
        cats = r.c(cats,row[aci('primary')])
        owners = r.c(owners,row[aci('owner_id')])

    print "resulting rows", len(feats)
    env[feature_name] = feats
    env['cat'] = r('as.factor')(cats)
    env['participant'] = r('as.factor')(owners)

    print 'feats', env[feature_name]
    print 'cat', env['cat']
    print 'part', env['participant']
    
    return fmla

## intention aov -- 
def aov(arows, feature_name, formula = "%s ~ primary + owner_id"):
    import jv3.study.keeping_labels
    get_note_owner = lambda nid: filter(lambda x :x[0]==nid, arows)[0][aci('owner_id')]
    feature_functions = {
        feature_name : lambda note_id: get_feature_for_note(note_id,feature_name),
        'primary' : lambda nid: get_note_role(arows,nid),
        'owner_id' : get_note_owner
    }
    note_ids = list(set([x[0] for x in arows]))
    # key element: b
    fmla = au.make_fmla_repeat_when_lists(formula % feature_name, note_ids, feature_functions, ['primary', 'owner_id'])
    au.compute_averages(note_ids,feature_functions,feature_name,'primary')    
    return fmla

aov_new = aov
# largely a failed experiment - p values blow up completely because
# we assign things to unknown category
def aov_padded(arows, feature_name, min_N_per_user=20, formula = "%s ~ cat + participant"):
    fla = formula % feature_name
    fmla = ro.Formula(fla)
    fmla.environment = ro.Environment()
    env = fmla.environment
    feats = r.c()
    owners = r.c()
    cats = r.c()
    for row in arows:
        rf = get_feature_for_note(row[0],feature_name)
        if rf is None: continue
        feats = r.c(feats,rf)
        cats = r.c(cats,row[aci('primary')])
        owners = r.c(owners,row[aci('owner_id')])


    # if we have less than N notes per person, we have less than a representative sample :(
    # so, to prevent the world from blowing, we fill in     
        
    notes_per_owner_in_arows = nltk.FreqDist( [ row[aci('owner_id')]  for row in arows ] )
    note_ids = set( [row[0] for row in arows ])
    for owner_id,v in notes_per_owner_in_arows.iteritems():
        owned_notes_not_yet_chosen = [x for x in User.objects.filter(id=owner_id)[0].note_owner.all() if x.id not in note_ids and len(x.contents.strip()) > 0]
        if v < min_N_per_user:
            to_choose_k = min(len(owned_notes_not_yet_chosen),min_N_per_user-v)
            chosen = random.sample(owned_notes_not_yet_chosen,to_choose_k)
            assert to_choose_k == len(chosen), "Could not find note, somethings wrong %d %d" % (to_choose_k , len(chosen) )
            for chnote in chosen:
                feat = nl.compute_feature_named(feature_name,chnote)
                feats = r.c(feats,nl.compute_feature_named(feature_name,chnote))
                cats = r.c(cats,'uncategorized')
                owners = r.c(owners,owner_id)
            print "adding ",to_choose_k," to ", owner_id

    env[feature_name] = feats
    env['cat'] = r('as.factor')(cats)
    env['participant'] = r('as.factor')(owners)

    print 'feats', env[feature_name]
    print 'cat', env['cat']
    print 'part', env['participant']
    return fmla

# experiment #2 - strip people that are below N
def aov_stripped(arows, feature_name, min_N_per_user=5, formula = "%s ~ cat + participant"):
    fla = formula % feature_name
    fmla = ro.Formula(fla)
    fmla.environment = ro.Environment()
    env = fmla.environment
    feats = r.c()
    owners = r.c()
    cats = r.c()
    notes_per_owner_in_arows = nltk.FreqDist( [ row[aci('owner_id')]  for row in arows ] )
    owner_keepers = [owner for owner,notes in notes_per_owner_in_arows.iteritems() if notes > min_N_per_user]
    print "reducing from " , len(notes_per_owner_in_arows), " to ", len(owner_keepers)
    for row in arows:
        if row[aci('owner_id')] in owner_keepers:
            rf = get_feature_for_note(row[0],feature_name)
            if rf is None: continue
            feats = r.c(feats,rf)
            cats = r.c(cats,row[aci('primary')])
            owners = r.c(owners,row[aci('owner_id')])

    print "resulting rows  ", len(feats)
        
    env[feature_name] = feats
    env['cat'] = r('as.factor')(cats)
    env['participant'] = r('as.factor')(owners)

    print 'feats', env[feature_name]
    print 'cat', env['cat']
    print 'part', env['participant']
    
    return fmla

def owner_hist(arows):
    owners = r('as.factor')(c([row[aci('owner_id')] for row in arows]))
    return owners

def plotTukeyHSD(feature_name,fmla):
    import StringIO
    tsdres = StringIO.StringIO()    
    name_aov = cap.make_filename('aov_%s' % feature_name)
    name_tsd = cap.make_filename('tsd_%s' % feature_name)
    r.png(name_aov)
    aov = r('aov')(fmla)
    print "AOV"
    print >>tsdres,r.summary(aov)
    r.plot(aov)
    r('dev.off()')
    tsd = r('TukeyHSD')(aov)
    print "TSD"
    print >>tsdres,tsd
    print r.summary(tsd)
    r.png(name_tsd)
    r.plot(tsd)
    r('dev.off()')
    return name_aov,name_tsd,tsdres.getvalue(),aov,tsd
    
# overall interesting

def compute_avg_for_overall_interesting(interesting_users,feature_name):
    interesting_notes = reduce(lambda x,y: x+y, [ list(i.note_owner.all().values()) for i in interesting_users])
    def printstats(varr):
        return [("len: ", len(varr)),
                ("mean: ",mean(varr)),
                ("median: ",median(varr)),
                ("min ", min(varr)),
                ("max ", max(varr)),               
                ("stdev:", pow(ca.var(varr),0.5) if len(varr) > 1 else "CANT COMPUTE len = 1")]

    
    print printstats([ nl.compute_feature_named(feature_name, n) for n in interesting_notes if nl.compute_feature_named(feature_name, n) is not None and nl.compute_feature_named(feature_name, n) >= 0])
    
    
