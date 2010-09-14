## Plot note-version on x-axis, other properties on y-axis via addAmt in 2nd for loop
import math
from datetime import datetime as dd  # Stacked Bar Graph Function Helpers
from jv3.study.wReURL import grabUrls

def vPlot(filename, user):
    numLines = lambda txt: len(txt.splitlines())-txt.splitlines().count('')
    aveSize = lambda a,b: int(float(a)/float(b)) if b != 0 else 0  ## a=quantity of something per how many b elts, if no b, return 0
    wksToIndex = lambda rowWeek, colWeek : rowWeek + (colWeek)*COL_SEGMENTS
    msecToDate = lambda msec : datetime.datetime.fromtimestamp(float(msec)/1000.0)
    DAY_IN_MS = 1000*60*60*24
    COL_SEGMENTS, ROW_GROUPS, GROUP_TYPES = 7,7,5 ## add, edit,edit, del,del
    notes = user.note_owner.all().exclude(jid='-1')
    allLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
    noteD = {'note-add':[], 'note-save':[], 'note-delete':[]}
    nD, nDCount = {}, {} ##[0 for i in range(0,maxVer+1)]
    for log in allLogs:
        if log.noteid == -1:
            continue
        noteArr = notes.filter(jid=log.noteid)
        if len(noteArr) < 1:  ## Processing logs for which we still
            continue          ## have the note (deleted or not)
        note = noteArr[0]
        noteD[log.action].append(log)
        pass
    for noteLog in noteD['note-add']:
        if noteLog.noteid == -1:
            continue
        noteVer = sum([ 1 if log.noteid == noteLog.noteid else 0 for log in noteD['note-save']])
        note = notes.filter(jid=noteLog.noteid)[0]
        ##addAmt = len(notes.filter(jid=noteLog.noteid)[0].contents)
        addAmt = 1 if len(grabUrls(note.contents)) > 0 else 0  ##1 if note.contents.find('http://') != -1 or note.contents.find('.comq/') != -1 else 0
        if addAmt > 5000:
            continue ## Skip atrociously long notes
        if noteVer in nD:
            nD[noteVer] += addAmt
            nDCount[noteVer] +=1
        else:
            nD[noteVer] = addAmt
            nDCount[noteVer] =1
    maxVer=0
    for k,v in nD.items():
        maxVer = max(maxVer, k)
    print maxVer
    nData = [0 for i in range(0,min(maxVer+1,200))]
    nDataC = [0 for i in range(0,min(maxVer+1,200))]
    for k,v in nD.items(): ## k=ver, v=count of whatever's being counted
        if k > 200:
            continue ## skip notes more than 400 versions - emax bug...
        nData[k] = float(v)##/float(nDCount[k])  ## quantity / note average for version=k
        nDataC[k] += nDCount[k] ## Count of notes at each version level
    print nDataC
    r.png(file = '/var/listit/www-ssl/_studywolfe/' + filename + '.png', w=1000,h=500)
    dayNames = ["Mon","Tues","Wed","Thur","Fri","Sat","Sun"]
    colors = r.c("red", 'orange', 'yellow', 'green', 'blue', 'grey', 'brown')
    title = "#Notes:#Logs:Email:ID -- " + str(notes.count()) + ":" + str(allLogs.count()) + ":" + user.email + ":" + str(user.id)
    r.barplot(c(r.rbind(nDataC, nData)), main=title,ylab='# Somethings',beside=True,col=r.c('grey','green'))    ##, col=colors, space=r.c(3,1,0.1,1,.1), names=axisNames, width=c(widths))
    devoff()


vPlot('wv1',gv)
vPlot('wv2',dk)
vPlot('wv3',brenn)
vPlot('wv4',em)


def gen_vPlot():
    i=0
    path = 'acu/ver/urls_1/userid-'
    print "Start time: ", time.gmtime()
    for user in u[:500]:
        uNotes = n.filter(owner=user)
        uLogs = ActivityLog.objects.filter(owner=user, action__in=['note-add','note-save','note-delete'])
        if (((uNotes.count() >= 120) or (uLogs.count() >= 120)) and ((uNotes.count() >= 50) and (uLogs.count() >= 50))):
            vPlot(path + str(user.id), user)
            i += i
            pass
        pass
    print "Users processed: ", str(i) , " out of: ", str(len(u))
    print "Finish time: ", time.gmtime()

        
