## Stacked bar-graph showing hourly usage of List.it: X-Axis: hour of day, Y-axis: Quantity of creates/edits/deletes
import os,sys
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
##import jv3.study.f as stuf
import jv3.study.thesis_figures as tfigs
import math
from datetime import datetime as dd  # Stacked Bar Graph Function Helpers
r = ro.r
emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
wstyke = User.objects.filter(email="wstyke@gmail.com")[0]
katfang = User.objects.filter(email="justacopy@gmail.com")
karger = User.objects.filter(email="karger@mit.edu")
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)

def bTime(filename, user, title='title'):
    filename = cap.make_filename(filename)
    COL_SEGMENTS = 2
    ROW_GROUPS = 24
    GROUP_TYPES = 1
    aveSize = lambda a,b: int(float(a)/float(b)) if b != 0 else 0  ## a=quantity of something per how many b elts, if no b, return 0
    msecToDate = lambda msec : dd.fromtimestamp(float(msec)/1000.0)
    dtToDayMsec = lambda dt: int((((dt.weekday()*24+dt.hour)*60+dt.minute)*60+dt.second)*1000 + float(dt.microsecond)/1000.0)
    dtToHourMsec = lambda dt: int(((dt.hour*60+dt.minute)*60+dt.second)*1000 + float(dt.microsecond)/1000.0)
    hrsToIndex = lambda colSeg, hrOfDay : colSeg + (hrOfDay)*COL_SEGMENTS
    ##
    notes = user.note_owner.all()
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    ##points = {'note-add':[0 for i in xrange(0,ROW_GROUPS*COL_SEGMENTS)],'note-save':[0 for i in xrange(0,24)],'note-delete':[0 for i in xrange(0,24)]}
    data = r.matrix(0,nrow=COL_SEGMENTS, ncol=ROW_GROUPS*GROUP_TYPES)
    for log in allLogs:
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:  ## Processing logs for which we still
            continue          ## have the note (deleted or not)
        note = noteArr[0]
        aDate, bDate = msecToDate(log.when), msecToDate(note.created)
        aDay, aHour = aDate.weekday(), aDate.hour
        dIndex = hrsToIndex(0, aHour)
        ##points[log.action][dIndex] += 1
        data[dIndex] += 1
        if (log.action == 'note-add'):      ## Record Add
            pass
        elif (log.action == 'note-save'):   ## Record Save: Split (edit on day of note.created vs not)
            pass
        elif (log.action == 'note-delete'): ## Record Death
            pass
        ##xTime = dtToDayMsec(aDate)
        ##yTime = dtToHourMsec(aDate)##dd(year=1,month=1,day=1, hour=aDate.hour,minute=aDate.minute,microsecond=aDate.microsecond))
        pass
    r.png(file = filename, w=2000,h=1000)
    if title == 'title':
        title = "#Notes:#Logs:Email:ID -- " + str(notes.count()) + ":" + str(allLogs.count()) + ":" + user.email + ":" + str(user.id)
    dayNames = ["Mon","Tues","Wed","Thur","Fri","Sat","Sun","Mon"]
    hourNames = ['midnight', '1am','2am','3am','4am','5am','6am','7am','8am','9am','10am','11am','noon']
    hourNames.extend(['1pm','2pm','3pm','4pm','5pm','6pm','7pm','8pm','9pm','10pm','11pm'])
    r.barplot(data, main=title,ylab='# Action Logs',beside=False, names=hourNames)##, width=c(widths), col=colors)
    ##
    ##r.barplot(points['note-add'], cex=8.0,col = "green", pch='o',xlab="Day Of Week", ylab="Hour of Day",main=title, axes=False, xlim=r.c(0,7*24*3600*1000), ylim=r.c(0,24*3600*1000))
    ##r.points(points['note-save'], cex=4.0,col = "purple", pch=17)
    ##r.points(points['note-delete'], cex=4.0,col = "dark red", pch='x')
    ##r.axis(1, at=c([float(x*24*60*60*1000.0) for x in range(0,8)]), labels=c([x for x in dayNames]), tck=1)
    ##r.axis(2, at=c([float(y*60*60*1000.0) for y in range(0,25)]), labels=c([x for x in hourNames]), tck=1)
    devoff()
