## Given ONE user's notes, plot note attribute (created) vs activitylog attribute (when)
def mmmPlot(filename, notes,  title='title'):
    ## Meta-data for title
    allLogs = ActivityLog.objects.filter(owner=notes[0].owner, action__in=['note-add','note-save','note-delete'])
    msecToWeek = 1.0/(1000.0*60*60*24*7)
    msecOfWeek = 1000.0*60*60*24*7
    useremail ,noteCount, actionCount = notes[0].owner.email, notes.count(), allLogs.count()
    title = "#Notes:#Logs:Email -- " + str(noteCount) + ":" + str(actionCount) + ":" + useremail
    ## Meta-data for points
    points = {'note-add':r.c(),'note-save':r.c(),'note-delete':r.c()}
    births , deaths, de, {}
    today = time.time()*1000.0
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=6400,h=3200) ## 3200x1600, 9600x4800, 12.8x6.4
    cc=[x['created'] for x in notes.values('created')]
    dd=allLogs.values('when')
    firstBirthEver = 1217622560992.0
    minBirth, maxBirth = float(min(cc)), float(max(cc))                        ## Week 2011 was first week of listit
    minAction, maxAction = float(min(dd)['when']), float(max(dd)['when'])
    for log in allLogs:
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:
            continue
        note = noteArr[0]
        ## birth/deahts
        births[note.jid] = note.created
        if not note.deleted and note.jid not in deaths:
            deaths[note.jid] = today
            pass
        if (log.action == 'note-delete'):
            deaths[note.jid] = float(log.when)
            points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
        pass
    xl,yl="Created Date", "Action Date"
    r.plot(points['note-add'], cex=1.0,col = "green", pch='o',xlab=xl,ylab=yl, main=title, xlim=r.c(firstBirthEver, time.time()*1000), ylim=r.c(firstBirthEver, time.time()*1000.0), axes=False)
    xWeeks = [float(x) for x in range(firstBirthEver*msecToWeek, time.time()*1000*msecToWeek, 1)]
    yWeeks = [float(y) for y in range(firstBirthEver*msecToWeek, time.time()*1000*msecToWeek, 1)]
    r.axis(1, at=c([float(x*7*24*60*60*1000.0) for x in xWeeks]), labels=c([int(x)-2011 for x in xWeeks]))
    r.axis(2, at=c([float(y*7*24*60*60*1000.0) for y in yWeeks]), labels=c([int(x)-2011 for x in yWeeks]))
    r.poinsave'], cex=2.0,col = "purple", pch=17)
    r.points(points['note-delete'], cex=2.0,col = "dark red", pch='x')
    xWks = float(time.time()*1000 - firstBirthEver) / (1000.0*60*60*24*7)
    yWks = float(time.time()*1000 - firstBirthEver) / (1000.0*60*60*24*7)
    print "min/max for created/action: ", minBirth, " : ",  maxBirth, " : ", minAction, " : ", maxAction
    print "x/y Wks: ", xWks, " : ", yWks
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
mmmPlot('wt1',dkn)
mmmPlot('wt2',nin)
