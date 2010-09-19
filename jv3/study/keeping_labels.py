
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
import jv3.study.intention as intent
import jv3.study.wUserWalk as wuw


r = rpy2.robjects.r
ro = rpy2.robjects
c = lambda vv : apply(r.c,vv)

columns = ['userid','wolfe','emax','notes']
cats = ['packrat','neat freak','sweeper'] #,'revisaholic']

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
        for c,f in column_parsers.iteritems():
            ret = f(row)
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



def parse_emax(row):
    r = row.get('emax',None)
    if r is None or r == '' or  r.find('ins') >= 0 : return None
    rs = [x for x in r.replace(';',' ').replace(' + ',' ').strip().split(' ') if len(x.strip()) > 0]
    s = {}
    print "reading emax on ",row["userid"],row["emax"]
    for r in rs:
        print "arr is ",r
        if r.find('NICE') == 0 or r.find('(NI') == 0:
          s['NICE'] = True
          continue
        try:
            category = cats[int(r[0])-1]
            strength = ({'--':1,'-':2,'':3,'+':4,'++':5,'+++':5}).get(r[1:],0)
            s[category]=strength
        except:
            print sys.exc_info()
    return s

default_note_features = [ca.note_words, ca.note_lines]
default_user_features = [wuw.user_percent_active_days,
                         wuw.user_mean_alive_percent,
                         wuw.user_var_alive_percent,
                         wuw.user_mean_alive,
                         wuw.user_var_alive,                         
                         wuw.user_mean_day_add,
                         wuw.user_var_day_add,
                         wuw.user_mean_day_del,
                         wuw.user_var_day_del
                         ]
default_note_feature_names = ['words','lines']
default_user_feature_names = ['active days','mean alive %','var alive %','mean alive N','var alive N','mean new/day','var new/day','mean del/day','var del/day']

def get_features_of_styles(arows,note_feature_list=None,user_feature_list=None,note_feature_names=None,user_feature_names=None):
    # makes a nice table of statistics ~~
    if note_feature_list is None: note_feature_list = default_note_features
    if user_feature_list is None: user_feature_list = default_user_features
    if note_feature_names is None: note_feature_names = default_note_feature_names
    if user_feature_names is None: user_feature_names = default_user_feature_names    
    owners = set([x['userid'] for x in arows])
    owners = filter(lambda oid: intent.owner_orm(oid) not in cal.RESEARCHERS,owners)
    notes_of_owners = reduce(lambda x,y:x+y,[[n for n in intent.owner_orm(o).note_owner.all().values()] for o in owners])

    print "----------------------------------------------------------------------ALL -----------------------------------"
    group_note_features = intent._gfanalyze(notes_of_owners,note_feature_list,note_feature_names)
    group_user_features = intent._gfanalyze(owners,user_feature_list,user_feature_names)

    # now partition by cats?
    cat_note_test = {}
    cat_user_test = {}
    for cat in cats:
        users_with_cat = [x["userid"] for x in arows if arows is not None and x['consolidated'].get(cat, 0) >= 3]
        print "[",cat,"]:",len(users_with_cat)
        print "--------------:",cat,":-----------------------------"
        cat_notes =  reduce(lambda x,y: x+y,[[x for x in User.objects.filter(id=o)[0].note_owner.values()] for o in users_with_cat ])
        cat_note_features = intent._gfanalyze(cat_notes, note_feature_list)
        cat_user_features = intent._gfanalyze(users_with_cat, user_feature_list)        
        cat_note_test[cat] = intent._gfcompare(cat_note_features,group_note_features,note_feature_names)
        cat_user_test[cat] = intent._gfcompare(cat_user_features,group_user_features,user_feature_names)
        
    return cat_note_test,cat_user_test

column_parsers = {'emax': parse_emax, notes: lambda x: None         }
