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
import jv3.study.exporter as exporter
import json

r = ro.r
c = lambda vv : apply(r.c,vv)

########################################################
# 

def participant_report():
   print "users "
   cu = [ u for u in User.objects.all() if is_consenting_study2(u)]
   print "total %d " % len(User.objects.all())
   print "total nonotes %d " % len([ u for u in User.objects.all() if u.note_owner.count() == 0])
   print "consenting %d " % len(cu)
   print "consenting somenotes %d " % len([c for c in cu if c.note_owner.count() > 0])
   print "consenting nonotes %d " % len([c for c in cu if c.note_owner.count() == 0])
   print "total notes %d " % Note.objects.exclude(owner__in=excluders).count()
   print "consenting notes %d " % Note.objects.filter(owner__in=cu).count()
   durations = [ float(u.note_owner.order_by('-edited')[0].edited - u.note_owner.order_by('edited')[0].edited)/(24.0*60.0*60000.0) for u in User.objects.all() if u.note_owner.count() > 0  ]   
   print 'average total length of activity min:%g max:%g median:%g mean: %g:' % (min(durations),max(durations),median(durations),mean(durations))
   durations = [ float(uact.serverlog_set.order_by('when')[uact.serverlog_set.count()-1].when - uact.serverlog_set.order_by('-when')[uact.serverlog_set.count()-1].when) for uact in User.objects.all() if uact.serverlog_set.count() > 0]
   print 'average duration of use min:%g max:%g median:%g mean: %g:' % (min(durations),max(durations),median(durations),mean(durations))   
   print 'users still active in the last 14 days %d' % len(set([x['user'] for x in ServerLog.objects.order_by('when').filter(when__gt=repr(time.time()*1000 - 14*24*60*60000)).values('user')]))

months = [0, 'jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']


#################################################################
# cumulative registrations figure
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
# time until deletion distribution, but NOT INCLUDED
# @see edit_recency below
def cumulative_time_till_delete(notes,filename='ttd',width=1280,height=800,xlim_days=90):
   tlim = 24*60*60*xlim_days
   deletions = dict([(x[0],float(x[1]/1000)) for x in ActivityLog.objects.filter(owner=notes[0].owner,noteid__in=[x.jid for x in notes],action='note-delete').values_list('noteid','when')])
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

############################################################
# edit_recency // delete_recency
# shows distribution of times-since-creation that notes
# get edited or deleted
# optional: cancelling of "adjacent edits"
def edit_recency(notes,action='note-save',filename='recency',width=1280,height=1024, nuke_consecutive_edits=True):
    user = notes[0].owner
    tosecs = lambda s : float(s/1000)
    creations = dict([(x[0],tosecs(x[1])) for x in notes.values_list('jid','created')])

    
    actlogs = ActivityLog.objects.filter(owner=user, action=action, noteid__in=[ n.jid for n in notes]).values('when','noteid')
    actlogd = {}
    for a in actlogs:
        actlogd[a['noteid']] = actlogd.get(a['noteid'],[]) + [tosecs(a['when'])]
        
    edits_since_creation_per_note = dict([ (n.jid, [(x - creations[n.jid]) for x in actlogd.get(n.jid,[])]) for n in notes ] )

    # if note save, then we might want to obliterate adjacent re-edits; e.g., people editing over and over again
    # because they're likely to re-edit something they've touched
    if action == 'note-save' and nuke_consecutive_edits : [nuke_reedits(x) for x in edits_since_creation_per_note.values()]

    edits_since_creation_all = reduce(lambda x,y : x + y, edits_since_creation_per_note.values())
    
    breaks = [0,60,60*60] + [i*24*60*60 for i in range (1,7)] + [i*7*24*60*60 for i in range (2,13)]
    breaklabels = ['1 min','1 hr'] + ["%d days" % x for x in range(1,7)]  + ["%d weeks" % x for x in range(2,13)]
    # filter things out
    edits_since_creation_all = [x for x in edits_since_creation_all if x < max(breaks) and x > 0]    
    
    # print max(breaks), max(edits_since_creation_all), max(breaks)-max(edits_since_creation_all)
    r.png(file=make_filename(filename),width=width,height=height)
    r.hist(c(edits_since_creation_all),breaks=c(breaks),labels=c(breaklabels),freq=True,xlab='',ylab='',main='frequency of edits to notes (measured in time since creation) %s' % user.email)
    r('dev.off()')

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
    


def debug_distance_between_note_add_and_creation_times(u):
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


## note length distribtion
def plot_note_words_hist(notes,filename="num_words",width=1024,height=800,soft_max=300):
   user = notes[0].owner
   nwords = [ca.note_words(x)[1] for x in notes.values("contents")]
   
   nchars_  = [len(x["contents"].strip()) for x in notes.values("contents")]
   nchars = [x for x in nchars_ if x < soft_max]

   r.png(file='/dev/null',width=width,height=height)
   breaks=[x for x in xrange(soft_max)]
   nchars = r.hist(c(nchars),breaks=c(breaks))[1]
   r('dev.off()')
   
   r.png(file=make_filename(filename),width=width,height=height)
   nwords_ = [x for x in nwords]
   nwords = [x for x in nwords if x < soft_max]

   hh = r.hist(c(nwords),breaks=c(breaks),labels=c(breaks), freq=True,xlab='',ylab='',main='length of notes (in words) %s (%d)' % (user.email,len(notes)))
   print len(breaks)," ", len(nchars)
   print nchars
   r.lines(c(breaks[:-1]),nchars,col='green')
   r.text(r.c(3.0/4.0*soft_max),r.c(3.0/4.8*max(hh[1])+0.1*max(hh[1])),"notes min-median-mode-max: %f %f %f %f" % (min(nwords_),median(nwords_),ca.mode(nwords_),max(nwords_)))
   r.text(r.c(3.0/4.0*soft_max),r.c(3.0/4.8*max(hh[1])),"char min-median-mode-max: %f %f %f %f" % (min(nchars_),median(nchars_),ca.mode(nchars_),max(nchars_)))

   r('dev.off()')
   return hh

def batch(fn,users,batchpath):
   index = 0
   for u in users:
      print u,len(u.note_owner.all())
      try:
         fn(u.note_owner.all(),filename=('%s/%d'%(batchpath,index)))
         index = index + 1
      except:
         try:
            print sys.exc_info();
            r('dev.off()')
         except:
            pass
      pass
   pass

batch_note_words = lambda users,batchpath="note_words/": batch(plot_note_words_hist, users, batchpath)

## this method goes and performs all plots a user at a time

n2vals = lambda n :{"contents":n.contents,"jid":n.jid,"owner":n.owner,"version":n.version,"deleted":n.deleted,"created":n.created,"id":n.id}
text2vals = lambda ntext :{"contents":ntext}

def htmlesc(text):
   if text is None: return "<None>"
   import cgi
   return cgi.escape(text).replace('\n','<br>').encode('ascii','ignore')

njidtodel={}
def time_till_deletion(n):
   global njidtodel
   if n.owner.email not in njidtodel:
      vs = ActivityLog.objects.filter(owner=n.owner,action="note-delete").values_list("noteid","when")
      
      max_deletes = {}
      for jid,when in vs:
         if not (jid in max_deletes) or max_deletes[jid] < float(when):
            max_deletes[jid] = float(when)
            
      njidtodel[n.owner.email] = dict([(jid, (when-float(n.created))) for jid,when in max_deletes.iteritems()])
   return njidtodel[n.owner.email].get(n.jid,None)

juxtapose_n_props = lambda i,n_created,n_text,n : "".join(
   [("<td>%s</td>" % repr(x)) for x in [
         i,
         int(n.jid),
         exporter.makedate_usec(float(n_created)),
         (time_till_deletion(n)/(24*60*60*1000) if time_till_deletion(n) is not None else "-?-") if n.deleted else "NOT DELETED",        
         len(n_text) if n_text is not None else 0,
         ca.note_words(text2vals(n_text))[1] if n_text is not None else 0,
         ca.note_lines(text2vals(n_text))[1] if n_text is not None else 0,
         ca.note_edits(n2vals(n)),
         htmlesc(n_text)         
    ]])

njidtosave={}
def juxtapose_note(i,n):
   ## cache all the note-saves, build chronological revision array { user.id : { noteid: (when, contents), (when, contents) , ... } }
   global njidtosave
   if n.owner.email not in njidtosave:
      person = {}
      for when,noteid,contents,action in ActivityLog.objects.filter(owner=n.owner,action__in=["note-add","note-save"]).values_list("when","noteid","noteText","action"):
         person[noteid] = person.get(noteid,[]) + [(float(when),contents,action)]
      for nid,edits in person.iteritems():
         edits.sort(key=lambda x:-x[0]) # reverse
      njidtosave[n.owner.email] = person
      pass
   olde = ""
   if n.jid in njidtosave[n.owner.email]:
      olde = ''.join(['<tr class="note_olde %s" jid="%s" owner="%s" version="%s">%s</tr>' %
                      ("add" if action == "note-add" else "edit", n.jid, n.owner.email, n.version, juxtapose_n_props(i,when,text,n)) for when,text,action in njidtosave[n.owner.email][n.jid]])
   newe = '<tr jid="%s" owner="%s" version="%s" class=\"note_current\">%s</tr>' % (n.jid,n.owner.email,n.version,juxtapose_n_props(i,n.created,n.contents,n))
   return newe + olde

def juxtapose_make_fname(i):
   return "index-%d.html" % i
def juxtapose_make_range(start,end,step):
   return' &nbsp '.join(['<a href="'+juxtapose_make_fname(i)+'"> [%d] </a>' % i for i in xrange(start,end+step,step)])
def juxtapose_html(body,range_end,range_step):
   return """
<html>
<head>
<title>notes juxt</title>
<script src="http://astroboy.csail.mit.edu/js/sorttable.js" type="text/javascript"></script>
<link rel="stylesheet" type="text/css" href="http://astroboy.csail.mit.edu/_studyplots/juxta.css" type="text/javascript"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js"></script>
<script type="text/javascript" src="http://astroboy.csail.mit.edu/_studyplots/juxta.js"></script>
</head>
<body>
%s
<hr>
%s
<hr>
%s
</body>
</html>
""" % (juxtapose_make_range(0,range_end,range_step),
       body,
       juxtapose_make_range(0,range_end,range_step))

juxtapose_imgs = lambda fname: ('<a href="%s.png" target="_blank"><img src="thumbs/%s.png"></a>' % (fname,fname))

def juxta_basicstats(u):
   ns = u.note_owner
   nvals = u.note_owner.values()
   stats = (
      ("N", ns.count()),  ## number of notes
      ("keep/del" ,"%s/%s" % (ns.filter(deleted=0).count(),ns.filter(deleted=1).count())),
      ("s:", exporter.makedate_usec(  min([float(x['created']) for x in nvals]) )),
      ("l:", exporter.makedate_usec(  max([ float(x['edited']) for x in nvals] + [ float(x['created']) for x in nvals ]))),
      ("|words|", mean([ca.note_words(nvs)[1] for nvs in nvals])),
      ("|chars|",  mean([len(nvs['contents'].strip()) for nvs in nvals])),
      ("|urls%|",sum([1 for nvs in nvals if ca.note_urls(nvs)[1] > 0])/(1.0*ns.count())*100),
      ("|#vers|",mean([float(nvs['version']) for nvs in nvals]))
   )
   return '<span class="userstats">%s</span>' % "; ".join([ '%s: <span class="val">%s</span>' %
                                                            (k,v) for k,v in stats])      

def juxtapose_notes(notes):
   innards =  "".join([juxtapose_note(i,notes[i]) for i in xrange(len(notes))])   
   return """
   <table class="sortable">
   <thead>
     <tr>
     <th>_</th>
     <th>jid </th>
     <th>created </th>
     <th>deleted</th>
     <th>nchars</th>
     <th>nwords</th>
     <th>nlines</th>
     <th>version</th>
     <th>text</th>
     </tr>
   </thead>
   <tbody>
     %s
   </tbody>
   </table>
   """ % innards


def juxtapose_user(u,user_index):

   import jv3.study.wNotes as w
   import jv3.study.wFunc as wF
   import jv3.study.wBar as wB

   juxtapose_fns = [
      lambda n,i:("lifeline-%d"%i,wF.mmmPlot("lifeline-%d"%i,n,'lifetime for notes %s' % n[0].owner.email)),  ## modified to wF.mmmPlot  (also, title is being over-written, will change soon)
      lambda n,i:("edit-recency-%d"%i,edit_recency(n,filename="edit-recency-%d"%i)),
      lambda n,i:("delete-recency-%d"%i,edit_recency(n,action='note-delete',filename="delete-recency-%d"%i,nuke_consecutive_edits=False)),
      lambda n,i:("note-length-%d" % i,plot_note_words_hist(n,filename="note-length-%d"%i,soft_max=500)),
      lambda n,i:("periodicity-%d" %i, wB.sBar("periodicity-%d"%i,n[0].owner)) ## added
   ]
   
   ns = u.note_owner.order_by('created').all()

   fnames = []
   for fn in juxtapose_fns:
      fname, foo = fn(ns,user_index)
      fnames.append(fname)
   return '<div class="user" owner="%s">%s (%s): %s<br>%s<br>%s</div>' % (u.email, u.email,
                                                                          juxta_basicstats(u),
                                                                          '<span class="comments">[ comments ]</span><textarea class="commentfield">**COMMENT SERVER DOWN DO NOT LEAVE COMMENTS**</textarea>',
                                                                          "".join([juxtapose_imgs(f) for f in fnames]),
                                                                          '<div class="shownotes">notes</div><div class="notes"' + juxtapose_notes(ns) +"</div>"
                                                                          )

def batch_juxtapose(users,basedir):
   ca.make_feature=lambda k,v:(k,v)
   cadt.make_feature=lambda k,v:(k,v)   
   cap.set_basedir(basedir)
   index = 0
   set_len = 10
   for user_n_slice in [slice(x,x+set_len) for x in xrange(0,len(users),set_len)]:
      html = ''         
      uset = users[user_n_slice]
      for u in uset:
         try:
            html = html + juxtapose_user(u,index)
            index = index + 1
            pass
         except:
            import traceback
            print sys.exc_info()
            traceback.print_tb(sys.exc_info()[2])
            try:
               r('dev.off()')
            except:
               pass

      filename = "%s/%s" % (basedir,juxtapose_make_fname(user_n_slice.start))
      f = open(filename,'w')
      print "writing ",filename
      f.write(juxtapose_html(html,len(users),set_len))
      f.close()
   return len(html)

# nc.batch_note_words(interesting_consenting)


## supporting comments
def _comments_read():
   import csv,settings,time
   f0 = "%s/%s" % (settings.THESIS_FIGURE_STUDY_DB,"index.csv")
   datas = {}
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      datas = dict([(r[0],r[1]) for r in rdr])
      F.close()
   return datas

def _comments_write(comments):
   import csv,settings,time
   f0 = "%s/%s" % (settings.THESIS_FIGURE_STUDY_DB,"index.csv")
   f1 = "%s/%s" % (settings.THESIS_FIGURE_STUDY_DB,"index-%s.csv" % time.ctime().replace(' ','_'))
   for f in [f0,f1]:
      print f
      F = open(f,'w')
      wtr = csv.writer(F)
      [ wtr.writerow([uuid,comm]) for uuid,comm in comments.iteritems() ]
      F.close()
      pass
   pass

def _get_comment(uid):
   print uid
   return _comments_read().get(uid,"")

def _save_comment(uid,comment):
   hs = _comments_read()
   hs[uid] = comment
   _comments_write(hs)
   return hs
        
# non-jsonp        
def get_comments(request):
   return HttpResponse(json.dumps(_comments_read()),"text/json")

def get_comments_view_jsonp(request):
   try :   
      callback = request.GET['callback']
      return HttpResponse('%s(%s)' % (callback, json.dumps(_comments_read())),"text/json")
   except:
      import traceback
      print sys.exc_info()
      traceback.print_tb(sys.exc_info()[2])      
   
def update_comment_view_jsonp(request):
   try :
      print request.GET.keys()
      print request.raw_post_data
      callback = request.GET['callback']
      uid = request.GET['uid']
      comment = request.GET['comment']
      print "COMMENTSAVE %s : %s " % (uid, comment)
      _save_comment(uid,comment)     
      return HttpResponse('%s(%s)' % (callback, json.dumps({"status":'ok'})),"text/json")
   except:
      import traceback
      print sys.exc_info()
      traceback.print_tb(sys.exc_info()[2])      
   
