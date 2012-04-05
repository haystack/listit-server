import sys
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *

em = User.objects.filter(email="emax@csail.mit.edu")[0]
emn = em.note_owner.all()
dk = User.objects.filter(email='karger@mit.edu')[0]
dkn = dk.note_owner.all()
ws = User.objects.filter(email='wstyke@gmail.com')[0]
wsn = ws.note_owner.all()
kf = User.objects.filter(email='justacopy@gmail.com')[0]
kfn = kf.note_owner.all()
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]

def getSaveAge(notes):
    delays = []
    i = 0
    for nn in notes:
        i += 1
        print 'Note #', i
        logs = ActivityLog.objects.filter(owner=nn.owner, noteid=nn.jid, action='note-save')
        for log in logs:
            delays.append(log.when - nn.created)
            pass
        pass
    delays.sort()
    print "Median # Days:", delays[len(delays)/2] / (1000*60*60*24)
    print 'Ave. # Days:', sum(delays)/(1000*60*60*24*len(delays))
    return delays

def get_save_age_by_users(users):
    """
    Returns list of ages when a note was saved.
    nc.get_save_age_by_users([user1, user2, ...])
    """
    delays = []
    i = 0
    for usr in users:
        i += 1
        print 'User #', i
        logs = ActivityLog.objects.filter(action='note-save', owner=usr)
        print '# note saves: ', logs.count()
        if logs.count() == 0:
            continue
        for log in logs:
            note = Note.objects.filter(owner=usr, jid=log.noteid)
            if len(note) > 0:
                delays.append(log.when - note[0].created)
            pass
        pass
    print "Median # Days:", delays[len(delays)/2] / (1000*60*60*24)
    print 'Ave. # Days:', sum(delays)/(1000*60*60*24*len(delays))
    return delays

def get_save_age_by_users2(users):
    delays = []
    i = 0
    for usr in users:
        i += 1
        print 'User #', i
        for note in Note.objects.filter(owner=usr):
            for log in ActivityLog.objects.filter(owner=note.owner, action='save-note', noteid=note.jid):
                delays.append(log.when - note.created)
                pass
            pass
        pass
    print "Median # Days:", delays[len(delays)/2] / (1000*60*60*24)
    print 'Ave. # Days:', sum(delays)/(1000*60*60*24*len(delays))
    return delays

def getEditDelays(users):
    totalNotes = 0
    editDelays = []
    for user in users:
        notes = Note.objects.filter(owner=user)
        logs = ActivityLog.objects.filter(owner=user, action='note-save')
        nc, lc = notes.count(), logs.count()
        for note in notes:
            notelogs = logs.filter(noteid=note.jid)
            saveTimes = [l.when for l in notelogs]
            if len(saveTimes) != 0:
                editDelays.append(min(saveTimes) - note.created)
            totalNotes += 1
    return {'numNotes': totalNotes,
            'editDelays': editDelays}

# 39 of 

"""
def getNoteCreateTimes(info, ownerID, notes):
    for note in notes:
        info["%s-%s"%(ownerID, note.jid)] = {'created': note.created}
    return info

def addSaveTimeArr(info, ownerID):
    for jid, infoObj in info.items():
        infoObj['note-save'] = []
    for log in ActivityLog.objects.filter(action='note-save'):
        if log.noteid in info:
            info[log.noteid]['note-save'].append(log.when)
    return info

def addMinSaveTime(info):
    for log in ActivityLog.objects.filter(action='note-save'):
        try:
            jid = log.noteid
            if jid in info:
                if 'note-save-min' not in info[jid]:
                    info[jid]['note-save-min'] = log.when
                info[jid]['note-save-min'] = min(
                    log.when,
                    info[jid]['note-save-min'])
                pass
            pass
        except:
            continue
        pass
    return info
"""
