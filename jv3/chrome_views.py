
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
from jv3.models import RedactedNote ##, RedactedSkip
from jv3.models import WordMap, WordMeta
import jv3.utils
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, BugReport, ServerLog, CachedActivityLogStats, ChromeLog
from jv3.utils import gen_cookie, makeChangePasswordRequest, nonblank, get_most_recent, gen_confirm_newuser_email_body, gen_confirm_change_password_email, logevent, current_time_decimal, basicauth_get_user_by_emailaddr, make_username, get_user_by_email, is_consenting_study1, is_consenting_study2, json_response, set_consenting
from django.template.loader import get_template
import sys,string,time,logging
import tempfile,os
from decimal import Decimal
from jv3.views import *

def _filter_dupes(note_queryset):
    distinct_jids = set([x[0] for x in note_queryset.values_list('jid')])
    notes = {}
    for n in note_queryset:
        if n.jid in notes and notes[n.jid].id < n.id : continue
        notes[n.jid] = n
    return [notes[n.jid] for n in note_queryset]

## Chrome Extension Get/Post Methods
def get_json_notes(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401
        return response
    
    ## Filter out notes that have already been redacted
    notes = _filter_dupes(request_user.note_owner.filter(deleted=0).order_by("-created"))

    ndicts = [ extract_zen_notes_data(note) for note in notes ]
    allNotes = []
    for note in ndicts:
        allNotes.append(
            {"jid":note['jid'],"version":note['version'], "contents":note['noteText'],
             "deleted":note['deleted'], "created":str(note['created']),
             "edited":str(note['edited']) })

    allNotes.sort(lambda x,y:cmp(x['created'], y['created']) )

    
    response = HttpResponse(JSONEncoder().encode({"notes":allNotes}), "text/json")
    response.status_code = 200
    return response

def post_json_notes(request):
    return put_zen(request)

def sort_user_for_notes(request_user, note_list):
    ## Sort and return user's notes
    if request_user.note_owner.filter(jid="-1").count() > 0:
        ## we want to determine order using magic note
        magic_note = request_user.note_owner.filter(jid="-1")[0]
        note_order = JSONDecoder().decode(magic_note.contents)['noteorder']
        notes = filter(lambda x: x.jid != -1,note_list)
        def sort_order(nx,ny):
            if nx.jid in note_order and ny.jid in note_order:
                result = note_order.index(nx.jid) - note_order.index(ny.jid)
            else:
                result = int((ny.created - nx.created)/1000)
            return result
        ## sort 'em
        notes.sort(sort_order)
    else:
        # sort by creation date ?
        ##notes = filter(lambda x : x.jid != -1, django_notes)
        notes = filter(lambda x: x.jid != -1, note_list)
        notes.sort(key=lambda x:-x.created)
    return notes


# def carefully(fn):
#     import sys, traceback
#     def boo(*args,**kwargs):
#         try:
#             return fn(*args,**kwargs)
#         except Exception as exc:
#             print "Unexpected error:", sys.exc_info()[0]
#             print str(exc)
#             traceback.print_exc(file=sys.stdout)
#             raise
#     return boo

carefully = lambda fn: fn

@carefully
def getUpdatedNotes(clientUnmodifiedNoteInfo, userNotes):
    """
    Return notes that were modified by the server (userNotes) but not the client.
    Tested
    """
    updateFinal = []
    for jid, ver in clientUnmodifiedNoteInfo:
        jid = int(jid)
        if (jid == -1):
            continue
        ver = int(ver)
        notes = [u for u in userNotes if u.jid == jid]
        if notes and notes[0].version > ver:
            note = extract_zen_notes_data(notes[0])
            updateFinal.append({"jid": note['jid'],
                                 "version": note['version'],
                                 "created":str(note['created']),
                                 "edited": str(note['edited']),
                                 "deleted": note['deleted'],
                                 "contents": note['noteText'],
                                 "modified": 0})
            pass
        pass
    return updateFinal

@carefully
def post_json_get_updates(request):
    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401;
        return response
    if not request.raw_post_data:
        response = HttpResponse(JSONEncoder().encode({'committed':[]}), "text/json")
        response.status_code = 200;
        return response
    
    ## 1) put_zen method of updating client's "Modified Notes"
    responses = [] # Successful commit of note.
    updateResponses = [] # Conflicting notes with new content!
    payload = JSONDecoder().decode(request.raw_post_data)
    userNotes = _filter_dupes(request_user.note_owner.all())
    
    #print 'Process modified notes'
    for datum in payload['modifiedNotes']:
        form = NoteForm(datum)
        form.data['owner'] = request_user.id;
        matching_notes = [u for u in userNotes if u.jid==form.data['jid']]
        assert len(matching_notes) in [0,1], "Got two, which is fail %d " % form.data['jid']
        #print '# matching notes:', len(matching_notes)
        if len(matching_notes) == 0: ## Save new note
            if form.is_valid() :
                #print "No conflict! Save note!"
                new_model = form.save()
                responses.append({
                        "jid": form.data['jid'],
                        "version": form.data['version'],
                        "status": 201})
                logevent(request, 'Note.create', 200, form.data['jid'])
            else:
                logevent(request,'Note.create', 400, form.errors)
                responses.append({"jid": form.data['jid'], "status": 400})
        else:
            ## UPDATE an existing note: check if the client version needs updating
            conflictNote = matching_notes[0]
            #print "conflictNote/form Ver: ", conflictNote.version, form.data['version']
            if (conflictNote.version > form.data['version']):
                # Server's version of note is conflicting with client's version, merge!
                if form.is_valid():
                    #print "Server is more up to date:", conflictNote.jid
                    for key in Note.update_fields: ## key={contents,created,deleted,edited}
                        if key == "contents":
                            newContent = ("Two versions of this note:" +
                                          "\nSubmitted Copy:\n%s\n\nServer Copy:\n%s"
                                          % (form.data[key],conflictNote.contents))
                            conflictNote.__setattr__(key, newContent)
                        else:
                            conflictNote.__setattr__(key, form.data[key])
                    newVersion = max(conflictNote.version,
                                     form.data['version']) + 1
                    conflictNote.version = newVersion
                    newEdited = max(conflictNote.edited,
                                    form.data['edited'])
                    conflictNote.edited = newEdited
                    ## Saved note will be MOST-up-to-date, ie:(max(both versions)+1)
                    conflictNote.save()
                    updateResponses.append({"jid": form.data['jid'],
                                            "version": newVersion,
                                            "edited": newEdited,
                                            "contents": newContent,
                                            "status": 201})
                    continue
                continue            
            # If the data contains no errors,
            elif form.is_valid(): # No version conflict, update server version.
                #print "Updating server's copy"
                for key in Note.update_fields:
                    if key in ['contents', 'created', 'deleted', 'edited']:
                        conflictNote.__setattr__(key, form.data[key])
                        pass
                    pass
                newVersion = form.data['version'] + 1
                conflictNote.version = newVersion
                conflictNote.save()
                responses.append({"jid": form.data['jid'],
                                  "version": newVersion,
                                  "status": 201})
            else:
                responses.append({"jid": form.data['jid'], "status": 400})
                logevent(request, 'Note.create', 400, form.errors)
                pass
            pass
        pass


    ##2) Figure out which of Client's unmodified notes has been updated on server
    updateFinal = getUpdatedNotes(payload['unmodifiedNotes'].items(), userNotes)
    

    #print 'process notes only known to server'
    ## 3) Return notes only server knows about!
    clientJIDs = map(lambda x:int(x['jid']), payload['modifiedNotes'])
    clientJIDs.extend(map(lambda x:int(x), payload['unmodifiedNotes'].keys()))
    serverNotes = [u for u in userNotes if u.deleted==0 and not u.jid in clientJIDs]
    
    serverNotes = sort_user_for_notes(request_user, serverNotes)
    
    ndicts = [ extract_zen_notes_data(note) for note in serverNotes ]

    ndicts.reverse()

    servNotes = [] # New notes server has & client doesn't.
    for note in ndicts:
        servNotes.append({
                "jid": note['jid'],
                "version": note['version'],
                "contents": note['noteText'],
                "deleted": note['deleted'],
                "created": str(note['created']),
                "edited": str(note['edited']),
                "modified": 0})
        ## Add meta field here!
        pass


    
    #print 'Add magical note!'
    magicNote = {}
    ## JID is a number field...
    magicalNote = [u for u in userNotes if u.jid == -1]
    #print 'magical note:', magicalNote
    if len(magicalNote) > 0: # magical note found
        #print 'magical note found!'
        magicalNote = magicalNote[0]
        magicNote = {
            'jid':  int(magicalNote.jid),
            'version': magicalNote.version,
            'created': int(magicalNote.created),
            'edited': int(magicalNote.edited),
            'deleted': magicalNote.deleted,
            'contents': magicalNote.contents,
            'modified': 0
            }
        pass

    #magicNote = checkMagicUpdate(clientMagic, serverMagic)

    ## Return Response!
    response = HttpResponse(
        JSONEncoder().encode({
                "committed": responses,
                "update": updateResponses,
                "updateFinal": updateFinal,
                "unknownNotes": servNotes,
                "magicNote": magicNote}),
        "text/json")
    
    response.status_code = 200;
    return response


def checkMagicUpdate(clientMagic, serverMagic):
    """Check if note jid=-1 has been updated"""

    
def post_json_chrome_logs(request):
    """
    Record Chrome usage logs, return timestamp of last log recorded.
    """
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'post_json_chrome_logs POST',
                 401, jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({
            'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401
        return response

    payload = JSONDecoder().decode(request.raw_post_data)
    logs = payload
    timestamp = 0
    for log in logs:
        # Save each log, keep track of latest log's timestamp.
        # keys: time, action, noteid (>0 or -10), info (JSON string)
        # ext only: tabid (chrome ext tab), url (of focused tab)
        entry = ChromeLog();
        entry.owner = request_user;
        entry.when = log['time'];
        timestamp = max(entry.when, timestamp)
        entry.action = log['action'];
        entry.noteid = log.get("noteid",None);
        entry.info = log.get("info",None);
        entry.url = log.get("url",None);
        entry.tabid = log.get("tabid",None); ## added in new rev
        entry.save();

    ## Return Response!
    response = HttpResponse(
        JSONEncoder().encode({
            "lastTimeRecorded": timestamp,
            }), "text/json")
    response.status_code = 200;
    return response
