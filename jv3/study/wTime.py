## For a scatter plot of:   x-axis:day of week,  y-axis:time of day
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
import jv3.study.f as stuf
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

def sTime(filename, user, title='title'):
    filename = cap.make_filename(filename)
    aveSize = lambda a,b: int(float(a)/float(b)) if b != 0 else 0  ## a=quantity of something per how many b elts, if no b, return 0
    msecToDate = lambda msec : dd.fromtimestamp(float(msec)/1000.0)
    dtToDayMsec = lambda dt: int((((dt.weekday()*24+dt.hour)*60+dt.minute)*60+dt.second)*1000 + float(dt.microsecond)/1000.0)
    dtToHourMsec = lambda dt: int(((dt.hour*60+dt.minute)*60+dt.second)*1000 + float(dt.microsecond)/1000.0)
    notes = user.note_owner.all()
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    points = {'note-add':r.c(),'note-save':r.c(),'note-delete':r.c()}
    for log in allLogs:
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:  ## Processing logs for which we still
            continue          ## have the note (deleted or not)
        note = noteArr[0]
        aDate, bDate = msecToDate(log.when), msecToDate(note.created)
        xTime = dtToDayMsec(aDate)
        yTime = dtToHourMsec(aDate)##dd(year=1,month=1,day=1, hour=aDate.hour,minute=aDate.minute,microsecond=aDate.microsecond))
        points[log.action] = r.rbind(points[log.action],c([xTime, yTime]))
        pass
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=2000,h=1000)
    if title == 'title':
        title = "#Notes:#Logs:Email:ID -- " + str(notes.count()) + ":" + str(allLogs.count()) + ":" + user.email + ":" + str(user.id)
    dayNames = ["Mon","Tues","Wed","Thur","Fri","Sat","Sun","Mon"]
    hourNames = ['midnight', '1am','2am','3am','4am','5am','6am','7am','8am','9am','10am','11am','noon']
    hourNames.extend(['1pm','2pm','3pm','4pm','5pm','6pm','7pm','8pm','9pm','10pm','11pm','midnight'])
    r.plot(points['note-add'], cex=8.0,col = "green", pch='o',xlab="Day Of Week", ylab="Hour of Day",main=title, axes=False, xlim=r.c(0,7*24*3600*1000), ylim=r.c(0,24*3600*1000))
    r.points(points['note-save'], cex=4.0,col = "purple", pch=17)
    r.points(points['note-delete'], cex=4.0,col = "dark red", pch='x')
    r.axis(1, at=c([float(x*24*60*60*1000.0) for x in range(0,8)]), labels=c([x for x in dayNames]), tck=1)
    r.axis(2, at=c([float(y*60*60*1000.0) for y in range(0,25)]), labels=c([x for x in hourNames]), tck=1)
    devoff()

sTime('wt001', gv)
sTime('wt002', dk)
sTime('wt003', brenn)

## Reminders:

## r.plot(points['note-add'], cex=1.0,col = "green", pch='o',xlab=xl,ylab=yl, main=title, xlim=r.c(firstBirthEver, time.time()*1000), ylim=r.c(firstBirthEver, time.time()*1000.0), axes=False)
## xWeeks = [float(x) for x in range(firstBirthEver*msecToWeek, time.time()*1000*msecToWeek, 1)]
## yWeeks = [float(y) for y in range(firstBirthEver*msecToWeek, time.time()*1000*msecToWeek, 1)]
## r.axis(1, at=c([float(x*7*24*60*60*1000.0) for x in xWeeks]), labels=c([int(x)-2012 for x in xWeeks]), tck=1)
## r.axis(2, at=c([float(y*7*24*60*60*1000.0) for y in yWeeks]), labels=c([int(x)-2012 for x in yWeeks]), tck=1)
## r.points(points['note-save'], cex=4.0,col = "purple", pch=17)
## r.points(points['note-delete'], cex=4.0,col = "dark red", pch='x')

##[[yData.append(elt[1]) for elt in points[type]] for type in points]

##dayNames = ["Mon","Tues","Wed","Thur","Fri","Sat","Sun"]
##colors = r.c("red", 'orange', 'yellow', 'green', 'blue', 'grey', 'brown')
##aveWidth = int(float(sum([elt[1] for elt in createdSize]))/float(sum([elt[0] for elt in createdSize])))
##widths = []
##[widths.extend([aveSize(elt[1],elt[0]), aveWidth, aveWidth, aveWidth, aveWidth]) for elt in createdSize]
##axisNames = []
##[axisNames.extend([str(widths[i*5]),"","",str(dayNames[i]),""]) for i in range(ROW_GROUPS)]
 
