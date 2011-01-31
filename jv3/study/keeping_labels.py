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
import codecs,json,csv,StringIO
from django.utils.simplejson import JSONEncoder, JSONDecoder
import rpy2,nltk,rpy2.robjects
import jv3.study.note_labels as nl
import jv3.study.intention as intent
import jv3.study.wUserWalk as wuw


r = rpy2.robjects.r
ro = rpy2.robjects
c = lambda vv : apply(r.c,vv)

columns = ['userid','wolfe','emax','kat','wstyke','notes']
cats = ['packrat','neat freak','sweeper','revisaholic']

def get_user(rows,userid): return [row for row in rows if row['userid'] == userid][0]

def read(filename=None):
    # runs through all rows from spreadsheet, parses "unique" syntax into
    # an obj like:
    #
    # { 'userid': '4440',
    # 'emax': {'packrat': 3, 'sweeper': 3},
    # 'wolfe':{'packrat': 4,
    # 'notes': 'one big sweep of old notes',
    f = _read(filename)
    # augment dems with
    rets = []
    for row in f:
        consolidated = {}
        for c,parser in column_parsers.iteritems():
            ret = parser(row.get(c,None)) # parse it
            if ret is not None:
                row[c] = ret
                for cr,v in ret.iteritems(): consolidated[cr] = max(consolidated.get(cr,0),v)
        row['consolidated'] = consolidated
        rets.append(row)
    return  rets

def _read(filename=None):
   f0 = "%s/%s" % (settings.KEEPING_STYLE_DIR, "index.csv" if filename is None else filename )
   datas = []
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      [datas.append(dict(zip(columns,r))) for r in rdr]
      F.close()
   return datas[1:]

# not in use
# def _write(datas):
#     import csv,settings,time
#     f0 = "%s/%s" % (settings.KEEPING_STYLE_DIR,"index.csv")
#     f1 = "%s/%s" % (settings.KEEPING_STYLE_DIR,"index-%d-%d-%d%d.csv" % (time.localtime().tm_year,
#                                                                           time.localtime().tm_mon,
#                                                                           time.localtime().tm_mday,
#                                                                           time.localtime().tm_hour))
#     for f in [f0,f1]:
#         F = open(f,'w')
#         wtr = csv.writer(F)      
#         row_keys = columns
#         def check_type(s):
#             if isinstance(s,basestring):
#                 return s.encode('ascii','ignore')
#             return s
#         wtr.writerow(columns)
#         [ wtr.writerow([check_type(x) for x in data]) for data in datas ]
#         F.close()
#         pass
#     pass

# def parse_emax_all(rows,user_id):
#     print "looking for : ", user_id, type(user_id)
#     r = get_user(rows,user_id).get('emax',None)
#     if r is None or r == '' or  r.find('ins') >= 0 : return None
#     rs = [x for x in r.replace(';',' ').replace(' + ',' ').strip().split(' ') if len(x.strip()) > 0]
#     s = {}
#     print user_id,"_",rs
#     for r in rs:
#         print "arr is ",r
#         if r.find('NICE') == 0 or r.find('(NI') == 0:
#           s['NICE'] = True
#           continue
#         try:
#             category = cats[int(r[0])-1]
#             strength = ({'--':1,'-':2,'':3,'+':4,'++':5,'+++':5}).get(r[1:],0)
#             s[category]=strength
#         except:
#             print sys.exc_info()
#     return s

def parse_wolfe(row):
    r = row.get('wolfe',None)
    if r is None or r == '' or  r.find('-1') >= 0 : return None
    ##rs = [x for x in r.replace(';',' ').replace(' + ',' ').strip().split(' ') if len(x.strip()) > 0]
    s = {}
    print "reading wolfe on ",row["userid"],row["wolfe"]
    for rt in r:
        val = int(rt)
        print "Value is: ", val
        if val in [1,2,3]:
            category = cats[val-1]
            strength = 5
            s[category] = strength
        elif val == 4:
            return None
        elif val == 5:
            s[cats[0]] = 5
            s[cats[2]] = 5
        elif val == 6:
            s[cats[1]] = 5
            s[cats[2]] = 5
        elif val == 7:
            s[cats[0]] = 5
            s[cats[1]] = 5
    return s


def parse_emax(r):
    global cats
    if r is None or r == '' or  r.find('ins') >= 0:
        #print "Skipping empty/ins:",r
        return None
    if max([r.find('rain'), r.find('turn'), r.find('slow'), r.find('neat'), r.find('freak')]) >= 0:
        print "Skipping weird cases"
        return None
    rs = [x for x in r.replace(';',' ').replace(' + ',' ').strip().split(' ') if len(x.strip()) > 0]
    s = {}
    for r in rs:
        if r.find('NICE') == 0 or r.find('(NI') == 0:
          s['NICE'] = True
          continue
        try:
            if r == '!!' or r[0] == '[' or r[0] == '5' or r[0] == '0':
                continue
            category = cats[int(r[0])-1]
            strength = ({'--':1,'-':2,'':3,'+':4,'++':5,'+++':5}).get(r[1:],0)
            s[category]=strength
        except:
            print "Problem r[0]:", r[0], r
            print sys.exc_info()
    return s

default_note_features = [ca.note_words, ca.note_lines, ca.note_changed_edits, ca.note_lifetime]
default_user_features = [wuw.user_percent_active_days,
                         wuw.user_mean_alive_percent,
                         wuw.user_var_alive_percent,
                         wuw.user_mean_alive,
                         wuw.user_var_alive,
                         wuw.user_mean_dead,
                         wuw.user_var_dead,                                                  
                         wuw.user_mean_day_add,
                         wuw.user_var_day_add,
                         wuw.user_mean_day_del,
                         wuw.user_var_day_del,
                         wuw.user_mean_change,
                         wuw.user_var_change,
                         ]
default_note_feature_names = ['words','lines','edits','lifetime']
default_user_feature_names = ['active days',
                              'mean alive %',
                              'var alive %',
                              'mean alive N',
                              'var alive N',
                              'mean dead N',
                              'var dead N',
                              'mean new/day',
                              'var new/day',
                              'mean del/day',
                              'var del/day',
                              'mean change/day',
                              'var change/day',                              
                              ]

# mutually exclusve (harsh) category selector that only takes the
# maximum --- 
def get_owner_category(owner_id):
    # will err if owner_id is not known in krows
    kl_rows = read()
    return get_category([r for r in kl_rows if r['userid'] == owner_id][0])

    
def get_category(kl_row,min_thresh=3):
    if len(kl_row['consolidated']) == 0: return None
    maxv = max(kl_row['consolidated'].values())
    if maxv < min_thresh: return None
    topcats = [x for x,v in kl_row['consolidated'].iteritems() if v == maxv]
    topcats.sort()
    return topcats[0]

def is_member_of_category(kl_row,cat):
    min_thresh = 3
    if len(kl_row['consolidated']) == 0: return None
    maxv = max(kl_row['consolidated'].values())
    if maxv < min_thresh: return None
    topcats = [x for x,v in kl_row['consolidated'].iteritems() if v >= min_thresh]
    return cat in topcats


"""
none: 0
s: 194
r: 57
r+s: 41
n: 246
n+s: 155
n+r: 45
n+r+s: 35
p: 213
p+s: 71
p+r: 20
p+r+s: 13
p+n: 65
p+n+s: 46
p+n+r: 11
p+n+r+s: 10
"""

def category_truth_table():
    user_ratings = read()
    cats = ['packrat', 'neat freak', 'revisaholic','sweeper']
    truth_table = []
    for kl_row in user_ratings:
        user_cats = []
        for a in [0,1]:
            for b in [0,1]:
                for c in [0,1]:
                    for d in [0,1]:
                        is_member = True
                        if a == 1: # include packrat
                            is_member = is_member and is_member_of_category(kl_row,'packrat')
                        if b == 1:
                            is_member = is_member and is_member_of_category(kl_row,'neat freak')
                        if c == 1:
                            is_member = is_member and is_member_of_category(kl_row,'revisaholic')
                        if d == 1:
                            is_member = is_member and is_member_of_category(kl_row,'sweeper')
                        if a==0 and b==0 and c==0 and d==0:
                            is_member = False
                        user_cats.append(is_member)
        truth_table.append(user_cats)
    return truth_table

#for i in range(32):
#   .....:     len(filter(lambda x:x[i],rr))





def is_member_of_categories(kl_row,catArr):
    catCorr = []
    for catA in catArr:
        for catB in catArr:
            if (catA == catB): break
            if is_member_of_category(kl_row,catA) and is_member_of_category(kl_row,catB):
                catCorr.append(1)
            else:
                catCorr.append(0)
    return catCorr
            
def is_member_of_paired_cats():
    rows = kl.read()
    pairs=[]
    map(lambda x:ee.append(kl.is_member_of_categories(x, ['packrat', 'neat freak', 'revisaholic','sweeper'])),dd)


## p+n, p+r, p+s
## n+r, n+s
## r+s

#topcats.sort()
#    return topcats[0]


#    return get_category(kl_row) == cat

def get_userids_with_cat(arows,cat=None):
    if cat is None: return set([x["userid"] for x in arows])

    # used to be this one:
    # is_member_of_category = lambda x,cat : x['consolidated'].get(cat, 0) >= 3

    return set([x["userid"] for x in arows if arows is not None and is_member_of_category(x,cat)])


def get_features_of_styles(arows,note_feature_list=None,user_feature_list=None,note_feature_names=None,user_feature_names=None):
    # makes a nice table of statistics ~~
    arows = [a for a in arows if a.get('emax',None) is not None] # fiter out insub
    if note_feature_list is None: note_feature_list = default_note_features
    if user_feature_list is None: user_feature_list = default_user_features
    if note_feature_names is None: note_feature_names = default_note_feature_names
    if user_feature_names is None: user_feature_names = default_user_feature_names    
    owners = get_userids_with_cat(arows)
    owners = filter(lambda oid: intent.owner_orm(oid) not in cal.RESEARCHERS,owners)
    notes_of_owners = reduce(lambda x,y:x+y,[[n for n in intent.owner_orm(o).note_owner.all().values()] for o in owners])

    print "-----------ALL [", len(notes_of_owners)," from ",len(owners),"]"
    group_note_features = intent._gfanalyze(notes_of_owners,note_feature_list,note_feature_names)
    group_user_features = intent._gfanalyze(owners,user_feature_list,user_feature_names)

    # now partition by cats?
    cat_test = {}
    for cat in cats:
        users_with_cat = get_userids_with_cat(arows,cat)
        cat_notes =  reduce(lambda x,y: x+y,[[x for x in User.objects.filter(id=o)[0].note_owner.values()] for o in users_with_cat ])
        print "--------------:",cat,":--------------- (u=",len(users_with_cat),"n =", len(cat_notes),")"
        cat_note_features = intent._gfanalyze(cat_notes, note_feature_list)
        cat_user_features = intent._gfanalyze(users_with_cat, user_feature_list)        
        cat_test[cat] = intent._gfcompare(cat_note_features,group_note_features,note_feature_names)
        cat_test[cat].update( intent._gfcompare(cat_user_features,group_user_features,user_feature_names)  )
        
    return cat_test

########################################################################################
## new delicious anova code for CHI 2011 paper
## Figures 3 and 7 are generated from these fns
## 
## krows = kl.read()
## kl.print_aov_bits(krows,'note_words')
## kl.print_aov_bits(krows,'note_lines')
## kl.print_aov_bits(krows,'note_deleted')
## kl.print_aov_bits(krows,'note_lifetime_none')

_filter_user_ids_for_researchers = lambda users: filter(lambda oid: intent.owner_orm(oid) not in cal.RESEARCHERS, users)
_filter_missing_keeper_labels = lambda arows,labeler: filter(lambda arow: arow.get(labeler,None) is not None, arows)
_get_all_notes_owned = lambda dude_ids: reduce(lambda x,y:x+y,[[n for n in intent.owner_orm(o).note_owner.all().values()] for o in dude_ids])
_get_owners_of_rows = lambda arows: set([x["userid"] for x in arows])

def anova_by_note_feature(krows,feature_name):
    owners = _get_owners_of_rows(krows)
    owners = _filter_user_ids_for_researchers(owners)

    owner_types = {}
    for cat in cats:
        [ owner_types.update({long(owner) : cat}) for owner in get_userids_with_cat(krows,cat) ]

    # gets rid of dudes who have no category
    owners = list(owner_types.keys())
    notes_of_owners = _get_all_notes_owned(owners)                                                  

    def compfeat(n,name):
        #print "COMPFEAT ", name, " ", n["id"]
        #if intent.get_feature_for_note(n["id"],feature_name) < 0:
        #print "getting feature for note ", n["id"], intent.get_feature_for_note(n["id"],feature_name), feature_name, n["contents"][:10], 
        return intent.get_feature_for_note(n["id"],name)

    feature_functions =  {
        "owner_type" : lambda n : owner_types.get(n["owner_id"],None),
        "owner_id" : lambda n: n["owner_id"],
        feature_name : lambda n: compfeat(n,feature_name) # lambda n: intent.get_feature_for_note(n["id"],feature_name)
        }

    print "notes of owners ", len(notes_of_owners)
    fmla = _make_aov_fmla(
        '%s ~ owner_type + owner_id' % feature_name,
        notes_of_owners,
        feature_functions,
        ['owner_id','owner_type'])

    compute_averages(notes_of_owners,feature_functions,feature_name,'owner_type')
    
    aov = r('aov')(fmla)
    tsd = r('TukeyHSD')(aov)
    ios = StringIO.StringIO()
    print >>ios,r.summary(tsd)
    return fmla,aov,tsd,ios.getvalue()

def anova_by_user_feature(krows,feature_name):
    ## first get rid of owners that don't have a keeping category -- bamf!
    krows = filter(lambda x : get_category(x) is not None, krows)
    owners = _get_owners_of_rows(krows)
    owners = _filter_user_ids_for_researchers(owners)

    owner_types = {}
    for cat in cats: [ owner_types.update({long(owner) : cat}) for owner in get_userids_with_cat(krows,cat) ]

    # print owner_types

    def compfeat(owner_id):
        result = getattr(wuw,feature_name)(owner_id).values()[0]
        print "owner -- ", owner_id, " ", result
        return result

    feature_functions =  {
        "owner_type" : lambda ownid : owner_types.get(long(ownid),None),
        #"owner_id" : lambda ownid: ownid,
        feature_name : lambda ownid: compfeat(ownid) # lambda n: intent.get_feature_for_note(n["id"],feature_name)
        }

    # fmla = _make_aov_fmla('%s ~ owner_type + owner_id' % feature_name, owners, feature_functions, ['owner_id', 'owner_type'])
    fmla = _make_aov_fmla('%s ~ owner_type' % feature_name, owners, feature_functions, ['owner_type'])

    compute_averages(owners,feature_functions,feature_name,'owner_type')
    aov = r('aov')(fmla)
    tsd = r('TukeyHSD')(aov)
    ios = StringIO.StringIO()
    print >>ios,r.summary(tsd)
    return fmla,aov,tsd,ios.getvalue()

def compute_averages(items,featurefunctions,of_what,by_what):
    sorted = {}
    for item in items:
        key = featurefunctions[by_what](item)
        if key is None: print "item rendered none for ", by_what, "::", item
        if key not in sorted:
            sorted[key] = []
        val = featurefunctions[of_what](item)
        if val is not None:  sorted[key].append(featurefunctions[of_what](item))
    #print sorted.keys()
    for k in sorted.keys():
        print k
        #print sorted[k]
        print "len : ", len(sorted[k]), "mean: ", mean(sorted[k]), "min ", min(sorted[k]), "max ", max(sorted[k]), " var:", ca.var(sorted[k]) if len(sorted[k]) > 1 else "CANT COMPUTE len = 1"

def _make_env_dict(items,featurefunctions):
    env = {}
    [ env.update({name:r.c()}) for name in featurefunctions.keys()]
    for item in items:
        itemenv = {}
        for name,fn in featurefunctions.iteritems():
            rf = fn(item)
            if rf is None: continue
            itemenv[name] = rf
        # ensure we've got all
        if len(itemenv) == len(featurefunctions):
            for name,rf in itemenv.iteritems():
                env[name] = r.c(env[name],rf)
    return env

def _make_aov_fmla(fla, items, featurefunctions, factor_fields):
    fmla = ro.Formula(fla)
    env = {}
    [ env.update({name:r.c()}) for name in featurefunctions.keys()]
    for item in items:
        itemenv = {}
        for name,fn in featurefunctions.iteritems():
            rf = fn(item)
            if rf is None:
                print "skipping ",item, "due to NULL", name
                continue
            itemenv[name] = rf
        # ensure we've got all
        if len(itemenv) == len(featurefunctions):
            for name,rf in itemenv.iteritems():
                # print name, '=', rf, type(rf)
                env[name] = r.c(env[name],rf)


    # debug
                
    # factorify r
    [env.update( {field_name : r('as.factor')(env[field_name])} ) for field_name in factor_fields]
    for k,v in env.iteritems(): fmla.environment[k] = v

    # debug
    print "------------ displaying contents of formula ---------------------"
    for k,v in env.iteritems():
        print k, v, "LENGTH: ", len(v)

    return fmla

def print_aov_bits(krows,feature_name):
    nlk = anova_by_note_feature(krows,feature_name)
    sio = StringIO.StringIO()
    print >>sio,r.summary(nlk[1])
    print sio.getvalue()[:7000]
    sio = StringIO.StringIO()
    print >>sio,nlk[2]
    print sio.getvalue()[:8000]


column_parsers = {
    'emax': parse_emax,
    'kat': parse_emax,
    'wstyke':parse_emax
    }

def get_distribution_of_days_active(user_ids,user_feature=wuw.user_percent_active_days,filename='daysdist'):
    r.png(cap.make_filename(filename))
    rhi = r.hist(c([user_feature(x).values()[0] for x in user_ids]),xlab=r.c(),ylab=r.c(),main=r.c())
    r('dev.off()')
    return rhi

def compute_cats_per_user(arows):
    return [ len([c for c,v in x['consolidated'].iteritems() if v > 2]) for x in arows  if len(x['consolidated']) > 0 ]


# xw = kl.read()
# get_distribution_of_days_active(

# compute Cohen's kappa

def getStats():
    simRat('wstyke','emax','kat')

def getRatings(userA, userB, userC):
    ratings = read()
    users = [[0]*4]*3 ## users[0,1,2][0,1,2,3]
    rTypes = ['packrat','neat freak','sweeper','revisaholic']
    for rating in ratings:
        if userA not in rating or userB not in rating or userC not in rating:
            continue
        tmpUserRat = [[0]*4]*3
        for ui, user in enumerate([userA,userB,userC]):
#            print rating, user
            if type(rating[user]) != type({}):
                continue
            userRatings = [(typ,val) for typ,val in rating[user].items()]
#            print userRatings
            if len(userRatings) == 0:
                continue
            maxType = [x for x,y in userRatings if y == max([i for n,i in userRatings])][0]
#            print maxType
            users[ui][rTypes.index(maxType)] += 1
            pass
    print users[0], users[1], users[2]
    print fKap(users[0],users[1],users[2])

def simRat(userA,userB,userC):
    import random
    r('library(irr)')
    ratings = read()
    userScores = [[], [],[]]
    rTypes = ['packrat','neat freak','sweeper','revisaholic']
    k=0
    userA = userA
    userC = userC
    for rating in ratings:
        if noRat(userA,rating) or noRat(userC,rating):
            k+=1
            continue
        sharedRatings = [(x,y) for x,y in rating[userA].iteritems() if x in rating[userC]]
        for ui, user in enumerate([userA, userC]):
            ## Added 3 lines below: if two rates gave a shared rating to a user, 
            ## use one of those shared ratings
#            if len(sharedRatings) != 0:
#                userScores[ui].append(sharedRatings[0][0])
#                continue
            userRatings = [(typ,val) for typ,val in rating[user].items()]
#            maxType = [x for x,y in userRatings if y == max([i for n,i in userRatings])]
            maxType = [x for x,y in userRatings]
            combined = [(x,y) for x,y in rating["consolidated"].iteritems()]
            combined.sort(key=lambda x: -x[1]) # ascending sort
            combined = [x for x,y in combined] # get rid of the ratings i think.
            maxType.sort(key=lambda x:listfind(combined,x))
            maxType = maxType[0]            
            userScores[ui].append(maxType)
    print 'skipped', k
    print len(userScores[0]), len(userScores[1]), len(userScores[2])
    print userA, "and", userC
    fKap2(userScores[0],userScores[1])

def ratCorr():
    for us in [ratingCorr('wstyke','emax'), ratingCorr('wstyke','kat'), ratingCorr('kat','emax')]:
        aveCorr(us)
        iccCat(us)

rTypes = ['packrat','neat freak','sweeper','revisaholic']

def ratingCorr(userA, userB):
    ## Correlation between Rater's ratings of users for each of 4 types
    users=[userA, userB]
    print "For raters: ", userA, ", ", userB
    ratings = read()
    userScores = [[],[]]
    global rTypes
    for rating in ratings:
        if noRat(userA, rating) or noRat(userB, rating):
            continue
        for ui,userString in enumerate(users):
            userRating = rating[userString]
            orderRating = [0]*4
            for typIndex, typ in enumerate(rTypes):
                if typ in userRating.keys():
                    orderRating[typIndex] = userRating[typ]
                else:
                    orderRating[typIndex] = 0 ## shares '--' rating
            userScores[ui].append(orderRating)
    return userScores

def aveCorr(userScores):
    corr = []
    for i in range(len(userScores[0])):
        corr.append(r.cor(c(userScores[0][i]),c(userScores[1][i]),method='pearson')[0])
    print "Pearson Correlation: ", sum(corr)/len(corr)
    print "Variance: ", variance(corr), '\n\n'

def iccCat(userScores):
    global rTypes
    ## This calculates intraclass correlation coefficient for each category
    summary = ""
    for catIndex in range(0,4):
        print "ICC For type: ", rTypes[catIndex]
        data = c([])
        for ratIndex in range(len(userScores[0])):
            data = r.rbind(data, c([userScores[0][ratIndex][catIndex],userScores[1][ratIndex][catIndex]]))
        result = r.icc(data, type='agreement')
        summary += "Category: %s, ICC: %s, p: %s, Confidince Interval: %s < ICC < %s\n" % (
            rTypes[catIndex],result[6][0], result[11][0], result[13][0],result[14][0])
        print result
    print summary
    return result

def listfind(l,x):
    if x in l: return l.index(x)
    return -1


def noRat(userString, rating):
    noRat =  userString not in rating or type(rating[userString]) != type({})
    if not noRat:
        userRatings = [(typ,val) for typ,val in rating[userString].items()]
        if len(userRatings) == 0:
            noRat = True
    if 'userString' in rating:
        if rating[userString] in ['','ins','0','insufficient']:
            return True
    return noRat


def fKap2(ratingsA, ratingsB):
    data = r.cbind(c(ratingsA), c(ratingsB))
    print r('kappam.fleiss')(data)



def fKap(ratingsA,ratingsB,ratingsC):
    data = r.cbind(r.cbind(c(ratingsA), c(ratingsB)),c(ratingsC))
    print r('kappam.fleiss')(data)
