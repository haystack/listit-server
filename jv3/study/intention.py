
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

notepool = [2983,92830,9283,19283,8923,1982,3892,19293,74,5939,9583,2787,374,849,982,849,2313]
N = 14

cats = ["memory trigger","reference","external cognition", "journal/activity log", "posterity"]
columns = ['coder','owner_id','jid','contents','primary']+cats

def read(filename=None):
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

def get_notes(request):
    import random
    ss = json.dumps([x for x in Note.objects.filter(id__in=random.sample(notepool,min(len(notepool),N))).values('owner_id','jid','contents')])
    return HttpResponse(ss,"text/json")    

def post_intention(request):
    rpd = request.raw_post_data
    print "rpd ", rpd, type(rpd)
    newsintentions = JSONDecoder().decode(rpd)['results'] # json.loads(request.raw_post_data)
    d = read()
    for ni in newsintentions:
        print ni
        r = []
        for c in columns:
            r.append(ni.get(c,None))
        d.append(r)
    _write(d)
    return HttpResponse("{}","text/json")    
