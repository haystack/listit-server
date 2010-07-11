from datetime import datetime as dd  # Stacked Bar Graph Function Helpers

## Returns true if the time is in the future...
def time_in_future(t):
    return int(time.ctime(latest/1000)[-4:]) >= 2011

test = None
def sBar(filename, user, title='title'):
    notes = user.note_owner.all()
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    bornID, saveID, deadID = [[] for i in range(21)], [[] for i in range(21)], [[] for i in range(21)]
    dayToAdd = lambda wkday : (wkday*3)-2
    dayToEdit = lambda wkday : (wkday*3)-1
    dayToDel = lambda wkday : wkday*3
    for log in allLogs:
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:
            continue
        note = noteArr[0]
        wkday = dd.fromtimestamp(float(log.when)/1000.0).weekday()
        if (log.action == 'note-add') and (log not in bornID[wkday]):
            bornID[dayToAdd(wkday)].append(log)     ## Record birth
            pass
        if (log.action == 'note-save'):   ## Record Save
            saveID[dayToEdit(wkday)].append(log)     
            pass
        if (log.action == 'note-delete'): ## Record Death
            deadID[dayToDel(wkday)].append(log)
            pass
        ##points[log.action] = r.rbind(points[log.action],c([float(note.created),float(log.when)]))
        pass
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=1000,h=500)
    ## Births, Edits, Deaths
    axisNames = r.c("Monday", "Tuesday", "Wednesday", "Thursday",  "Friday", "Saturday", "Sunday")
    raw_data = [len(bornID[0]), len(bornID[1]), len(bornID[2]), len(bornID[3]), len(bornID[4]), len(bornID[5]), len(bornID[6])]
    raw_data.extend([len(deadID[0]), len(saveID[1]), len(saveID[2]), len(saveID[3]), len(saveID[4]), len(saveID[5]), len(saveID[6])])
    raw_data.extend([len(deadID[0]), len(deadID[1]), len(deadID[2]), len(deadID[3]), len(deadID[4]), len(deadID[5]), len(deadID[6])])
    m_data = r.matrix(c(raw_data), nrow = 3, ncol=7, byrow=True)
    subTitle = "Actions: (black) note-add, note-save, note-delete (white)"
    legText = r.c("Note-Add", "Note-Save", "Note-Delete")
    r.barplot(m_data, width=r.c(1,1,1),  legend=legText,main=title,ylab='# Action Logs',beside=True,names=axisNames)
    devoff()

sBar('wt0',gv, "GV Note Action Periodicities")
sBar('wt1',dk, "DK's Note Action Periodicities")
sBar('wt2',em, "Emax's Note Action Periodicities")
sBar('wt3',kf, "KatFang's Note Action Periodicities")
sBar('wt4',ws, "WS's  Note Action Periodicities")
sBar('wt5',brenn, "Brenn's Note Action Periodicities")

sBar('wt5',gv, "GV's Weekly Note-creation") ## 0
sBar('wt6',dk, "DK's  Weekly Note-creation") ## 1
sBar('wt7',em, "Emax's Weekly Note-creation") ## 2
sBar('wt8',kf, "KatFang's Weekly Note-creation") ## 4


