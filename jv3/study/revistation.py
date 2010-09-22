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
from jv3.study.study import variance

r = rpy2.robjects.r
ro = rpy2.robjects
c = lambda vv : apply(r.c,vv)

## decision tree stuff ~~~ 
def multiple_regression(notes, predictor_fn, feature_fns):

    fnames = ['f_%d' % i for i in xrange(len(feature_fns))]
    fla = " y ~ %s " % " + ".join(fnames)
    fmla = ro.Formula(fla)
    env = fmla.environment
    
    yvec = r.c()
    xs = {}
    for n in notes:
        yvec = r.c(yvec,predictor_fn(n).values()[0])
        for f_i in xrange(len(fnames)):
            xs[fnames[f_i]] = r.c(xs.get(fnames[f_i],r.c()),feature_fns[f_i](n).values()[0])

    env['y'] = yvec
    for fname in fnames:
        env[fname] = xs[fname]

    return r('lm')(fmla)

    # if method == 'anova':
    #     env['y'] = fyvec
    # else:
    #     env['y'] = r.factor(fyvec)
    #     print r.levels(env['y'])

    # r('library(rpart)')
    # return r('rpart')(fmla,method=method)

def creations(users):
    print "bar"
    cusave = [wuw.reduceRepeatLogsValues(list(cu.activitylog_set.filter(action__in=['notecapture-focus','note-add']).values())) for cu in users]
    means = []
    varss = []
    userstimes = []
    for u_i in xrange(len(cusave)):
        print u_i
        user = users[u_i]
        print user                
        uals = cusave[u_i]
        uals.sort(key=lambda x: long(x["when"]))
        if len(uals) == 0: continue
        print len(uals)
        thisal = uals[0]
        usertimes = []
        for al in uals[1:]:
            if thisal["action"] == 'notecapture-focus' and al["action"] == 'note-add':
                elapsed = long(al["when"]) - long(thisal["when"])
                usertimes.append(long(al["when"]) - long(thisal["when"]))
            thisal = al
        userstimes.append(usertimes)
        try:
            means.append(mean(usertimes))
            varss.append(variance(usertimes))
        except:
            import sys
            print sys.exc_info()
    return reduce(lambda x,y:x+y, userstimes),userstimes,means,varss
            
