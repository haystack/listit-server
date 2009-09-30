
# 
from eyebrowse.models import *
import csv

def h(s):
    import md5
    md5 = md5.md5()
    md5.update(s) 
    return md5.hexdigest()

identity = lambda s: s

def get_cols(obfuscator=h):
    return {
        'username': lambda pageview: obfuscator(pageview.owner.email),
        'start_time': lambda pageview: pageview.startTime,
        'end_time': lambda pageview: pageview.endTime,
        'url': lambda pageview: pageview.url,
        'host': lambda pageview: pageview.host
    }     

def dump_pageviews_csv(filename='/tmp/foo.csv',user=None,pvrecords=None):
    f = open(filename,'w')    
    csv_writer = csv.writer(f, dialect='excel')
    if user:
        pvrecords = PageView.objects.filter(user=user).order_by('startTime')
        colgens = get_cols(identity) # no encryption
        csv_writer.writerow(colgens.keys())
        for x in pvrecords:
            csv_writer.writerow([ col(x) for col in colgens.values() ])
    else:
        pvrecords = PageView.objects.all().order_by('startTime')
        colgens = get_cols(h) # no encryption
        csv_writer.writerow(colgens.keys())
        for x in pvrecords:
            csv_writer.writerow([col(x) for col in colgens.values() ])
    f.close()
