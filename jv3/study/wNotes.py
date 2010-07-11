python manage.py shell
## startup
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
from cap import make_filename
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
import random
r = ro.r
em = User.objects.filter(email="emax@csail.mit.edu")[0]
emn = Note.note_owner.all()
dk = User.objects.filter(email='karger@mit.edu')[0]
dkn = dk.note_owner.all()
ws = User.objects.filter(email='wstyke@gmail.com')[0]
wsn = ws.note_owner.all()
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)

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


## Specific Plots using above general plots

## Plots note-add and note-edits on a x=created, y=edited graph
## - Vertical row of dots   = one note being edited a bunch
## - Horizontal row of dots = one time when a bunch of notes edited

def plot_note_edits(filename, notes):
    username = notes[0].owner.email
    aPlot("note_edits/" +filename, notes, 'created', 'when', ['note-save', 'note-add'], 'created', 'when', 'Created vs When-Log-Entry-Recorded for '+username)


## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)
def mPlot(filename, notes,  title='title'):
  points = {'note-add':r.c(),'note-save':r.c(),'note-delete':r.c()}
  r.png(file = make_filename(filename), w=3600,h=1800)
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-save','note-delete'])
  for log in allLogs:
     noteArr = notes.filter(jid=log.noteid)
     if len(noteArr) < 1:
         continue
     note = noteArr[0]
     points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
     pass
  r.plot(points['note-add'], cex=6.0,col = "orange", pch='.', xlab='created', ylab='action', main=title)
  r.points(points['note-save'], cex=1.0,col = "purple", pch='o')
  r.points(points['note-delete'], cex=1.0,col = "dark red", pch='x')
  devoff()

## Plot up to 100 users who satisfy conditions

def makeACUPlots():
    i=0
    path = 'acu/note_life2/'
    print "Start time: ", time.gmtime()
    startTime = time.time()
    for user in u:
        uNotes = Note.objects.filter(owner=user)
        uLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
        if (((uNotes.count() >= 120) or (uLogs.count() >= 120)) and ((uNotes.count() >= 50) and (uLogs.count() >= 50))):
            mmmPlot(path+str(i)+"-"+str(user.id), uNotes)
            i += 1
            pass
        pass
    print "Users processed: ", str(i) , " out of: ", str(len(u))
    print "Finish time: ", time.gmtime()
    finishTime = time.time()

