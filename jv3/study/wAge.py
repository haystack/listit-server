## Plot of X-axis: age of a user's notes (birth to death), Y-axis: Try to correlate something with age!!

def bAge(filename, user, title="Note Age vs Weekday, aveLines= "):  ## where do i get global database_snapshot time??
    dbSnapTime = 1.27815e12
    firstBirthEver = 1217622560992.0
    filename = cap.make_filename(filename)
    msecToDate = lambda msec : dd.fromtimestamp(float(msec)/1000.0)
    msecToWeek = 1.0/(1000.0*60*60*24*7)
    notes = Note.objects.filter(owner=user)
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    addLogs, saveLogs = allLogs.filter(action='note-add'), allLogs.filter(action='note-save')
    delLogs = allLogs.filter(action='note-delete')
    addIDs, delIDs = {},{} ## Map jid to when(msec) action happened
    aveLines = sorted([note.contents.count('\n') for note in notes])[notes.count()/2] / float(notes.count())
    title +=  str(aveLines)
    for item in addLogs.values_list('noteid','when'): ## dict of created notes
        addIDs[item[0]] = item[1] if item[0] != -1 else True 
    for item in delLogs.values_list('noteid','when'): ## dict of deleted notes
        delIDs[item[0]] = item[1]
    noteAge, ptSize, ptCol = r.c(), r.c(), r.c()
    dayCols = ['red','orange','yellow','green','blue','grey','brown']
    for noteid, when in addIDs.items():
        note = notes.filter(jid=noteid)
        if len(note) != 1:
            continue
        note = note[0]
        if note.version > 200 or len(note.contents) >= 200000 or len(note.contents.split('\n')) >= 200: ## Some notes are obvious error-riddled ones...
            continue
        actDate = msecToDate(when)
        wkDay = actDate.weekday()
        yVal = actDate.weekday()  ##note.contents.count('\n')
        ##1 if note.deleted else w0##len(grabUrls(note.contents)) ## change this!!!!!!!!!!!!!!!!
        size = 2 if note.contents.count('\n') < aveLines else 4
        col = dayCols[actDate.weekday()]
        if noteid in delIDs:
            noteAge = r.rbind(noteAge, c([(float(delIDs[noteid])-float(when))/(1000.0*60*60*24), int(yVal)]))
        else:
            noteAge = r.rbind(noteAge, c([(float(dbSnapTime)-float(when))/(1000.0*60*60*24), int(yVal)]))
        ptSize = r.rbind(ptSize, c([size]))
        ptCol = r.rbind(ptCol, c([col]))
        pass
    ## Now noteAge has all note id's mapped to note's age
    r.png(file = filename, w=3000,h=1500) ## 3200x1600, 9600x4800, 12.8x6.4
    xl,yl = 'Note Age in days','Something!!'
    r.plot(noteAge, cex=ptSize,col = ptCol, pch='o',xlab=xl,ylab=yl, main=title)##, xlim=r.c(firstBirthEver, dbSnapTime))##, axes=False)
    devoff()

bAge('ba6',dk)
bAge('ba7',gv)
bAge('ba8',em)

    
                             
                             
   
