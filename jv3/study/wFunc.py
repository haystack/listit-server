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
from jv3.study.thesis_figures import n2vals,text2vals
r = ro.r
c = lambda vv : apply(r.c,vv)
devoff = lambda : r('dev.off()')
emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
wstyke = User.objects.filter(email="wstyke@gmail.com")[0]
katfang = User.objects.filter(email="justacopy@gmail.com")
dk = User.objects.filter(email="karger@mit.edu")
dkn = Note.objects.filter(owner=dk)

firstBirth = 1229718560992.0 ## 21 weeks in

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
  global firstBirth
  ##firstBirth = 1217622560992.0
  ## Meta-data for title
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-delete'])
  saveLogCount = ActivityLog.objects.filter(owner=notes[0].owner, action='note-save').count()
  msecToWeek = 1.0/(1000.0*60*60*24*7)
  msecOfWeek = 1000.0*60*60*24*7
  useremail ,noteCount, actionCount = notes[0].owner.email, notes.count(), allLogs.count()
  title = "#Notes:#SaveLogs:#Dels:Email -- " + str(noteCount) + ":" + str(saveLogCount) + ":" + str(sum([n.deleted for n in notes])) + ":" + useremail
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
        ##if edit_categorized(
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
       r.lines(c([float(births[x])]*2),c([float(births[x]),float(deaths[x])]), col=color, lwd=3)
       pass
  devoff()

def test_mmmPlot():
  mmmPlot('wt0',emn)
  mmmPlot('wt1',dkn)


def makeACUPlots(u):
    i=0
    path = cap.BASEDIR + '/note_life3/'
    print "Start time: ", time.gmtime()
    startTime = time.time()
    for user in u:
        uNotes = Note.objects.filter(owner=user)
        uLogs = ActivityLog.objects.filter(owner=user, action__in=['note-save','note-delete'])
        if (((uNotes.count() >= 120) or (uLogs.count() >= 120)) and ((uNotes.count() >= 50) and (uLogs.count() >= 50))):
            mmmPlot(path+str(i)+"-"+str(user.id), uNotes)
            i += 1
            pass
        pass
    print "Users processed: ", str(i) , " out of: ", str(len(u))
    print "Finish time: ", time.gmtime()
    finishTime = time.time()


def makeNoteLifePlots(u, decider, middleDir):
    i=0
    path = cap.BASEDIR + middleDir
    print "Start time: ", time.gmtime()
    startTime = time.time()
    for user in u:
        if (isInterestingUser(user) and decider(user) and not isTroublesomeUser(user)):
            uNotes = Note.objects.filter(owner=user)
            print "Processing user %d with %d notes" % (user.id, uNotes.count())
            mmmPlot(path+str(user.id), uNotes)
            i += 1
            pass
        pass
    print "Users processed: ", str(i) , " out of: ", str(len(u))
    print "Finish time: ", time.gmtime()
    finishTime = time.time()

## Try to pick out pack-rats for plotting! !
def plotPackRat(u):
  makeNoteLifePlots(u, isPackRat, '/user_types/pack_rat/02/')

def plotNeatFreak(u):
  makeNoteLifePlots(u, isNeatFreak, '/user_types/neat_freak/01/')

def plotAll(u):
  makeNoteLifePlots(u, retTrue, '/note_life4/')

def retTrue(u):
  return True

## Gatherers
def getPackrats(users):
  packrats, nonPR = [], []
  for user in users:
    if (not isInterestingUser(user) or isTroublesomeUser(user)):
        continue
    if (isPackRat(user)):
        packrats.append(user)
    else:
        nonPR.append(user)
  return (packrats, nonPR)

def getNeatFreaks(users):
  neatfreaks, nonNF = [], []
  for user in users:
    if (not isInterestingUser(user) or isTroublesomeUser(user)):
        continue
    if (isNeatFreak(user)):
        neatfreaks.append(user)
    else:
        nonNF.append(user)
  return (neatfreaks, nonNF)


def getNumNotes(usersA):
  countA = 0
  for user in usersA:
    countA += Note.objects.filter(owner=user).count()
  ##for user in usersB:
    ##countB += Note.objects.filter(owner=user).count()
  return countA

def getNumAliveNotes(usersA):  #, usersB):
  countA =0 ##, countB = 0,0
  for user in usersA:
    countA += sum([1 - n.deleted for n in Note.objects.filter(owner=user)])
  ##for user in usersB:
    ##countB += sum([1 - n.deleted for n in Note.objects.filter(owner=user)])
  return countA


## Summarizer:

def userStats(users):
  userCount = len(users)
  noteCount = []
  noteAlive = []
  noteDead  = []
  aliveCharLength = []
  deadCharLength = []
  for user in users:
    notes = Note.objects.filter(owner=user)
    noteCount.append(notes.count())
    noteAlive.append(int(sum([1-n.deleted for n in notes])))
    noteDead.append(int(sum([n.deleted for n in notes])))
    for note in notes:
      if note.deleted == 1:
        deadCharLength.append(int(len(note.contents)))
      else:
        aliveCharLength.append(int(len(note.contents)))
      pass
    pass
  numNoteVar = variance(noteCount)
  noteCount = sum(noteCount)
  noteAliveVar = variance(noteAlive)
  noteAliveCount = sum(noteAlive)
  noteDeadVar = variance(noteDead)
  noteDeadCount = sum(noteDead)  
  aveAliveChar, aveDeadChar = mean(aliveCharLength), mean(deadCharLength)
  varAliveChar, varDeadChar = variance(aliveCharLength), variance(deadCharLength)
  print userCount, noteCount, noteCount/userCount, numNoteVar
  print noteAliveCount, noteAliveCount/userCount, noteAliveVar
  print noteDeadCount, noteDeadCount/userCount, noteDeadVar
  print aveAliveChar, aveDeadChar, varAliveChar, varDeadChar
  return aliveCharLength, deadCharLength, noteAlive, noteDead

## Classifiers
def isTroublesomeUser(user):
  return user.id in [13867, 11756, 3, 7, 13, 17, 11310, 13273, 14137, 14291, 11658]

def isInterestingUser(user):
  numNotes = Note.objects.filter(owner=user).count()
  numLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-delete']).count()
  return numNotes >= 50 and numLogs >= 10

def isPackRat(u):
  uNotes = Note.objects.filter(owner=u)
  if uNotes.count() == 0:
    amt=-1
  else:
    amt = float(sum([n.deleted for n in uNotes])) / float(uNotes.count())
  return 0 <= amt and amt <= 0.2

def isNeatFreak(u):
  uNotes = Note.objects.filter(owner=u)
  if uNotes.count() == 0:
    amt = -1
  else:
    amt = float(sum([n.deleted for n in uNotes])) / float(uNotes.count())
  return 1.0 >= amt and amt >= 0.8

## Helping me find classify bounds
def getPackRatAmt(u):
  allLogs = ActivityLog.objects.filter(owner=u)
  uNotes = Note.objects.filter(owner=u)
  uAdds = allLogs.filter(action='note-add')
  uSave = allLogs.filter(action='note-save')
  uDels = allLogs.filter(action='note-delete')
  if uNotes.count() == 0:
    amt=-1
  else:
    amt = float(sum([n.deleted for n in uNotes])) / float(uNotes.count())
  return (amt, u.id, uNotes.count(),uAdds.count(),uSave.count(),uDels.count())

def testPR(users):
  for user in users:
    if getPackRatAmt(user)[0] > 1:
      print user.id, getPackRatAmt(user)

## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)

msecToWeek = lambda x : x * (1.0/(1000.0*60*60*24*7))

black = lambda note: 'black'

def one_or_no_url_redblk(note):
  note = n2vals(note)
  urls = ca.note_urls(note)
  if type(urls) == dict:
    return 'red' if urls['note_urls'] > 0 else 'black'
  return 'red' if urls[1] > 0 else 'black'

def one_or_no_email_redblk(note):
  note = n2vals(note)
  emails = ca.note_emails(note)
  if type(emails) == dict:
    return 'red' if emails['email_addrs'] > 0 else 'black'
  return 'red' if emails[1] > 0 else 'black'

def one_or_more_lines_multicolor(note):
  note = n2vals(note)
  lines = ca.note_lines(note)
  if type(lines) == dict:
    val = lines['note_lines']
  else:
    val = lines[1]
  if val == 1: return 'black'
  if val in [2,3,4,5]: return 'blue'
  if val in range(6,12): return 'orange'
  return 'red'

def one_or_more_numbers_redblk(note):
  note = n2vals(note)
  lines = ca.numbers(note)
  if type(lines) == dict:
    val = lines['note_lines']
  else:
    val = lines[1]  
  return 'red' if val > 0 else 'black'

def one_or_more_verbs_redblk(note):
  note = n2vals(note)
  lines = ca.note_verbs(note)
  if type(lines) == dict:
    val = lines['note_verbs']
  else:
    val = lines[1]    
  return 'red' if val > 0 else 'black'
  
def one_or_more_daysofweek_redblk(note):
  note = n2vals(note)
  lines = ca.daysofweek(note)
  if type(lines) == dict:
    val = lines['daysofweek']
  else:
    val = lines[1]      
  return 'red' if lines > 0 else 'black'

def one_or_more_timeref_redblk(note):
  note = n2vals(note)
  timeCount = ca.daysofweek(note)['daysofweek'] if type(ca.daysofweek(note)) == dict else ca.daysofweek(note)[1]
  timeCount += ca.months(note)['months'] if type(ca.months(note)) == dict else ca.months(note)[1]
  return 'red' if timeCount > 0 else 'black'

def one_or_more_todoref_redblk(note):
  note = n2vals(note)
  todoCount = ca.note_todos(note)['note_todos'] if type(ca.note_todos(note) ) == dict else ca.note_todos(note)[1]  
  return 'red' if todoCount > 0 else 'black'

def two_or_more_sentences_redblk(note):
  note = n2vals(note)
  senCount = ca.note_sentences(note)['note_sentences'] if type(ca.note_sentences(note)) == dict else ca.note_sentences(note)[1]
  return 'red' if senCount > 1 else 'black'

## performs a flattened collapsed lifeline with     
def lifelineFlatCollapsedCompareColor(filename, notes, title='Note Lifelines', color_function=black, YMAG=1.0):
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-save','note-delete'])
  firstBirth = float(min([x[0] for x in notes.values_list('created')]))
  title = "%s -- %s %s %s  " % (title,str(notes.count()),notes[0].owner.email,notes[0].owner.id)
  ## Meta-data for points

  births, deaths = {}, {}, 
  today = time.time()*1000.0
  print "saving to %s " % cap.make_filename(filename)
  r.png(file=cap.make_filename(filename), w=3200,h=1600) ## 3200x1600, 9600x4800, 12.8x6.4
  texts=dict([(n.jid,n.contents) for n in notes])
  births = dict([(n.jid,float(n.created)) for n in notes])
  jid2note = dict([(n.jid,n) for n in notes])
  
  whenmax = 0
  whenmin = time.time()*1000.0
  for log in allLogs:
    if log.action == 'note-add':  births[log.noteid] = float(log.when)
    if log.action in ['note-add','note-save'] and log.noteText is not None and log.noteid not in texts : texts[log.noteid] = log.noteText
    if log.action == 'note-delete': deaths[log.noteid] = float(log.when)
    whenmax = max(whenmax,float(log.when))
    whenmin = min(whenmin,float(log.when))

  print "whenmax ", whenmin, '-', int(whenmax), (whenmax-whenmin)/(24*60*60*1000.0)

  # if not deleted we fill these in
  for n in notes.filter(deleted=False) : deaths[n.jid] = whenmax

  # order notes by creation
  births_ordered = [ (jid, btime) for jid, btime in births.iteritems() ]
  births_ordered.sort(key=lambda x:x[1])
  jid2idx = dict([(births_ordered[i][0],i) for i in xrange(len(births_ordered))])

  # compute the edits, compile the colors
  print "computing edits"
  edits_ = ca.note_edits_for_user(notes[0].owner)
  
  print "Color function"
  colors=dict([(jid,color_function(text2vals(text))) for jid,text in texts.iteritems()])
  print "--"
  births_r,colors_r,deletes_r= r.c(),r.c(),r.c()
  edits_r = r.c()
  edit_dirs_r = r.c()
  edit_delta = 3 

  print "BIRTHS= %d " % len(births)
  print "DEATHS %d " % len(deaths)
  
  for njid in births: 
    births_r = r.rbind(births_r, c([ jid2idx[njid], 0 ]))  # 
    colors_r = r.c(colors_r,colors[njid] if njid in colors else'grey') 
    deletes_r = r.rbind(deletes_r, c([ jid2idx[njid], deaths[njid]-births[njid] if njid in deaths else whenmax-whenmin ])) # whenmax-whenmin])) 
    if njid in edits_:
      for edit_action in edits_[njid]:
        ## Add big icon
        edits_r = r.rbind(edits_r,c([jid2idx[njid], float(edit_action['when'])-births[njid]]))
        edit_dirs_r = r.c(edit_dirs_r, pch_of_delta(edit_action['initial'],edit_action['final']))

  r.plot(births_r,cex=2.0, col=colors_r, pch='o',xlab='Created date',ylab='Action date', main=title, xlim=r.c(0, notes.count()),ylim=r.c(0, YMAG*(whenmax-whenmin)), axes=False)
  r.points(edits_r, col='black', pch=edit_dirs_r,  cex=edit_delta)
  r.points(deletes_r, cex=2.0,col = 'black', pch='x')
  
  yWeeks = [int(y) for y in range(int(msecToWeek(firstBirth)), int(msecToWeek(whenmax)), 1)]
  r.axis(2, at=c([float(y*7*24*60*60*1000.0) for y in yWeeks]), labels=c([int(x)-2012 for x in yWeeks]), tck=1)

  duds = []
  for x in births.keys():
    if x in deaths and x in colors:
      r.lines(c([float(jid2idx[x])]*2),c([float(jid2idx[x]),float(deaths[x]-births[x])]), col=colors[x])
    else:
      duds.append(x)
  print "skipped %d whose death time was not known " % len(duds)

  goodness_stats = [
    ("notes", len(births) ),
    ("missing note" ,len( [x for x in births if x not in jid2note]) ),
    ("missing text" ,len([x for x in births if x not in texts])),
    ("missing note-delete times" , len([jid2note[x].deleted for x in births if x in jid2note and x not in deaths])),
    ("negative lifetime", len([x for x in births if x in deaths and deaths[x] - births[x] < 0]))
    ]

  print "avg start-end %d " % (median( [deaths[njid]-births[njid] for njid in births.keys() if njid in deaths ] )/(24*60*60*1000.0))

  devoff()
  return goodness_stats

def summarize_goodness(gstats):
  gstats = [dict(x) for x in gstats]
  sumnotes, summissing,meanmissing = sum([x["notes"] for x in gstats]),sum([x["missing note"] for x in gstats]),mean([x["missing note"]*1.0/x["notes"] for x in gstats]),
  print "missing notes %d/%d (%g %%) " % (summissing,sumnotes,meanmissing)
  print "missing note-delete times %d %g " % (sum([x["missing note-delete times"] for x in gstats]),mean([x["missing note-delete times"]*1.0/x["notes"] for x in gstats]))
  print "missing text %d : %g " % (mean([x["missing text"]*1.0/x["notes"] for x in gstats]), mean([x["missing text"]*1.0/x["notes"] for x in gstats]))
  print "negative lifetimes  %d %g " % (sum([x["negative lifetime"] for x in gstats]),mean([x["negative lifetime"]*1.0/x["notes"] for x in gstats]))

  print '\n'.join(["%g"%(x["missing note"]*1.0/x["notes"]) for x in gstats])
  
## basedir like:   "acu/weekly_3/"     
def plot_notelife_with_color(basedir, users, color_fn):#, firstHalf=True):
  i=0
  print "Start time: ", time.gmtime()
  startTime = time.time()
  ##start, end = (0,len(u)/2) if firstHalf else (len(u)/2, len(u)-1)
  for user in users:
    uNotes = Note.objects.filter(owner=user)
    uLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    if (((uNotes.count() >= 120) or (uLogs.count() >= 120)) and ((uNotes.count() >= 50) and (uLogs.count() >= 50))):
      lifelineFlatCollapsedCompareColor(cap.make_filename(basedir + "userid-"+str(user.id)), uNotes, color_function=color_fn)
      i += 1
      pass
    pass
  print "Users processed: ", str(i) , " out of: ", str(len(users))
  print "Finish time: ", time.gmtime()
  finishTime = time.time()


def plot_all_lifelines_for_urls(users):
  plot_notelife_with_color('acu/note_lifeline/urls/', users, one_or_no_url_redblk)

def plot_all_lifelines_for_emails(users):
  plot_notelife_with_color('acu/note_lifeline/emails/', users, one_or_no_email_redblk)

def plot_all_lifelines_for_lines(users):
  plot_notelife_with_color('acu/note_lifeline/lines/', users, one_or_more_lines_multicolor)

def plot_all_lifelines_for_numbers(users):
  plot_notelife_with_color('acu/note_lifeline/numbers/', users, one_or_more_numbers_redblk)

def plot_all_lifelines_for_verbs(users):  ## Takes awhile sometimes... maybe make these later?
  plot_notelife_with_color('acu/note_lifeline/verbs/', users, one_or_more_verbs_redblk)

# missing dayofweek

def plot_all_lifelines_for_timeref_redblk(users):
  plot_notelife_with_color('acu/note_lifeline/timeref/', users, one_or_more_timeref_redblk)

def plot_all_lifelines_for_sentences_redblk(users):
  plot_notelife_with_color('acu/note_lifeline/sentences/', users, two_or_more_sentences_redblk)






## one_or_no_url_redblk
## one_or_no_email_redblk
## one_or_more_lines_multicolor
## one_or_more_numbers_redblk
## one_or_more_verbs_redblk
## one_or_more_daysofweek_redblk
## one_or_more_timeref_redblk
## one_or_more_todoref_redblk
## two_or_more_sentences_redblk



## Plot edits by day of week of created note and day of week of edit
def compareEditsBinWeek(filename, notes, title='Note Lifelines', color_function=one_or_no_url_redblk, YMAG=0.5):
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-delete'])
  ##firstBirth = float(min([x[0] for x in notes.values_list('created')]))
  global firstBirth
  title = "%s -- %s %s %s  " % (title,str(notes.count()),notes[0].owner.email,notes[0].owner.id)
  ## Meta-data for points
  points = {'note-add':r.c(), 'note-delete':r.c()} ## Shortened to just the two, since note-edit added later
  births, deaths = {}, {},
  today = time.time()*1000.0
  print "saving to %s " % cap.make_filename(filename)
  r.png(file=cap.make_filename(filename), w=3200,h=1600) ## 3200x1600, 9600x4800, 12.8x6.4
  colors=dict([(n.jid,color_function(n)) for n in notes])
  
  ## 7 creation bins, each with 7 edit bins inside
  ## Each of 49 bins holds entries detailing when edits happen - plot these on line for that bin!
  creationBins = [[r.c() for i in xrange(7)] for i in xrange(7)] 

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

  points['bin-edits'] = r.c()
  weekdayColors = ['red','orange','yellow','green','blue','grey','brown']
  edit_col = r.c()
  maxDelta = 0


  for n in notes:  ## wCom: not all notes eval'd here may have note-add events !!
    colors_r = r.c(colors_r,colors[n.jid])
    if n.jid in edits_:
      for edit_action in edits_[n.jid]:
        ## Add edit to creationBin
        noteDOW = wUtil.msecToDate(n.created).weekday()
        editDOW = wUtil.msecToDate(edit_action['when']).weekday()
        timeDelta = edit_action['when'] - n.created 
        ##if edit_action['when'] != None and edit_action['when'] > firstBirth and edit_action['when'] < ca.DATABASE_SNAPSHOT_TIME:
          ## Current y-val plots time between edit and creation -- second y-val in comment plots absolute time of edit
        if timeDelta > 1000*3600*24*7:
          points['bin-edits'] = r.rbind(points['bin-edits'], c([int(noteDOW*7+editDOW), float(timeDelta)]))
          maxDelta = max(float(timeDelta), maxDelta)
        
          ##KEEP: points['bin-edits'] = r.rbind(points['bin-edits'], c([int(noteDOW*7+editDOW), float(edit_action['when'])]) )        
          edit_col = r.c(edit_col, weekdayColors[editDOW])
        pass
  xl,yl="Created Date", "Action Date"
  
  #maxDelta = 1000*3600*24*60

  r.plot(points['bin-edits'], cex=3.0, col=edit_col, pch='x' ,xlab=xl,ylab=yl, main=title, xlim=r.c(0, 48), ylim=c([0, float(maxDelta)]), axes=False )
  ##KEEP: , axes=False)#, ylim=c([firstBirth, ca.DATABASE_SNAPSHOT_TIME]) )
  
  ## 1 below, 2 left
  r.axis(1, at=c(range(0,49,7)), labels=c(['Mon','Tue','Wed','Thur','Fri','Sat','Sun']), col='grey' )  

  ## Something wrong here  #help!#
  ## Graph is coming up with tiny y-axis plotting # of days between note-create and edit event
  yTicks, yNames, ySep = [], [], 1000*3600*24 # daily ticks
  for tickTime in range(0,maxDelta, ySep): # daily ticks
    yTicks.append(tickTime)
    yNames.append(float(tickTime)/ySep)
    pass
  r.axis(2, at=c(yTicks), labels=c(yNames))
  #help!#
  
  ##r.points(points['note-edit'], col=colors_r, pch=edit_dir,  cex=edit_delta)  
  ##r.points(points['note-delete'], cex=2.0,col = colors_r, pch='x')
  yWeeks = [int(y) for y in range(int(msecToWeek(firstBirth)), int(msecToWeek(time.time()*1000)), 1)]

  for x in births.keys():
     if x in deaths:
       stillalive = (today-deaths[x] < 0.001)
       color = colors[x] # ('green' if stillalive else 'black')
       ##r.lines( c( [float(births[x])]*2)     ,c([ float(births[x]),float(deaths[x]-births[x]) ]), col=color)
       pass
     pass
  for i in range(0,49,7):
    r.abline(v=float(i)-0.5, col='purple')
    pass
  for i in range(0,49):
    r.abline(v=float(i)-0.5, col='gray')
  devoff()
