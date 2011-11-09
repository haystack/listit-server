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
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, BugReport, ServerLog, CachedActivityLogStats
from jv3.utils import gen_cookie, makeChangePasswordRequest, nonblank, get_most_recent, gen_confirm_newuser_email_body, gen_confirm_change_password_email, logevent, current_time_decimal, basicauth_get_user_by_emailaddr, make_username, get_user_by_email, is_consenting_study1, is_consenting_study2, json_response, set_consenting
from django.template.loader import get_template
import sys,string,time,logging
import tempfile,os
from decimal import Decimal
from jv3.views import *

######################
##  Redaction Code  ##
######################

def convertWordToSymbols(privWord):
    ## Convert private word into public word
    pubWordList = list(privWord)
    for i, char in enumerate(pubWordList):
        if char in string.ascii_lowercase:
            pubWordList[i] = 'x'
        elif char in string.ascii_uppercase:
            pubWordList[i] = 'X'
        elif char in string.digits:
            pubWordList[i] = '9'
        else:
            pubWordList[i] = "*"
    return ''.join(pubWordList)

def getWordMap(request_user, rType, privWord):
    match = WordMap.objects.filter(owner=request_user,wordType=rType, privWord=privWord)
    if len(match) == 1:
        return (match[0], match[0].pubWord)
    elif len(match) == 0:
        return False
    elif len(match) > 1:
        ## This should never happen, but default to first WordMap
        return (match[0], match[0].pubWord)

## Adds word of given type to WordMap, returns created WordMapand the repWord chosen
def createWordMap(request_user, rType, privWord):
    pubWord = convertWordToSymbols(privWord)
    wMap = WordMap(owner=request_user, wordType=rType, privWord=privWord, pubWord=pubWord)
    wMap.save()
    return (wMap, pubWord)

## Use this when server and client disagree over length of word being redacted
## IE: Chinese symbols, use length server sends out (1 per symbol)
## not the 3 per symbol the client returns...
def createSpecialWordMap(request_user, rType, privWord, wordLength):
    pubWord = '^'*wordLength
    wMap = WordMap(owner=request_user, wordType=rType, privWord=privWord, pubWord=pubWord)
    wMap.save()
    return (wMap, pubWord)

def get_redact_notes(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401
        return response
    
    ## Filter out notes that have already been redacted
    notes = Note.objects.filter(owner=request_user).order_by("-created").exclude(jid=-1).exclude(contents="")
    numNotes = len(notes)
    userRedactedNotes = RedactedNote.objects.filter(owner=request_user)
    
    for redactedNote in userRedactedNotes:
        notes = notes.exclude(version=redactedNote.version, jid=redactedNote.jid)
        pass
    numNotesLeft = len(notes)
    ndicts = [ extract_zen_notes_data(note) for note in notes ]
    allNotes = []
    for note in ndicts:
        allNotes.append(
            {"jid":note['jid'],"version":note['version'], "contents":note['noteText'],
             "deleted":note['deleted'], "created":str(note['created']),
             "edited":str(note['edited']) })
    resultMap = {
        'markAsRemoved' : {},
        'markAsName'    : {},
        'markAsPassword': {},
        'markAsPhone'   : {}}
    redactedWordArray = WordMap.objects.filter(owner=request_user)
    for wMap in redactedWordArray:
        if wMap.wordType in resultMap:
            resultMap[wMap.wordType][wMap.privWord] = True
        pass

    
    userMeta = {
        'userPoints': "0",
        'totalNotes': str(numNotes),
        'numNotesLeft': str(numNotesLeft)}
    response = HttpResponse(JSONEncoder().encode({'notes':allNotes, 'wordMapIndices':resultMap, 'userMeta':userMeta}), "text/json")
    response.status_code = 200
    return response


def post_redacted_note(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode(
            {'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401
        return response
    for datum in JSONDecoder().decode(request.raw_post_data):    
        ver = datum['version']
        noteID = datum['id']
        matchingNotes = RedactedNote.objects.filter(jid=noteID, version=ver)
        for mNote in matchingNotes:
            del_wordmeta_for_note(mNote)
            mNote.delete()
            pass
        rNote = RedactedNote()
        rNote.owner = request_user
        rNote.nCreated = datum['origCreated']
        rNote.nEdited  = datum['origEdited']
        rNote.nDeleted = datum['origDeleted']
        rNote.created = datum['created']
        rNote.jid = datum['id']
        rNote.version = datum['version']
        rNote.noteType = datum['noteType']
        sCharIndices = datum['sCharIndices'] ## Tuples: (char index, word length)
        noteText = datum['text']
        noteCharList = list(noteText)
        wordMapIndicesStore = [] ## [word index, WordMap(instance)] to make WordMeta 
        sCharIndices.sort(lambda x,y:cmp(y[2],x[2])) ## Sort redacted indices in reverse order
        ## Walk thru note text, changing redacted text for public xX9* version
        for rIndex, rLen, sIndex, sLen in sCharIndices:
            ## Ex: chinese symbol Z from server seen on client as 3 utf-8 chars: abc
            ## String "ZZ", with 2nd one redacted
            ## rIndex = 4 = start index of redacted text in string
            ## rLen   = 3 = length of word as seen by redact site (utf-8)
            ## sIndex = 1 = start index of redacted text in original encoding (utf-16?)
            ## sLen   = 1 = length of redacted string as sent from server
            rType = "markAsRemoved"
            privWord = ''.join(noteCharList[rIndex:rIndex+rLen])
            matchWordMap = getWordMap(request_user, rType, privWord)
            if matchWordMap is False:   ## Create a new WordMap
                if rLen != sLen:
                    ## Word server sent out and word recieved are encoded to different lengths
                    wordMapIDRep, repWord = createSpecialWordMap(request_user, rType, privWord, sLen)
                else:
                    ## Create WordMap that stores original 
                    wordMapIDRep, repWord = createWordMap(request_user, rType, privWord)
                wordMapIndicesStore.append([sIndex, sLen, wordMapIDRep])
                noteCharList[rIndex:rIndex+rLen] = list(repWord)
            else:
                ## Found a WordMap already describing this word
                wordMapIndicesStore.append([sIndex, sLen, matchWordMap[0]])
                noteCharList[rIndex:rIndex+rLen] = list(matchWordMap[1])
            pass
        rNote.contents = ''.join(noteCharList)
        rNote.save()
        ## Create all the WordMeta using pairs from wordMapIndicesStore
        for data in wordMapIndicesStore:
            wMeta = WordMeta(owner=request_user, rNote=rNote, index=data[0], length=data[1], wordMap=data[2])
            wMeta.save()
            pass
        pass
    response = HttpResponse("No Errors?", "text/json")
    response.status_code = 200
    return response


## Uses skippedNote model to remember never to pester user to redact a note again.
##def post_skipped_redacted_note(request):
##    request_user = basicauth_get_user_by_emailaddr(request)
##    if not request_user:
##        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
##        response = HttpResponse(JSONEncoder().encode(
##            {'autherror':"Incorrect user/password combination"}), "text/json")
##        response.status_code = 401
##        return response
##
##    for datum in JSONDecoder().decode(request.raw_post_data):
##        ver = datum['version']
##        noteID = datum['id']
##        matchingNotes = RedactedNote.objects.filter(jid=noteID, version=ver)
##        ##matchingSkips = RedactedSkip.objects.filter(jid=noteID, version=ver)
##        for mNote in matchingNotes:
##            del_wordmeta_for_note(mNote)
##            mNote.delete()
##        for sNote in matchingSkips:
##            sNote.delete()
##            pass
##        skippedNote = RedactedSkip()
##        skippedNote.owner   = request_user
##        skippedNote.jid     = datum['id']
##        skippedNote.version = datum['version']
##        skippedNote.save()
##        pass
##    response = HttpResponse("No Errors?", "text/json")
##    response.status_code = 200
##    return response

## Deletes WordMeta objects associated with given note.
def del_wordmeta_for_note(n):
    wMetas = WordMeta.objects.filter(rNote=n)
    for meta in wMetas:
        meta.delete()


## Misc View
import csv, codecs, cStringIO

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def misc_view(request):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=redacted_notes.csv'

    rWriter = UnicodeWriter(response)
    rWriter.writerow(['category', 'contents'])
    for note in RedactedNote.objects.all().order_by('created'):
        rWriter.writerow([note.noteType, note.contents])
    
    ##response.status_code = 200
    return response

def misc_viewer(request):
    css = """
    html, body {
      padding: 0px;
      margin:0px;
    }
    #main {
      margin:50px auto;
      width:80%;
      min-width:500px;
      border:1px solid #000;
      border-radius:4px;
      -moz-border-radius: 20px;
      -webkit-border-radius: 20px;
      -khtml-border-radius: 20px;
      border-radius: 20px;
      padding:20px;
    }
    .cat {
        margin-top:10px;
        background-color:#AAF;
        -webkit-radius:
    }
    .text {
        background-color:#DDF;
    }
    """
    body = []
    notes = RedactedNote.objects.all().order_by('created')
    notes.reverse()
    for note in notes:
        body.append("""<div class='note'>
            <div class='cat'>%s</div>
            <div class='text'>%s</div>
        </div>"""%(note.noteType, note.contents))
    
    html = """<html>
    <head><title>MISC Gallery</title>
    <style type='text/css'>%s</style></head>
    <body>
    <div id="main">
    %s
    </div>

    </body></html>"""%(css ,''.join(body))
    
    response = HttpResponse(html)
    #response['Content-Disposition'] = 'attachment; filename=redacted_notes.csv'

    #rWriter = UnicodeWriter(response)
    #rWriter.writerow(['category', 'contents'])
    #for note in RedactedNote.objects.all().order_by('created'):
    #    rWriter.writerow([note.noteType, note.contents])
    
    ##response.status_code = 200
    return response

def misc_json(request):
    allNotes = []
    notes = RedactedNote.objects.all().order_by('created')
    notes.reverse()
    for note in notes:
        allNotes.append({"type":"Note", "label":note.noteType, "contents":note.contents})
        pass
    print 1
    types = {"Note":{'pluralLabel': "Notes"} }
    print 2
    response = HttpResponse(JSONEncoder().encode({'types':types, 'items':allNotes}), "text/json")
    response.status_code = 200
    return response
    


