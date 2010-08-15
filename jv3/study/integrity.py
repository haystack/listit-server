## startup
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
from django.db.models.query import QuerySet
from jv3.study.ca_plot import make_filename
r = ro.r
c = lambda vv : apply(r.c,vv)
def createadddist(u):
   nid2when = {}
   nid2create = {}

   # BUG IN DJANGO? query returns 0 
   # u = User.objects.filter(id=u.id) ## reproducible error
   if type(u) == User:
       u = [x for x in User.objects.filter(id=u.id)]
   elif type(u) == QuerySet:
       u = [x for x in u]
       
   # print u,type(u),len(u)
   print "alog ", ActivityLog.objects.filter(action__in=["note-add"],owner__in=u).count()

   keh = lambda o,nid : "%d:%d" % (o,nid)
   
   for when,noteid,owner in ActivityLog.objects.filter(owner__in=u,action="note-add").values_list('when','noteid','owner'):
      nid2when[keh(owner,noteid)] = nid2when.get(keh(owner,noteid),[]) + [when]

   for noteid,when,owner in reduce(lambda x,y: x+y, [ [x for x in U.note_owner.all().values_list('jid','created','owner')] for U in u]):
      nid2create[keh(owner,noteid)] = when

   print "notes length %d "% len(nid2create)
   print "alog length %d " % len(nid2when)
   
   print "notes missing %d " %len( [x for x in nid2when.keys() if x not in nid2create.keys()])
   print "alog missing %d " %len([x for x in nid2create.keys() if x not in nid2when.keys()])
   print "intersection %d " %len([x for x in nid2create.keys() if x in nid2when.keys()])

   intersection = [x for x in nid2create.keys() if x in nid2when.keys()]

   number = [len(x) for x in nid2when.values()]
   mind = [float(min(nid2when[T]) - nid2create[T]) for T in intersection ]   
   maxd = [float(max(nid2when[T]) - nid2create[T]) for T in intersection ]

   bogusnotes = [Note.objects.filter(jid=T.split(':')[1],owner=T.split(':')[0]) for T in intersection if float(min(nid2when[T]) - nid2create[T]) > 10000]

   return (number,mind,maxd,bogusnotes)

months = [0, 'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

def cumulative_registrations(width=1000,height=700):
   registrations = [float(x[0])/1000.0 for x in UserRegistration.objects.values_list('when')]
   registrations.sort()
   total = 0
   cudist = {}
   for i in registrations:
      total += 1
      cudist[i] = total
   print make_filename('registrations')
   r.png(file=make_filename('registrations'),width=width,height=height)
   r.plot(c(cudist.keys()), c([x for x in cudist.values()]),xlab='',ylab='',axes=False)
   days = 60
   print len(r.seq(min(registrations),max(registrations),24*60*60*days))   
   r.axis(1, r.seq(min(registrations),max(registrations),24*60*60*days),
           [ "%s %d" % (months[x.tm_mon],x.tm_year) for x in
             [time.localtime(b) for b in xrange(min(registrations), max(registrations), 24*60*60*days)]])

   # label the max
   r.axis(2,r.c(r.seq(0,((total/5000)+1)*5000,5000),total),r.c(r.seq(0,((total/5000)+1)*5000,5000),total))
   r.title('cumulative listit registrations (august 2008-august 2010)')
   
   #   r.lines(c([float(x) for x in cudist.keys()]), c([x for x in cudist.values()]),xlab=r.c(),ylab=r.c()))
   r('dev.off()')


#########################################################

def cumulative_time_till_delete(notes,filename='ttd',width=1280,height=800,xlim_days=90):
   tlim = 24*60*60*xlim_days
   deletions = dict([(x[0],float(x[1]/1000)) for x in
                ActivityLog.objects.filter(owner=notes[0].owner,noteid__in=[x.jid for x in notes],action='note-delete').values_list('noteid','when')])
   creations = dict([(x[0],float(x[1])/1000) for x in notes.values_list('jid','created')])
   
   d1 = [ (deletions[d] - creations[d]) for d in deletions.keys() if d in creations.keys()]
   d1.sort()
   durations = [D for D in d1 if D > 0 and D < 24*60*60*xlim_days]
   print "durations: ", len(durations)
   total = 0
   cudist = {}
   for i in durations:
      total += 1
      cudist[i] = total

   print make_filename(filename)
   r.png(file=make_filename(filename),width=width,height=height)
   r.plot(c(cudist.keys()), c([x*1.0/len(d1) for x in cudist.values()]),xlab='',ylab='',axes=False,xlim=r.c(0,tlim))
   BUCKET = 24*60*60

   breaks = r.seq(0,tlim+BUCKET,BUCKET)
   r.axis(1,breaks,[x/(24*60*60) for x in breaks ])
   r.lines(r.c(0,7000.0),r.c(0,1000.0),lwd=2,col='black')
   r.title('percentage of deleted notes deleted after X days after it was created (user: %s) ' % notes[0].owner.email)
   r('dev.off()')

def cumulative_time_for_all_users(users):
    for u in users:
        print u,len(u.note_owner.all())
        try:
            cumulative_time_till_delete(u.note_owner.all(),filename='ttd/%s'%u.email)
        except:
            r('dev.off()')
            pass

#             deletions = dict([(x[0],tosecs(x[1])) for x in
#                       ActivityLog.objects.filter(owner=user,
#                                                  noteid__in=[x.jid for x in notes],
#                                                  action='note-delete').values_list('noteid','when')])
    

############################################################

def nuke_reedits(vec,threshold=10*60): # ten minutes
    if len(vec) < 2 : return;
    tonuke = []
    last = vec[0]
    for v in vec[1:] :
        if v - last < threshold:
            tonuke.append(v)
        last = v
    print "deleting %d " % len(tonuke)
    [vec.remove(v) for v in tonuke if v in vec]
    pass

def edit_recency(notes,action='note-save',filename='recency',width=1280,height=1024, nuke_consecutive_edits=True):
    user = notes[0].owner
    tosecs = lambda s : float(s/1000)
    creations = dict([(x[0],tosecs(x[1])) for x in notes.values_list('jid','created')])

    
    actlogs = ActivityLog.objects.filter(owner=user, action=action, noteid__in=[ n.jid for n in notes]).values('when','noteid')
    actlogd = {}
    for a in actlogs:
        actlogd[a['noteid']] = actlogd.get(a['noteid'],[]) + [tosecs(a['when'])]
        
    edits_since_creation_per_note = dict([ (n.jid, [(x - creations[n.jid]) for x in actlogd.get(n.jid,[])]) for n in notes ] )
    if nuke_consecutive_edits : [nuke_reedits(x) for x in edits_since_creation_per_note.values()]
    #edits_since_creation_per_note = dict([ (n.jid, [ (tosecs(x['when']) - creations[n.jid])  for x in ActivityLog.objects.filter(owner=user, action='note-save', noteid=n.jid).values('when')]) for n in notes ])
    edits_since_creation_all = reduce(lambda x,y : x + y, edits_since_creation_per_note.values())

    
    breaks = [0,60,60*60] + [i*24*60*60 for i in range (1,7)] + [i*7*24*60*60 for i in range (2,13)]
    breaklabels = ['1 min','1 hr'] + ["%d days" % x for x in range(1,7)]  + ["%d weeks" % x for x in range(2,13)]
    edits_since_creation_all = [x for x in edits_since_creation_all if x < max(breaks) and x > 0]    
    
    print max(breaks), max(edits_since_creation_all), max(breaks)-max(edits_since_creation_all)
    r.png(file=make_filename(filename),width=width,height=height)
    r.hist(c(edits_since_creation_all),breaks=c(breaks),labels=c(breaklabels),freq=True,xlab='',ylab='',main='frequency of edits to notes (measured in time since creation) %s' % user.email)
    r('dev.off()')

def edit_recency_batch(users,basepath='edit_since_creation/'):
    index = 0
    for u in users:
        print u,len(u.note_owner.all())
        try:
           edit_recency(u.note_owner.all(),filename=('%s/recency-%d'%(basepath,index)))
           index = index + 1
        except:
            try:
                r('dev.off()')
            except:
                pass

def delete_recency_batch(users,basepath='delete_since_creation/'):
    index = 0
    for u in users:
        print u,len(u.note_owner.all())
        try:
           edit_recency(u.note_owner.all(),action='note-delete',filename=('%s/recency-%d'%(basepath,index)))
           index = index + 1
        except:
            try:
                r('dev.off()')
            except:
                pass
            
def time_till_deletehist(notes,width=1024,height=768):
    delete_logs = lambda n : ActivityLog.objects.filter(owner=n.owner,noteid=n.jid,action='note-delete')
    if type(notes) == QuerySet:  notes = notes.filter(deleted=1)
    else: notes = [n for n in notes if n.deleted]
    vals = []
    for n in notes:
        dl = delete_logs(n)
        if dl.count() == 0: continue
        if float(dl[0].when)/1000 - float(n.created)/1000 > 0:
            vals.append( float(dl[0].when)/1000 - float(n.created)/1000 );
    r.png(file=make_filename('ttd'),width=width,height=height)

    breaks = r.c(0,60*60,2*60*60,24*60*60,2*24*60*60,r.seq(3*24*60*60,max(vals)+24*60*60,24*60*60))
    rr = r.hist( c(vals),breaks=breaks,axes=False,xlab='',ylab='',ylim=r.c(0,10))
    r('dev.off()')

    r.png(file=make_filename('ttd'),width=width,height=height)
    r.barplot(rr[1])
    print len(breaks)
    print len([x/60*60 for x in breaks])
    r.axis(1,at=r.seq(0,len(breaks)-1),labels=[x/(24*60*60) for x in breaks])
    r('dev.off()')
    return rr
    

# def createadddist(u=emax):
#    number = []
#    mind = []
#    maxd = []
#    for n in u.note_owner.all():
#       addnote = [x['when'] for x in ActivityLog.objects.filter(noteid=n.jid,owner=emax,action="note-add").values('when')]
#       number.append( len(addnote) )
#       print len(addnote), " ",
#       if len(addnote) == 0: continue
#       if len(addnote) > 0:
#          mind.append(float(n.created) - float(addnote[0]))
#          print float(n.created) - float(addnote[0])
#       if len(addnote) == 1:
#          maxd.append('same')
#       else:
#          maxd.append( mind.append(float(n.created) - float(addnote[-1])))
         
#    return (number,mind,maxd)
