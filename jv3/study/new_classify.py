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
import jv3.study.f as stuf
r = ro.r
emax = User.objects.filter(email="emax@csail.mit.edu")[0]
emax2 = User.objects.filter(email="electronic@gmail.com")[0]
brenn = User.objects.filter(email="brennanmoore@gmail.com")[0]
gv = User.objects.filter(email="gvargas@mit.edu")[0]
wstyke = User.objects.filter(email="wstyke@gmail.com")[0]
katfang = User.objects.filter(email="justacopy@gmail.com")
karger = User.objects.filter(email="karger@mit.edu")
devoff = lambda : r('dev.off()')
c = lambda vv : apply(r.c,vv)

import nltk
from nltk.tokenize import WordTokenizer
import nltk.cluster as cluster
import numpy
from numpy import array



def notes_to_bow_features_nltk(notes, docs=None, word_proc=lambda x: x.lower().strip(), text=lambda x: x["contents"],limit=None):
    tokenizer = WordTokenizer()
    notewords = lambda x : [ word_proc(x) for x in tokenizer.tokenize(text(x)) ]

    id2nw = dict([(x['jid'],notewords(x)) for x in notes])
    wfq = nltk.FreqDist(reduce(lambda x,y: x + y, id2nw.values()))

    start = int(len(wfq)*0.03)
    if limit is None: limit=int(0.25*len(wfq))
    print "len", len(wfq), "taking",limit
    
    freqkeys = wfq.keys()[start:start+limit]
    print "frequent keys"
    print '\n'.join([repr(x) for x in wfq.iteritems()][start:start+limit])
    print len(freqkeys)
    
    if docs is None: docs = {}
    for n in notes:
        wfq = nltk.FreqDist(id2nw[n['jid']])
        fv = docs.get(n["jid"],[])
        fv = fv + [ ("freq_%s" % x, wfq[x]) for x in freqkeys ]
        docs[n["jid"]] = fv
    
    return docs

ca.make_feature=lambda k,v:(k,v)
def notes_to_note_features(notes,docs=None):
    if docs is None: docs = {}
    for n in notes:
        fv = docs.get(n["jid"],[])
        fv = fv + [ x(n) for x in ca.content_features ]
        docs[n["jid"]] = fv    
    return docs    

def km_cluster_docs(docs,nclusters=3,normalise=True,distance=cluster.cosine_distance,svd_d=None):
    # first convert to numeric vectors
    dv = (lambda docs: ([(id, array([count for fname,count in dfreq])) for id,dfreq  in docs.iteritems() if sum([count for fname,count in dfreq]) > 0 ]))(docs)

    n_features = len(dv[0][1])
    rand_means = [array([random.random() for i in xrange(n_features)]) for j in xrange(nclusters)]
    
    if svd_d is not None:
        kmc = cluster.KMeansClusterer(nclusters,distance=distance,normalise=normalise,svd_dimensions=svd_d,initial_means=rand_means) ## svd is horribly
    else:
        kmc = cluster.KMeansClusterer(nclusters,distance=distance,normalise=normalise,initial_means=rand_means)

    print "Documents: ",len([dv_[1] for dv_ in dv])
    for dv_ in dv:
        print dv_[1]
    kmc.cluster([dv_[1] for dv_ in dv])
    #print kmc.cluster(dv.values())
    classes_by_jid = dict( [(id,kmc.classify(fv)) for id,fv in dv] )
    return dv,classes_by_jid,kmc


def km_r_cluster(docs,nclusters=3):
    # first convert to numeric vectors
    dv = (lambda docs: ([(id, c([count for fname,count in dfreq])) for id,dfreq  in docs.iteritems() if sum([count for fname,count in dfreq]) > 0 ]))(docs)

    print "Documents: ",len([dv_[1] for dv_ in dv])
    for dv_ in dv: print dv_[0],":",dv_[1]    

    rows = reduce(lambda x,y: r.rbind(x,y), [dv_[1] for dv_ in dv])
    rows = r.scale(rows)
    #print r.princomp(rows)
    args = {"iter.max":100}
    clusters = r.kmeans(rows,nclusters,**args)
    return dv,clusters,r.kmeans(r.princomp(rows)[5],nclusters)


def gmm_cluster_docs(docs,nclusters=3,svd_d=5):
    # gaussian mixture model 
    # first convert to numeric vectors
    import random
    dv = (lambda docs: ([(id, array([count for fname,count in dfreq])) for id,dfreq  in docs.iteritems() if sum([count for fname,count in dfreq]) > 0 ]))(docs)

    n_features = len(dv[0][1])
    rand_means = [array([random.random() for i in xrange(n_features)]) for j in xrange(nclusters)]
    
    kmc = cluster.EMClusterer(rand_means,normalise=True) ## ,svd_dimensions=svd_d) ## svd is horribly 

    kmc.cluster([dv_[1] for dv_ in dv])
    #print kmc.cluster(dv.values())
    classes_by_jid = dict( [(id,kmc.classify(fv)) for id,fv in dv] )
    return dv,classes_by_jid,kmc


def print_classes(notes,classes):
    jid2text = dict([(n["jid"],n["contents"].replace('\n',' ')) for n in notes])
    for jid,clazz in classes.iteritems():
        print "%s : %s" % (clazz,jid2text[jid][:100])

def print_r_classes(notes,dv,cluster):
    jid2text = dict([(n["jid"],n["contents"].replace('\n',' ')) for n in notes])
    for i in xrange(len(dv)):
        jid = dv[i][0]
        clazz = cluster[0][i]
        print "%s : %s" % (clazz,jid2text[jid][:100])

        
# import jv3.study.new_classify as nc
# notes = emax.note_owner.all()[1000:].values()                  
#bb = nc.notes_to_bow_features_nltk(notes)
#bb = nc.notes_to_note_features(notes,bb)

# don't use this: cc,classes,km = nc.km_cluster_docs(bb,10)
# nc.print_classes(notes,classes)                  

# use these:
#dv,clusters,pclusters = nc.km_r_cluster(bb,10)
#nc.print_r_classes(notes,dv,clusters)


## Wolfe Edits:
## use  km_r_cluster     not km_cluster_Docs    

    


