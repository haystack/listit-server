data = None
def sBar(filename, user, title='title'):
    COL_SEGMENTS = 7
    notes = user.note_owner.all()
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    bornID, saveID, deadID = [[] for i in range(21)], [[] for i in range(21)], [[] for i in range(21)]
    global data
    data = r.matrix(0,nrow=COL_SEGMENTS, ncol=21) ## 3 cols per weekday, each col segmented into 7 parts/rows
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
            ##bornID[wkday].append(log)
            pass
        elif (log.action == 'note-save'):   ## Record Save
            ##saveID[dayToEdit(wkday)].append(log)
            data[wksToIndex(birthDay, actDay*3+1)] += 1
            ##saveID[wkday].append(log)
            pass
        elif (log.action == 'note-delete'): ## Record Death
            ##deadID[dayToDel(wkday)].append(log)
            data[wksToIndex(birthDay, actDay*3+2)] += 1
            ##deadID[wkday].append(log)
            pass
        ##points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
        pass
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=1000,h=500)
    ## Births, Edits, Deaths
    ##axisNames = r.c("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",'','','','','','','','','','','','','','')
    axisNames = c(["","Mon.","","","Tue.","","","Wed.","","","Thur.","","","Fri.","","","Sat.","","","Sun.",""])
    ##raw_data = [len(bornID[i]) for i in range(7)]  ##raw_data.extend([len(saveID[i]) for i in range(7)]) ##raw_data.extend([len(deadID[i]) for i in range(7)])
    ##m_data = r.matrix(c(raw_data), nrow = 3, ncol=7, byrow=True)
    subTitle = "Actions: (black) note-add, note-save, note-delete (white)"
    legText = r.c("Note-Add", "Note-Save", "Note-Delete")
    colors = r.c("red", 'orange', 'yellow', 'green', 'blue', 'grey', 'brown')
    r.barplot(data, legend=legText ,main=title,ylab='# Action Logs',beside=False, col=colors, space=r.c(3,1,1), names=axisNames)
    devoff()


sBar('wt00',gv,"GV's Note Action Periodicities")
