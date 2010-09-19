##python manage.py shell
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


import jv3.study.note_labels as nl
import jv3.study.intention as intent
import jv3.study.wFunc as wf
import jv3.study.wUserWalk as uw

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

cap.set_basedir('/home/emax/public_html/graphs')

## consenting users and notes
u = [ us for us in User.objects.all() if is_consenting_study2(us)]
n = Note.objects.filter( owner__in=[ us for us in User.objects.all() if is_consenting_study2(us)] )

## Returns array of property values for entityArray
def arr_prop(objArray, prop):
    return [float(x) for x in objArray.values_list(prop, flat=True)]

def get_rand_user():
    user = u[random.randint(0,len(u))]
    notes = Note.objects.filter(owner=ru)
    return (user, notes)

def plot_xyz(filename,x,y,z, xl="x",yl="y",title="title"):
    r.png(file = make_filename(filename), w=3200,h=1600)
    r.plot(x,y,cex=z,xlab=xl,ylab=yl,main=title)
    devoff()

def ezPlot(filename, x,y,z, xl="x",yl="y",title="title"):
    xd, yd, zd = c(x), c(y), c(z)
    plot_xyz(filename, xd, yd, zd, xl, yl, title)   

## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)
def aPlot(filename, notes,  xProp, logProp, logTypes, xl='x', yl='y', title='title'):
    x, y, z = [], [], []
    allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=logTypes)
    for log in allLogs:
   	noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) != 1:
    	   continue
  	## We have a single note found
	note = noteArr[0]
	x.append(note.created)
	y.append(log.when)
    ## Now we have a list of notes and logs
    x = [float(v) for v in x]
    y = [float(v) for v in y]    
    ezPlot(filename, x,y,[1]*len(x),xl, yl, title)

## X-Y Scatter Plots with bubble size fixed
def bPlot(filename, x, xProp, y, yProp, size=1, xl='x', yl='y', title='title'):
    xd = c(arr_prop(x, xProp))
    yd = c(arr_prop(y, yProp))
    zd = c([size]*len(x))
    plot_xyz(filename, xd, yd, zd, xl, yl, title)

## X-Y Scatter plots with specified bubble sizes
def cPlot(filename, x, xProp, y, yProp, z, zProp, xl='x', yl='y', title='title'):
    xd = c(arr_prop(x, xProp))
    yd = c(arr_prop(y, yProp))
    zd = c(arr_prop(z, zProp))
    plot_xyz(filename, xd, yd, zd, xl, yl, title)
