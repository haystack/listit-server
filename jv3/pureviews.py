from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.utils.simplejson import JSONEncoder, JSONDecoder
import django.contrib.auth.models as authmodels
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from jv3.models import Note, NoteForm
from jv3.models import RedactedNote
from jv3.models import WordMap, WordMeta
import jv3.utils
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, BugReport, ServerLog
from jv3.utils import gen_cookie, makeChangePasswordRequest, nonblank, get_most_recent, gen_confirm_newuser_email_body, gen_confirm_change_password_email, logevent, current_time_decimal, basicauth_get_user_by_emailaddr, make_username, get_user_by_email, is_consenting_study1, is_consenting_study2, json_response, set_consenting
import time
from django.template.loader import get_template
import sys
from jv3.views import *

def get_sorted_notes(user):
    ## we want to determine order using magic note
    if Note.objects.filter(owner=request_user,jid="-1").count() > 0:
        magic_note = Note.objects.filter(owner=request_user,jid="-1")[0]
        note_order = JSONDecoder().decode(magic_note.contents)['noteorder']
        notes = [ n for n in Note.objects.filter(owner=request_user,deleted=False).exclude(jid=-1) ]
        def sort_order(nx,ny):
            if nx.jid in note_order and ny.jid in note_order:
                result = note_order.index(nx.jid) - note_order.index(ny.jid)
            else:
                result = int((ny.created - nx.created)/1000)
            return result
        ## sort 'em
        notes.sort(sort_order)
        return notes
    
    notes = Note.objects.filter(owner=request_user,deleted=False).order_by("-created").exclude(jid=-1)
    return notes

def get_pure(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401 ## removed semi-colon??
        return response

    notes = get_sorted_notes(request_user)

    def puredict(note):
        return {"noteText":note.contents,
            "edited":note.edited,
            "pk":note.id,
            "jid":note.jid,
            "col":80,
            "row":1,
            "version":note.version,
            "deleted":"false",
            "created":note.created}

    ndicts = [ puredict(note) for note in notes ]

    #htmlblob = "\n".join([ "<div class='note' nid='%(jid)s' id='%(jid)s' style='display:%(startVisibility)s'><img class='deleteX' src='arrow-left.png' alt='Delete' onMouseOver='zenNoteView.dispNoteOptions(\"%(jid)s\", true)' onmouseout=\"zenNoteView.noteOptions.startTimer();\"/> <textarea name='note'  edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onFocus='zenNoteView.noteClicked(\"%(jid)s\")' cols='%(col)s' rows='%(row)s' hasFocus='false' hasSelect='false' onBlur='zenNoteView.noteBlur(\"%(jid)s\")' style='overflow:hidden'>%(noteText)s</textarea></div>" % n for n in ndicts ])
    
    htmlblob = "\n".join(["<div class='note' id='%(jid)s' %(noteText)s</div>" % n for n in ndicts ])    
    response = HttpResponse(htmlblob, 'text/html');
    response.status_code = 200
    return response
