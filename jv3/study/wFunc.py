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
import jv3.study.thesis_figures as tfigs
import jv3.study.wUtil as wUtil
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

def pch_of_delta(first,last):
  if len(first) < len(last): return 2 # R's up triangle pch
  if len(first) == len(last): return 5  # R's diamond  pch
  return 6 # R's down triangle pch

def pch_of_innerEdit(initText, endText): 
  return 15  if wUtil.str_sum_lines(initText) <= 1 else 17 ## Square=1-liner, Tri= 2+ lines
  ##return 3 if wUtil.str_sum_lines(initText) <= 1 else 4   ## + if (1 line note) else X mark

def col_of_edit(initText,type,when=0):
  if type == 'outer':
    if ca.str_n_urls(initText) >= 1: return 'blue'
    elif ca.str_n_emails(initText) >= 1: return 'orange'
    return 'black'
  elif type == 'inner':  ## Color of triangle hard to see!
    ## Fill in for inner edit: purple if 1 line note, red if multi-line
    day = wUtil.msecToDate(when).weekday()
    return ['red','orange','yellow','green','blue','gray', 'brown'][day]
    ##return 'blue' if wUtil.str_sum_lines(initText) <= 1 else 'red'
  else:
    print 'invalid type given to col_of_edit in wFunc.py'

## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)
def mmmPlot(filename, notes,  title='title'):
  firstBirth = 1217622560992.0
  ## Meta-data for title
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-delete'])
  msecToWeek = 1.0/(1000.0*60*60*24*7)
  msecOfWeek = 1000.0*60*60*24*7
  useremail ,noteCount, actionCount = notes[0].owner.email, notes.count(), allLogs.count()
  title = "#Notes:#Logs:Email -- " + str(noteCount) + ":" + str(actionCount) + ":" + useremail
  ## Meta-data for points
  points = {'note-add':r.c(), 'note-delete':r.c()} ## Shortened to just the two, since note-edit added later
  births , deaths = {}, {}
  today = time.time()*1000.0
  r.png(file=cap.make_filename(filename), w=6400,h=3200) ## 3200x1600, 9600x4800, 12.8x6.4
  cc=[x['created'] for x in notes.values('created')]
  dd=allLogs.values('when')
  minBirth, maxBirth = float(min(cc)), float(max(cc))                        ## Week 2011 was first week of listit
  minAction, maxAction = float(min(dd)['when']), float(max(dd)['when'])
  for log in allLogs:
     noteArr = notes.filter(jid=log.noteid)
     if len(noteArr) < 1:
        continue
     note = noteArr[0]
     births[note.jid] = note.created
     if not note.deleted and note.jid not in deaths:
        deaths[note.jid] = today
        pass
     if (log.action == 'note-delete'):
        deaths[note.jid] = float(log.when)
     points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
     pass
  xl,yl="Created Date", "Action Date"
  r.plot(points['note-add'], cex=2.0,col = "green", pch='o',xlab=xl,ylab=yl, main=title, xlim=r.c(firstBirth, today), ylim=r.c(firstBirth, today), axes=False)
  xWeeks = [int(x) for x in range(int(firstBirth*msecToWeek), int(time.time()*1000*msecToWeek), 1)]
  yWeeks = [int(y) for y in range(int(firstBirth*msecToWeek), int(time.time()*1000*msecToWeek), 1)]
  r.axis(1, at=c([float(x*7*24*60*60*1000.0) for x in xWeeks]), labels=c([int(x)-2012 for x in xWeeks]), tck=1)
  r.axis(2, at=c([float(y*7*24*60*60*1000.0) for y in yWeeks]), labels=c([int(x)-2012 for x in yWeeks]), tck=1)  
  #New code for edits inserted here
  edits_ = ca.note_edits_for_user(notes[0].owner)
  points['note-edit'] = r.c()
  edit_dir, edit_delta, edit_col = r.c(), r.c(), r.c()
  for n in notes:  ## wCom: not all notes eval'd here may have note-add events !!
    if n.jid in edits_:
      ##print "in ",n.jid,n.owner.email,len(edits_[n.jid])
      for edit_action in edits_[n.jid]:
        ## Add big icon
        points['note-edit'] = r.rbind(points['note-edit'],c([float(n.created), float(edit_action['when'])]))
        edit_dir = r.c(edit_dir, pch_of_delta(edit_action['initial'],edit_action['final']))
        edit_delta = r.c(edit_delta, 14)#abs(10 + 10*(len(edit_action['initial']) - len(edit_action['final']))/1000.0))
        edit_col = r.c(edit_col, col_of_edit(edit_action['initial'],'outer'))
        ## Add small icon
        points['note-edit'] = r.rbind(points['note-edit'],c([float(n.created), float(edit_action['when'])]))
        edit_dir = r.c(edit_dir, pch_of_innerEdit(edit_action['initial'],edit_action['final']))
        edit_delta = r.c(edit_delta, 7)#abs(10 + 10*(len(edit_action['initial']) - len(edit_action['final']))/1000.0))
        edit_col = r.c(edit_col, col_of_edit(edit_action['initial'], 'inner', edit_action['when']))
  ##End new code
  r.points(points['note-edit'], col=edit_col, pch=edit_dir,  cex=edit_delta)
  r.points(points['note-delete'], cex=5.0,col = "dark red", pch='x')
  for x in births.keys():
     if x in deaths:
       color = 'green' if (today-deaths[x] < 0.001) else 'black'
       r.lines(c([float(births[x])]*2),c([float(births[x]),float(deaths[x])]), col=color)
       pass
  devoff()

def test_mmmPlot():
  mmmPlot('wt0',emn)
  mmmPlot('wt1',dkn)


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



## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)

msecToWeek = lambda x : x * (1.0/(1000.0*60*60*24*7))

def one_or_no_url_redblue(note):
  from thesis_figures import n2vals
  note = n2vals(note)
  urls = ca.note_urls(note)
  if type(urls) == dict:
    return 'blue' if urls['note_urls'] > 0 else 'red'
  return 'blue' if urls[1] > 0 else 'red'
    
def lifelineFlatCollapsedCompareColor(filename, notes, title='title', color_function=one_or_no_url_redblue, YMAG=0.5):
  ## Meta-data for title
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-delete'])
  firstBirth = float(min([x[0] for x in notes.values_list('created')]))
  title = "%s -- %s %s  " % (title,str(notes.count()),notes[0].owner.email)
  ## Meta-data for points
  points = {'note-add':r.c(), 'note-delete':r.c()} ## Shortened to just the two, since note-edit added later
  births, deaths = {}, {}, 
  today = time.time()*1000.0
  print "saving to %s " % cap.make_filename(filename)
  r.png(file=cap.make_filename(filename), w=6400,h=3200) ## 3200x1600, 9600x4800, 12.8x6.4
  colors=dict([(n.jid,color_function(n)) for n in notes])  

  # order notes by creation
  jids = [id[0] for id in notes.order_by("created").values_list('jid')]
  jid2idx = dict([(jids[i],i) for i in xrange(len(jids))])
  
  for log in allLogs:
     noteArr = notes.filter(jid=log.noteid)
     if len(noteArr) < 1:
        continue
     note = noteArr[0]
     births[note.jid] = jid2idx[note.jid]
     if not note.deleted and note.jid not in deaths:
        deaths[note.jid] = today
        pass
     if (log.action == 'note-delete'):
        deaths[note.jid] = float(log.when-note.created)
     points[log.action] = r.rbind(points[log.action],c([jid2idx[note.jid],float(log.when-note.created)]))
     pass

  # compute the edits, compile the colors
  edits_ = ca.note_edits_for_user(notes[0].owner)
  points['note-edit'] = r.c()
  edit_dir, edit_delta, colors_r = r.c(), r.c(), r.c(),
  ymax = 0
  for n in notes:  ## wCom: not all notes eval'd here may have note-add events !!
    colors_r = r.c(colors_r,colors[n.jid])
    if n.jid in edits_:
      for edit_action in edits_[n.jid]:
        ## Add big icon
        ymax = max(ymax,float(edit_action['when']-n.created))
        points['note-edit'] = r.rbind(points['note-edit'],c([jid2idx[n.jid], float(edit_action['when']-n.created)]))
        edit_dir = r.c(edit_dir, pch_of_delta(edit_action['initial'],edit_action['final']))
        edit_delta = 3 # r.c(edit_delta, abs(3 + 1*(len(edit_action['initial']) - len(edit_action['final']))/1000.0))
        # ## Add small icon
        #         points['note-edit'] = r.rbind(points['note-edit'],c([jid2idx[n.jid], float(edit_action['when'])]))
        #         edit_dir = r.c(edit_dir, pch_of_innerEdit(edit_action['initial'],edit_action['final']))
        #         edit_delta = r.c(edit_delta, 7)#abs(10 + 10*(len(edit_action['initial']) - len(edit_action['final']))/1000.0))
        #         edit_col = r.c(edit_col, col_of_edit(edit_action['initial'], 'inner', edit_action['when']))
        
  print points['note-edit']
  xl,yl="Created Date", "Action Date"
  r.plot(points['note-add'], cex=2.0,col=colors_r, pch='o',xlab=xl,ylab=yl, main=title, xlim=r.c(0, notes.count()),ylim=r.c(0, YMAG*ymax), axes=False)
  r.points(points['note-edit'], col=colors_r, pch=edit_dir,  cex=edit_delta)
  r.points(points['note-delete'], cex=2.0,col = colors_r, pch='x')
  yWeeks = [int(y) for y in range(int(msecToWeek(firstBirth)), int(msecToWeek(time.time()*1000)), 1)]
  r.axis(2, at=c([float(y*7*24*60*60*1000.0) for y in yWeeks]), labels=c([int(x)-2012 for x in yWeeks]), tck=1)

  for x in births.keys():
     if x in deaths:
       stillalive = (today-deaths[x] < 0.001)
       color = colors[x] # ('green' if stillalive else 'black')
       r.lines(c([float(births[x])]*2),c([float(births[x]),float(deaths[x]-births[x])]), col=color)
       pass
  devoff()



