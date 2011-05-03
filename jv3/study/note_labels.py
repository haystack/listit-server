import sys,os
from django.contrib.auth.models import User
from jv3.models import *
from jv3.utils import *
import jv3.study.content_analysis as ca
import jv3.study.diagnostic_analysis as da
import jv3.study.ca_datetime as cadt
import jv3.study.ca_sigscroll as cass
import jv3.study.ca_load as cal
import jv3.study.ca_plot as cap
import jv3.study.ca_search as cas
import jv3.study.wFunc as wF
import rpy2
import rpy2.robjects as ro
from jv3.study.study import *
from jv3.study.thesis_figures import n2vals
from numpy import array
import jv3.study.content_analysis as ca
import codecs
import nltk

r = ro.r
c = lambda vv : apply(r.c,vv)

import csv,settings,time

blank_field = "---"

def is_feature_name(s):
    return hasattr(ca,s)

def read(filename=None):
   f0 = "%s/%s" % (settings.NOTE_LABELINGS_DIR, "index.csv" if filename is None else filename )
   #print f0
   datas = []
   note_fields = []
   feature_fields = []      
   label_fields = []
   
   if os.path.isfile(f0):
      F = open(f0,'r')
      rdr = csv.reader(F)
      # first row defines the labels
      headings = rdr.next()
      
      n = Note.objects.all()[0]
      # split headers into note fields and label fields

      for header in headings:
          #print header
          if hasattr(n,header):
              # it's a note field
              note_fields.append(header)
          elif is_feature_name(header):
              feature_fields.append(header)
          else:
              label_fields.append(header)
      
      [ datas.append(dict(zip(headings,r))) for r in rdr ]
      F.close()
   
   return { "note_fields": note_fields, "label_fields": label_fields, "feature_fields": feature_fields, "notes" : datas }

def compute_feature_named(feature_name,n):
    if getattr(ca,feature_name,None):
        return getattr(ca,feature_name)(n2vals(n))[feature_name]  ## compute the feature given the note!
    return None

def add_notes(ns):
    label_struct = read()
    has_notes = [x["id"] for x in label_struct["notes"]]
    
    for n in ns:        
        if n.id in has_notes: continue # skip if we already hazzit        
        note_dict = dict([(field,getattr(n,field)) for field in label_struct["note_fields"]])

        # now we want to process each of the features
        for feature_name in label_struct["feature_fields"]:
            note_dict[feature_name] = compute_feature_named(feature_name,n)
            
        # now we want to add labels
        for label_name in label_struct["label_fields"]:
            note_dict[label_name] = blank_field

        label_struct["notes"].append(note_dict)        
    return label_struct

def update_features(new_features, labels_struct):
    if isinstance(new_features,basestring):
        new_features = new_features.strip().split(',')
    # labels_struct gets modified in-place
    old_features = labels_struct["feature_fields"]
    for note_dict in labels_struct["notes"]:
        print note_dict
        for of in old_features:
            del note_dict[of]
        for feature_name in new_features:
            n = Note.objects.filter(id=note_dict["id"])[0]
            note_dict[feature_name] = compute_feature_named(feature_name, n)
            
    labels_struct["feature_fields"] = new_features

def _write(labels_struct):
    # history is a list of dict s [ {when: "", to: "", "text" : "" } ... ]
    import csv,settings,time
    # GHETTO JOURNALLING APPROACH (tm) COPYRIGHT 2010 EMAX. (I SHOULD PATENT THIS IDEA.)
    f0 = "%s/%s" % (settings.NOTE_LABELINGS_DIR,"index.csv")
    f1 = "%s/%s" % (settings.NOTE_LABELINGS_DIR,"index-%d-%d-%d%d.csv" % (time.localtime().tm_year,
                                                                          time.localtime().tm_mon,
                                                                          time.localtime().tm_mday,
                                                                          time.localtime().tm_hour))
    for f in [f0,f1]:
        F = open(f,'w')
        wtr = csv.writer(F)      
        row_keys = reduce(lambda x,y : x + y, [labels_struct[x] for x in ["note_fields", "feature_fields", "label_fields"]])
        # write the headers
        wtr.writerow(row_keys)
        # write the datas
        def check_type(s):
            if isinstance(s,basestring):
                return s.encode('ascii','ignore')
            return s
        
        [ wtr.writerow([ check_type(data[key]) for key in row_keys ]) for data in labels_struct["notes"] ]
        F.close()
        pass
    pass

def is_note_interesting(n):
    from jv3.utils import is_tutorial_note
    from jv3.study.wClean import is_activity_log_fail
    c = n.contents
    return len(c.strip()) > 1 and not is_activity_log_fail(c) and not is_tutorial_note(n)

def random_notes(N=1000,consenting=True):
    import random,jv3.study.thesis_figures
    emax = [User.objects.filter(email="emax@csail.mit.edu")[0],User.objects.filter(email="electronic@gmail.com")[0]]
    note_count = Note.objects.all().count()
    good_note_ids = [x.id for x in Note.objects.exclude(owner__in=emax).filter(owner__in=jv3.study.thesis_figures.get_interesting_consenting()) if is_note_interesting(x)]
    return Note.objects.filter(id__in=random.sample(good_note_ids,N))

## decision tree stuff ~~~ 
def build_tree(label_struct, label_column, features, method='anova'):
    # make formula
    xs = features   # ["x%s" % i for i in range(len(features))]
    fla = " y ~ %s " % " + ".join(xs)
    fmla = ro.Formula(fla)
    env = fmla.environment

    for fi in range(len(features)):
        fvec = r.c()
        fname = features[fi]
        for n in label_struct["notes"]:
            fvec = r.c(fvec,int(n[fname]))
        env[fname] = fvec
        print fname, "----", fvec

    fyvec = r.c()
    for n in label_struct["notes"]:
        fyvec = r.c(fyvec,n[label_column])
        
    if method == 'anova':
        env['y'] = fyvec
    else:
        env['y'] = r.factor(fyvec)
        print r.levels(env['y'])

    r('library(rpart)')
    return r('rpart')(fmla,method=method)

def get_unique_labels(struct):
    return set([x['label_note_type'] for x in struct['notes']])

# import jv3.study.prep_parse abbbs pp
# ca.set_tagger(pp.get_brill())
# struct = nl.read()
# tree = nl.build_tree(inn,'label_note_type',['note_urls','note_verbs','note_words','note_date_count','note_emails','numbers','note_phone_numbers'],method='class')
# tree = nl.build_tree(struct,'note_lines',['note_urls','note_verbs'],method='class')
# r.png('/var/www/emax/foo.png')
# r.plot(tree)
# r.text(tree, **{"use.n":True, "all":True, "cex":.8})
# r('dev.off()')
    


## stuff for importing from excel markup
# def get_sample1(fname='sample1-combined.csv'):
#     f0 = "%s/%s" % (settings.NOTE_LABELINGS_DIR,fname)
#     csvr = csv.reader(open(f0,'Ur'))
#     xx = [x for x in csvr]
#     csvd = [dict(zip(xx[0],b)) for b in xx]
#     return csvd

label_columns = {'sample1/sample1-nolabels-mc.csv':1,
              'sample1/sample1-emax.csv':11,
              'sample1/sample1-nolabels-ip.csv':2,
              'sample1/sample1-alberto.csv':2,
              'sample1/sample1-nolabels-fg.csv':2,
              'sample1/sample1-nolabels-pa3.csv':2,
              'sample1/sample1-alisdair.csv':0,
              'sample1/sample1-nolabelsec.csv':2}

id_columns = {'sample1/sample1-nolabels-mc.csv':0,
               'sample1/sample1-emax.csv':0,
               'sample1/sample1-nolabels-ip.csv':0,
               'sample1/sample1-alberto.csv':0,
               'sample1/sample1-nolabels-fg.csv':0,
               'sample1/sample1-nolabels-pa3.csv':0,
               'sample1/sample1-alisdair.csv':1,
               'sample1/sample1-nolabelsec.csv':0}

#id_columns = {'sample1/sample1-alberto.csv':0}

def get_sample1():
    text_by_note = {} 
    by_note = {}
    by_user = {}
    def split(s):
        s = s.lower().replace(';',',')
        s = s.lower().replace(' and ',',')
        s = s.lower().replace(' or ',',')
        s = s.lower().replace('/',',')
        return [x.lower().strip() for x in s.split(",")]
    def load(fname):
        f0 = "%s/%s" % (settings.NOTE_LABELINGS_DIR,fname)
        print f0
        csvr = csv.reader(open(f0,'Ur'))
        xx = [x for x in csvr]
        for row in xx:
            print row
            if len(row) <= label_columns[fname] : continue
            noteid,label = row[id_columns[fname]],row[label_columns[fname]]
            for sublabel in split(label):
                by_note[noteid] = by_note.get(noteid,[]) + [sublabel]
                by_user[fname] = by_user.get(fname,[])+[sublabel]
    [load(f) for f in id_columns]
    [text_by_note.update({iid:ca.note_abbreviated_contents(Note.objects.filter(id=int(iid)).values()[0])['note_abbreviated_contents']})for iid in by_note.keys() if len(iid) > 0 and not iid == "id"]
    return by_note,dict([(x,set(y)) for x,y in by_user.iteritems()]),text_by_note

def print_sample1(tags_by_note,text_by_note):
    for t in text_by_note:
        print t,":",text_by_note[t]
        print "; ".join([x for x in tags_by_note[t] if len(x) > 0])
        print "-----------------"    

def get_factors(ss):
    # prints out all the possible labels_per_user_that_labeled_it, can handle a single sheet with _all_ users
    import re
    cols = [c for c in ss[0] if c.find("label_") == 0]
    #splitup = lambda s : [x.strip().lower() for x in s.split(',') if not s.strip().lower() == 'or'] if s is not None else []
    splitup = lambda s : [x.strip().lower() for x in re.findall(r'\w+', s) if not s.strip().lower() == 'or'] if s is not None else []
    return [(c,set(reduce(lambda x,y:x+y,[[nn for nn in splitup(x.get(c,None))] for x in ss[1:]]))) for c in cols]

STOPLABELS = ['???','FOREIGN','TEST']
def note_labels(ss,n,filter_questions=True) :
    print n
    labels = reduce(lambda x,y : x+y,[n[lf].split(";") for lf in ss['label_fields']])
    if filter_questions:
        labels = filter(lambda x : not x in STOPLABELS, labels)
    if len([x for x in labels if x.strip() == '']):
        print "------------------------------------------L!@KJ#LK!J@#LK#!@J -",n
        raise Exception()
    return labels

def get_distribution_of_types(ss,filename=None,width=1600,height=1200):
    from jv3.study.ca_plot import make_filename

    get_all_labels_for_notes =  lambda notes: reduce(lambda x,y:x+y,[note_labels(ss,n) for n  in notes])
    if filename is not None:
        r.png(file=make_filename(filename),width=width,height=height)
    t = r.table(r.factor(c(get_all_labels_for_notes(ss['notes']))))  # #reduce(lambda x,y:x+y,[note_labels(ss,n) for n  in ss['notes']]))))
    
    if filename is not None:
        t = r.sort(t,decreasing=True)
        r.barplot(t,names=t,col='white')
        r.legend(40,r.max(t),r.names(t),cex=0.90)
        r('dev.off()')

    ## find freqs -- compare max and min

    return t,nltk.FreqDist(get_all_labels_for_notes(ss['notes']))

    # counts = {}    
    # for n in ss['notes']:
    #     for l in note_labels(n):
    #         counts[l] = counts.get(l,0) + 1
    # return counts

# xx = nl.get_distribution_of_types(nr,'note_type_dist_aggressive')
# xx[1]['CONTACT']+ xx[1]['WEB_BOOKMARK']+ xx[1]['TODO']+ xx[1]['CALENDAR']
# [y for y,z in xx[1].iteritems() if z == 1]
# Out[949]: 
# ['ACCOUNTNUMBER',
#  'ADDRESS',
#  'ADJECTIVE',
#  'AUCTION',
#  'DONE',
#  'EDITS',
#  'EXPRESSION',
#  'FACTS',
#  'FUNNY',
#  'ITINERARY',
#  'MARKUP',
#  'MESSAGES',
#  'OTHER',
#  'PLACE',
#  'PROBLEM',
#  'SHOPPINGLIST',
#  'STATE',
#  'THOUGHT',
#  'TIPS',
#  'TODOLIST',
#  'TRACKING']

