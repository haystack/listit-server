## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)
def mmmPlot(filename, notes,  title='title'):
  ## Meta-data for title
  allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-save','note-delete'])
  useremail = notes[0].owner.email
  noteCount = notes.count()
  actionCount = allLogs.count()
  title = "#Notes:#Logs:Email -- " + str(noteCount) + ":" + str(actionCount) + ":" + useremail 
  ## Meta-data for points
  points = {'note-add':r.c(),'note-save':r.c(),'note-delete':r.c()}
  births = {}
  deaths = {}
  today = time.time()*1000.0
  r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=3200,h=1600)
  minCreatedMSEC, maxCreatedMSEC = 0, 0
  minActionMSEC, maxActionMSEC = 0, 0
  for log in allLogs:
     noteArr = notes.filter(jid=log.noteid)
     if len(noteArr) < 1:
        continue
     note = noteArr[0]
     minCreatedMSEC = min(minCreatedMSEC, note.created)
     maxCreatedMSEC = max(maxCreatedMSEC, note.created)
     minActionMSEC = min(minActionMSEC, log.when)
     maxActionMSEC = max(maxActionMSEC, log.when)
     ## birth/deahts
     births[note.jid] = note.created
     if not note.deleted and note.jid not in deaths:
        deaths[note.jid] = today
        pass
     if (log.action == 'note-delete'):
        deaths[note.jid] = float(log.when)
     points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
     pass
  r.plot(points['note-add'], cex=1.0,col = "green", pch='o',xlab='Created Date',ylab='Action Date', main=title)
  r.points(points['note-save'], cex=2.0,col = "purple", pch=17)
  r.points(points['note-delete'], cex=2.0,col = "dark red", pch='x')
  #r.lines( reduce(r.rbind,[r.c(float(births[x]),float(deaths[x])) for x in births.keys() if x in deaths],r.c()), col = "dark red")
  xWks = (maxCreatedMSEC - minCreatedMSEC) / (1000*60*60*24*7)
  yWks = (maxActionMSEC - minActionMSEC) / (1000*60*60*24*7)
  r.grid(nx=int(xWks), ny=int(yWks), col="black", lwd=1)
  for x in births.keys():
     if x in deaths:
        if today - deaths[x] < 0.001 :
           color = 'green'
        else:
           color = 'black'
        r.lines(c([float(births[x])]*2),c([float(births[x]),float(deaths[x])]), col=color)
        pass
  devoff()

mmmPlot('wt0',emn)
