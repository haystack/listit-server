## startup
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from numpy import array
r = ro.r
em = User.objects.filter(email="emax@csail.mit.edu")[0]
c = lambda vv : apply(r.c,[float(v) for v in vv])

def hist(data,breaks="auto",auto_nbins_top=50,auto_nbins_skip=1,filename="/var/www/hist.out.png",title="histogram of something",xlabel="x",ylabel="counts",width=1280,height=1024):
    # data should be raw [1,2,1,2,3,2,...]
    # 
    r.png(file=filename,width=width,height=height)
    # print data
    if type(breaks) == list:
        breaks = c(breaks)
    elif breaks == "auto":
        ## breaks = r.c(r.seq(0,50,1),10000)
        breaks = r.seq(min(data), max(auto_nbins_top,max(data)+1), auto_nbins_skip)
        
    print breaks
        
    histout = r.hist(c(data),breaks=breaks,plot=True,main=title,xlab=xlabel,ylab=ylabel)
    r('dev.off()')
    return histout

def loghist(data,breaks="Scott",auto_nbins_top=50,auto_nbins_skip=1,filename="/var/www/hist.out.png",title="histogram of something",xlabel="x",ylabel="counts",width=1280,height=1024):
    # data should be raw [1,2,1,2,3,2,...]
    # 
    r.png(file=filename,width=width,height=height)
    # print datalabel
    if type(breaks) == list:
        breaks = c(breaks)
    elif breaks == "auto":
        ## breaks = r.c(r.seq(0,50,1),10000)
        breaks = r.seq(min(data), max(auto_nbins_top,max(data)+1), auto_nbins_skip)

    print "data: %s " % c(data)
    print breaks        
    histout = r.hist(c(data),breaks=breaks,plot=False,main=title,xlab=xlabel,ylab=ylabel)
    kwargs = {"names.arg":[x for x in histout[0]][1:]}
    print kwargs
    print histout[1]
    r.barplot( c([log(x+1)/log(10) for x in histout[1]] ),plot=True,main=title,**kwargs) 
    r('dev.off()')
    return histout


def scatter(data,filename="/var/www/scatter.out.png",title="histogram of something",xlabel="x",ylabel="y",width=1280,height=1024):
    ## data should be [ (x,y) .. ]
    # example: cap.scatter( [(n['jid'],n['deleted']) for n in renotes[0]],title="deleted versus not deleted", xlabel="not deleted/deleted", ylabel="# of notes (out of 2500)")
    r.png(file=filename,width=width,height=height)
    out = r.plot(c([float(d[0]) for d in data]),c([float(d[1]) for d in data]),main=title,xlab=xlabel,ylab=ylabel)
    r('dev.off()')
    return out

def bar(data,filename="/var/www/bar.out.png",title="barplot of something",xlabel="x",ylabel="y",width=1280,height=1024):
    ## data should be : [ (colname,5), ... ]
    # example: cap.bar({"foo":123,"bar":200,"baz":299}.items())
    r.png(file=filename,width=width,height=height)
    kwargs = { "names.arg" : c([d[0] for d in data]) }
    print c( [d[1] for d in data])
    out = r.barplot( c( [d[1] for d in data] ), **kwargs )
    r('dev.off()')
    return out

def sbar(data,filename="/var/www/bar.out.png",title="barplot of something",xlabel="x",ylabel="y",width=1280,height=1024):
    # stacked bar
    # example: cap.bar({"foo":[123,444],"bar":[200,222],"baz":[299,111]}.items())
    r.png(file=filename,width=width,height=height)
    kwargs = { "names.arg" : c([d[0] for d in data]) }
    print c( [d[1] for d in data])
    inner_dim = len(d[0])
    catted = r.c( c([d[1] for d in data]) )
    print "dim : %s % " % repr(inner_dim)
    out = r.barplot( r.matrix(catted,c(inner_dim,1)), **kwargs )
    r('dev.off()')
    return out

