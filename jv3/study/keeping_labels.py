
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

r = rpy2.robjects.r
ro = rpy2.robjects
c = lambda vv : apply(r.c,vv)

columns = ['userid','wolfe','emax','notes']
cats = ['packrat','neat freak','sweeper','revisaholic']

def get_user(rows,userid): return [row for row in rows if row['userid'] == userid][0]

def read(filename=None):
   f0 = "%s/%s" % (settings.KEEPING_STYLE_DIR, "index.csv" if filename is None else filename )
   datas = []
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      [datas.append(dict(zip(columns,r))) for r in rdr]
      F.close()
   return datas[1:]

def _write(datas):
    import csv,settings,time
    f0 = "%s/%s" % (settings.KEEPING_STYLE_DIR,"index.csv")
    f1 = "%s/%s" % (settings.KEEPING_STYLE_DIR,"index-%d-%d-%d%d.csv" % (time.localtime().tm_year,
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
        
def parse_emax(rows,user_id):
    print user_id
    r = get_user(rows,user_id).get('emax',None)
    if r is None or r == '' or  r.find('ins') >= 0 : return None
    rs = [x for x in r.replace(';',' ').replace(' + ',' ').strip().split(' ') if len(x.strip()) > 0]
    s = {}
    print user_id,"_",rs
    for r in rs:
        print "arr is ",r
        if r.find('NICE') == 0 or r.find('(NI') == 0:
          s['NICE'] = True
          continue
        try:
            category = cats[int(r[0])]
            strength = ({'--':1,'-':2,'':3,'+':4,'++':5,'+++':5}).get(r[1:],0)
            s[category]=strength
        except:
            print sys.exc_info()
    return s


        
