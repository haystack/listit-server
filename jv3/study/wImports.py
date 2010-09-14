from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
from jv3.study.ca_plot import make_filename
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
import random

import jv3.study.wTimeOffset as wto
import jv3.study.wFunc as wf


r = ro.r
em = User.objects.filter(email="emax@csail.mit.edu")[0]
emn = em.note_owner.all()
dk = User.objects.filter(email='karger@mit.edu')[0]
dkn = dk.note_owner.all()
ws = User.objects.filter(email='wstyke@gmail.com')[0]
wsn = ws.note_owner.all()
kf = User.objects.filter(email='justacopy@gmail.com')[0]
kfn = kf.note_owner.all()
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)


## consenting users and notes
u = [ us for us in User.objects.all() if is_consenting_study2(us)]
n = Note.objects.filter( owner__in=[ us for us in User.objects.all() if is_consenting_study2(us)] )

