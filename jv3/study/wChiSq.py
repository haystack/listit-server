## Chi Square Tests!
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
import jv3.study.thesis_figures as tfigs
import jv3.study.wUtil as wUtil
from jv3.study.thesis_figures import n2vals
import r.chisq

r = ro.r
c = lambda vv : apply(r.c,vv)
devoff = lambda : r('dev.off()')



def chi_sq_edits_per_user(user):
    notes = Note.objects.filter(owner=user)
    edits_ = ca.note_edits_for_user(notes[0].owner)
    chiMatrix = r.matrix(c([0 for i in range(49)]), ncol=7,nrow=7)
    for n in notes:
        if n.jid in edits_:
            createdDOW = wUtil.msecToDate(n.created).weekday()
            for edit_action in edits_[n.jid]:
                timeDelta = edit_action['when'] - n.created
                if timeDelta > 1000*3600*24*7:
                    ## For each edit of this note, find editDOW and increment spot in matrix
                    editDOW = wUtil.msecToDate(edit_action['when']).weekday()
                    chiMatrix[createdDOW+editDOW*7] += 1
                    pass
                pass
            pass
        pass
    print chiMatrix
    print '--------------------------------------------'
    result = r('chisq.test')(chiMatrix)
    print result
    print '--------------------------------------------'
    return result


def chisq_edits_for_users(users):
    chiMatrix = r.matrix(c([0 for i in range(49)]), ncol=7,nrow=7)
    for user in users:
        notes = Note.objects.filter(owner=user)
        edits_ = ca.note_edits_for_user(user)
        for n in notes:
            if n.jid in edits_:
                createdDOW = wUtil.msecToDate(n.created).weekday()
                for edit_action in edits_[n.jid]:
                    timeDelta = edit_action['when'] - n.created
                    if timeDelta > 1000*3600*24*7:
                    ## For each edit of this note, find editDOW and increment spot in matrix
                        editDOW = wUtil.msecToDate(edit_action['when']).weekday()
                        chiMatrix[createdDOW+editDOW*7] += 1
                        pass
                    pass
                pass
            pass
        pass
    result = r('chisq.test')(chiMatrix)
    return (result, chiMatrix)
