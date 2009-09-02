_activity_log_cache = None
def populate_activity_logs(notes):
    ## gets activity logs for all users of all notes passed in 
    global _activity_log_cache
    owners = [ note["owner"] for note in notes ]
    #leaves them cached:
    _activity_log_cache = _actlogs_to_values(ActivityLog.objects.filter( owner__in=owners ))
    
    #_activity_log_cache = [ a for a in ActivityLog.objects.filter( owner__in=owners ).values("id","action","owner","when","client","noteid","search","noteText") ]

# def activity_logs_for_user(user,action="note-edit"):
#    global _activity_log_cache
#    assert _activity_log_cache is not None, "activity logs is none"
#    return [x for x in _activity_log_cache if x["owner"] == user and x["action"] == action ]    
#    activity_logs_for_note = lambda n,action="note-edit": jv3.models.ActivityLog.objects.filter(action=action,owner=n["owner"],noteid=n["jid"])

def random_notes_slow(n=1000,consenting=True):
    """ returns random subset of notes """
    if consenting:
        users = non_stop_consenting_users()
    else:
        users = non_stop_users()
        
    results = []
    keys = []
    notes = Note.objects.filter(owner__in=users)
    i = 0
    while len(results) < n and i < n+10000:
        note = notes[random.randint(0,notes.count()-1)]
        if note.id not in keys:
            keys.append(note.id)
            results.append(note)            
        i = i + 1
        print "%d " % len(results)
    return results

def _random_notes(n=1000,created_before=None):
    results = []
    keys = []
    
    if created_before is None:
        notes = Note.objects.all()
    else:
        notes = Note.objects.filter(created__lte=created_before)
        
    count = notes.count()
    i = 0
    while len(results) < n and i < n+10000:
        note = notes[random.randint(0,count-1)]
        if note.id not in keys:
            keys.append(note.id)
            results.append(note)            
        i = i + 1
        #print "%g " % (len(results)*1.0/n)
    return results

def lm(notes=None,min_word_freq=3,labeler=note_edits,
       context_fn=lambda x : x,min_content_features_per_note=1,lexicon=None):

    if notes is None:
        full_notes = random_notes()

    # computes a dictionary and transforms note into that dictionary
    terms,fvs,dicts = vectify(full_notes,min_word_freq=min_word_freq,lexicon=lexicon)
    # print "terms : %s " % terms[0:20]
    # 
    filtered_notes = []
    filtered_fvs = []    
    # filters notes for those that at least have min_content_features words
    filtered_combo = [ (full_notes[ii],fvs[ii]) for ii in range(len(full_notes)) if len(fvs[ii]) > min_content_features_per_note ]
    notes = [ fc[0] for fc in filtered_combo ]
    fvs = [ fc[1] for fc in filtered_combo ]

    ##
    print "notes reduced to %s/%s, populating act logs  " % (len(notes),len(fvs))
    ## opulate_activity_logs(notes)
    
    labels = apply(r.c, [labeler(n) for n in notes])
    
    print "done with labels : %d " % len(labels)
    print labels

    content_dim = len(terms)
    termmatrix = r.c()

    print "termify"
    for n_i in range(len(notes)):
        fv = fvs[n_i]
        note = notes[n_i]
        
        ## content features
        content_row=r.rep(0,times=content_dim)
        print fv
        for k,v in fv.iteritems():
            content_row[k]=v
        termmatrix = r.c(termmatrix,content_row)

    print "done termify"
    ## reshape into a matrix plz
    termmatrix = r.t(r.matrix(termmatrix,ncol=len(notes),nrow=content_dim))

    global contextframe
    contextframe = context_frame(notes)
    contextframe["terms"] = termmatrix
    contextframe = r["data.frame"](**contextframe)
    print contextframe

    ro.globalenv["l"] = labels
    ro.globalenv["x"] = contextframe    

    ## kaboom
    ## result = r.lm("l ~ %s " % " + ".join([ "x$%s" % col for col in contextframe.colnames ]))

    pvals = {}
    global results
    results = []
    for col in contextframe.colnames:
        result = r.lm("l ~ x$%s " % col )
        results.append(result)
        try:
            if 'terms.' in col:
                pvals[col[5:]] = r['summary'](result)[3][7]
            else:
                pvals[col] = r['summary'](result)[3][7]
            
        except:
            pass
        
    print pvals
    
#     for ii in range(content_dim):
#         print "%s:%g" % (terms[ii],r.coefficients(result)[ii+1])

    print decompose_results(terms,pvals)

    return full_notes,notes,terms,labels,termmatrix,results,pvals

decompose_results = lambda terms,pvals,pval_thresh=0.10: [ ( terms[ int(term[1:]) - 1],val) for term,val in pvals.iteritems() if val < pval_thresh and term[0] == '.' ]


# def random_notes(n=10000,sscroll_filter=False,created_before=None):    
#     if created_before is None:
#         notes = Note.objects.all()
#     else:
#         notes = Note.objects.filter(created__lte=created_before)
    
#     count = notes.count()
#     print "starting with %d " % count

#     random_ids = []
#     while len(random_ids) < n:
#         r = random.randint(0,count-1)
#         if r not in random_ids:
#             random_ids.append(r)

#     random_ids.sort()
#     print "random ids len %d " % len(random_ids)

#     ## load em all at once
#     notes = _notes_to_values(notes.filter(id__in=random_ids))

#     results = []
#     keys = []
    
#     for note in notes:
#         if sscroll_filter:
#             if ActivityLog.objects.filter(owner=note["owner"],action="significant-scroll").count() < 10:
#                 continue;
            
#         if note["id"] not in keys:
#             keys.append(note["id"])
#             results.append(note)
#             print "%d" % len(results)
#         if len(results) == n:
#             break;

#     return results


# def lm(notes=None,min_word_freq=3,labeler=note_edits,context_fn=lifetime_length_context,min_content_features_per_note=1,lexicon=None):

#     if notes is None:
#         full_notes = random_notes()

#     terms,fvs,dicts = vectify(full_notes,min_word_freq=min_word_freq,lexicon=lexicon)
#     filtered_notes = []
#     filtered_fvs = []

#     print "# of notes/fvs %d %d " % (len(full_notes),len(fvs))

#     filtered_combo = [ (full_notes[ii],fvs[ii]) for ii in range(len(full_notes)) if len(fvs[ii]) > min_content_features_per_note ]

#     notes = [ fc[0] for fc in filtered_combo ]
#     fvs = [ fc[1] for fc in filtered_combo ]    

#     print "reduced to %s " % len(fvs)
#     print "terms(%d) : %s " % (len(terms),repr(terms))
    
#     labels = apply(r.c, [labeler(n) for n in notes])    
#     content_dim = len(terms)

#     # final thing to return
#     predictors = r.c()

#     context_dim = 0

#     for n_i in range(len(notes)):
#         fv = fvs[n_i]
#         note = notes[n_i]

#         context_row = context_fn(note)
#         context_dim = len(context_row)

#         ## content features
#         content_row=r.rep(0,times=content_dim)
#         print fv
#         for k,v in fv.iteritems():
#             content_row[k]=v
#         predictors = r.c(predictors,apply(r.c, context_row),content_row)

#     ## reshape into a matrix plz
#     mpredictors = r.t(r.matrix(predictors,ncol=len(notes),nrow=content_dim+context_dim))

#     print mpredictors
#     print labels

#     fmla = ro.Formula('yo ~ xo')
#     fmla.environment['xo'] = mpredictors
#     fmla.environment['yo'] = labels
    
#     print "type of predicts %s " % repr(type( fmla.environment['xo'] ))
#     print "type of labels %s " % repr(type( fmla.environment['yo'] ))
    
#     result = None
#     try :
#         result = r.lm(fmla)
#         print(r.summary(result))
#     except :
#         sys.exc_info();

#     for ii in range(content_dim):
#         print "%s:%g" % (terms[ii],r.coefficients(result)[ii+context_dim+1])
    
#     return full_notes,notes,terms,labels,mpredictors,result
    
    
    

    # rids = []
    # for i in range(n):
    #     rids.append(random.randint(0,count-1))
    # rids.sort()
    # print "fetching %s" % repr(rids)
    # evts = [ good_events[i] for i in rids ]
    # print "ownering"

    # owners = set([x.owner for x in evts])
    # print owners
    # print set([  is_consenting_study2(o) for o in owners ])
    
    
    #for er in evntrs:
    #print er.entityid
