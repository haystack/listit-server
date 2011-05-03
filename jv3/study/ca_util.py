
import os,sys
from django.contrib.auth.models import User
from jv3.models import *

def is_english(s):
    try:
        le = s.encode('utf-8','ignore')
        return s == le
    except:
        pass
    return False
    
def find_histogram_weirdos(counts, THRESH=1000):
    cur_count = counts[0]
    for i in xrange(0,len(counts)):
        if (counts[i] - cur_count) > THRESH:
            #print "weirdo at offset ", i, (counts[i] - cur_count), counts[i], cur_count
            print i, ",", counts[i]
        cur_count = counts[i]

def notes_with_features(fvs,key,val):
    return [ Note.objects.filter(id=k)[0] for k,x in fvs.iteritems() if x[key] == val]


def printnotes(notes):
    for n in notes:
        print "---------------------------------------------"
        print n.id, " :::::::::::::: "
        print "\"",n.contents,"\""
    

def writenotes(notes,fname="/home/mvk/temp.csv"):
    import csv,codecs
    f = codecs.open(fname,'w','utf-8')
    fw = csv.writer(f)
    for n in notes:
        fw.writerow([n.id,n.owner,n.contents.encode('ascii','ignore')])
    f.close()
    print " wrote ", len(notes)
    
