from datetime import datetime as dd  # Stacked Bar Graph Function Helpers

def sBar(filename, user, title='title'):
    COL_SEGMENTS, ROW_GROUPS, GROUP_TYPES = 7,7,3
    notes = user.note_owner.all()
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    data = r.matrix(0,nrow=COL_SEGMENTS, ncol=ROW_GROUPS*GROUP_TYPES) ## 3 cols per weekday, each col segmented into 7 parts/rows
    wksToIndex = lambda rowWeek, colWeek : rowWeek + (colWeek)*COL_SEGMENTS
    for log in allLogs:
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:  ## Processing logs for which we still
            continue          ## have the note (deleted or not)
        note = noteArr[0]
        actDay = dd.fromtimestamp(float(log.when)/1000.0).weekday()
        birthDay = dd.fromtimestamp(float(note.created)/1000.0).weekday()
        if (log.action == 'note-add'):      ## Record Add
            data[wksToIndex(birthDay,actDay*3)] += 1
            pass
        elif (log.action == 'note-save'):   ## Record Save
            data[wksToIndex(birthDay, actDay*3+1)] += 1
            pass
        elif (log.action == 'note-delete'): ## Record Death
            data[wksToIndex(birthDay, actDay*3+2)] += 1
            pass
        pass
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=1000,h=500)
    dayNames = ["Mon","Tues","Wed","Thur","Fri","Sat","Sun"]
    colSums = r.colSums(data)
    colMax = r.apply(data, 2, r.max) ## VooDoo !? Returns array of column max values
    colRatios = [int(float(100*colMax[i])/float(colSums[i])) if colSums[i] != 0 else 0 for i in range(ROW_GROUPS*GROUP_TYPES)]
    axisNames = []
    [axisNames.extend([dayNames[i], colRatios[i*3+1], colRatios[i*3+2]]) for i in range(ROW_GROUPS)] 
    subTitle = "Actions: (black) note-add, note-save, note-delete (white)"
    colors = r.c("red", 'orange', 'yellow', 'green', 'blue', 'grey', 'brown')
    title = "#Notes:#Logs:Email:ID -- " + str(notes.count()) + ":" + str(allLogs.count()) + ":" + user.email + ":" + str(user.id)
    r.barplot(data, main=title, ylab='# Action Logs',beside=False, col=colors, space=r.c(3,1,1), names=axisNames) ## legend=logText
    devoff()


sBar('wt00',gv,"GV's Note Action Periodicities")

def test_wBar():
    sBar('wt1',gv, "GV Note Action Periodicities")            ## Was 6-11 (accidentally over-wrote 6!)
    sBar('wt2',dk, "DK's Note Action Periodicities")
    sBar('wt3',em, "Emax's Note Action Periodicities")
    sBar('wt4',kf, "KatFang's Note Action Periodicities")
    sBar('wt5',ws, "WS's  Note Action Periodicities")
    sBar('wt6',brenn, "Brenn's Note Action Periodicities")

def makeACUBarPlots():
    i=0
    path = 'acu/rhythms/weekly_1/userid-'
    print "Start time: ", time.gmtime()
    for user in u[750:]:
        uNotes = n.filter(owner=user)
        uLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
        if (((uNotes.count() >= 120) or (uLogs.count() >= 120)) and ((uNotes.count() >= 50) and (uLogs.count() >= 50))):
            sBar(path + str(user.id), user)
            i += 1
            pass
        pass
    print "Users processed: ", str(i) , " out of: ", str(len(u))
    print "Finish time: ", time.gmtime()

