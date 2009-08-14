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
from django_restapi.authentication import basicauth_get_user 
from django_restapi.resource import Resource
from django_restapi.model_resource import InvalidModelData
from jv3.models import Note
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, ServerLog
import jv3.models
import jv3.study.emails as studytemplates
import time
import datetime
import random
import urllib
import sys
from os import listdir
from decimal import Decimal        

current_time_decimal = lambda : int(time.time()*1000);

def logevent(request,action,result=None,info=None,changepasswordrequest=None,registration=None):
    event = ServerLog()
    event.action = action
    ##event.result = repr(result)
    event.info = repr(result) + "/" + repr(info)
    event.when = int(time.time()*1000);
    event.url = request.get_full_path()
    event.host = request.get_host()
    user = basicauth_get_user(request);
    if user:  event.user = user
    event.changepasswordrequest = changepasswordrequest
    event.registration = registration
    event.save()
    return event

def gen_cookie(cookiesize=25):
    randchar = lambda : chr(ord('a')+random.randint(0,25))
    return ''.join([ randchar() for i in range(cookiesize) ])                

def makeChangePasswordRequest(username):
    cpr = ChangePasswordRequest()
    cpr.when = int(time.time()*1000);
    cpr.username = username
    cpr.cookie = gen_cookie()
    cpr.save();
    return cpr        

def nonblank(s):
    return (s != None) and (type(s) == str or type(s) == unicode) and len(s.strip()) > 0


def gen_confirm_newuser_email_body(userreg):
    url = "%s/jv3/confirmuser?cookie=%s" % (settings.SERVER_URL,userreg.cookie)
    return  """
    Hi!

    You or someone tried to register for listit the note-taking tool listit
    using your the email address %s.


    If you are that person, click here to get started!
    
    %s

    Thanks,

    the Listit Team at MIT CSAIL.
    http://groups.csail.mit.edu/haystack/listit

    """ % (userreg.email, url);

## not a view
def gen_confirm_change_password_email(userreg):
    ## userreg is a changepasswordrequest not a user registration!
    url = "%s/jv3/changepasswordconfirm?cookie=%s" % (settings.SERVER_URL,userreg.cookie)
    return  """
    Hello %s,

    You or someone requested to have your list.it password changed.

    If you are that person and wish to change your password, please click the link below.
    
    %s

    Thanks,

    the Listit Team at MIT CSAIL.
    """ % (userreg.username,url);
             
def get_most_recent(act):
    if act == None or len(act) == 0:
        return None
    return act.order_by("-when")[0];    
    # def comp(x,y):
    #         if x.when >= y.when:
    #             return x;
    #         return y;
    # return reduce(comp,act);        

def decimal_time_to_str(msecs):
    return time.ctime(float(msecs)/1000.0)

def get_user_by_email(email):
    matches = authmodels.User.objects.filter(email__iexact=email)
    if len(matches) > 0:
        return matches[0]
    return None

def _authenticate_user(emailaddr,password):
    try:
        user = get_user_by_email(emailaddr)
        if user and user.check_password(password):
            ## print "User authenticated : " + user.email
            return user;
    except authmodels.User.DoesNotExist:
        pass
    return None        

def basicauth_get_user_by_emailaddr(request):
    decoded = basicauth_decode_email_password(request)
    if decoded is not None and len(decoded) == 2 and len(decoded[0]) > 0 and len(decoded[1]) > 0:
        return _authenticate_user(decoded[0],decoded[1])
    return None

def basicauth_decode_email_password(request):
    """
    If we use this, then we do not have to rely on session authentication 
    """
    ## it's either in the META or the GET
    try:
        authblob = request.META.get('HTTP_AUTHORIZATION', None)
        if authblob is None:
            auth_get = request.GET.get("HTTP_AUTHORIZATION",None)
            authblob = urllib.unquote(auth_get) 
        (authmeth, auth) = authblob.split(' ', 1)
        assert authmeth.strip().lower() == 'basic', "auth token 1 must be basic %s " % authmeth.lower()
        auth = auth.strip().decode('base64')
        emailaddr, password = auth.split(':', 1)        
        return (emailaddr,password)        
    except:
        print sys.exc_info();
    return None        

def decode_emailaddr(request):
    """
    If we use this, then we do not have to rely on session authentication 
    """
    ## it's either in the META or the GET
    decoded = basicauth_decode_email_password(request)
    if decoded is not None and len(decoded) == 2:
        return decoded[0]
    return None

def json_response(dict_obj):
    return HttpResponse(JSONEncoder().encode(dict_obj), "text/json")

USERNAME_MAXCHARS = 30

def make_username(email):
    proposed = email[:USERNAME_MAXCHARS]
    while len(authmodels.User.objects.filter(username__iexact=proposed)) > 0:
        proposed = email[:(USERNAME_MAXCHARS-10)]+gen_cookie(10)
    return proposed

def get_newest_registration_for_user_by_email(email):
    return get_most_recent(UserRegistration.objects.filter(email=email))

def get_consenting_users_old(userset=None,newerthan=time.mktime(datetime.date(2008,9,1).timetuple())*1000):
    ## gets users who have in their most _recent_ consent agreed to couhes
    if userset == None: userset = authmodels.User.objects.all()
    return [u for u in userset if get_newest_registration_for_user_by_email(u.email) and
            get_newest_registration_for_user_by_email(u.email).couhes and
            (newerthan is None or float(get_newest_registration_for_user_by_email(u.email).when) > newerthan)]

study_2_point = 1249099200000 ## 1249099200000 = august 1 2009
def is_consenting_study1(user):
    ## accurate.
    consents=UserRegistration.objects.filter(email=user.email).order_by("-when")
    if consents.count() > 0:
        last_consent = consents[0]
        return last_consent.couhes and last_consent.when < study_2_point
    return False

def is_consenting_study2(user):
    consents=UserRegistration.objects.filter(email=user.email).order_by("-when")
    if consents.count() > 0:
        last_consent = consents[0]
        return last_consent.couhes and last_consent.when > study_2_point
    return False

def set_consenting(user,is_consenting):
    ## clones a userreg
    regs = UserRegistration.objects.filter(email=user.email).order_by("-when")
    if regs.count() == 0:
        make_fake_reg_for_admin_user(user.email,False)
        regs = UserRegistration.objects.filter(email=user.email).order_by("-when")
        
    clone = regs[0].clone()
    
    clone.when = current_time_decimal()
    clone.couhes = is_consenting
    clone.save()
    print "Saving clone %s %s %s %s" % (repr(clone.id),repr(clone.couhes),repr(clone.email),repr(clone.when))

def get_consenting_users(userset=None,newerthan=long(time.mktime(datetime.date(2008,9,1).timetuple())*1000)):
    ## gets users who have in their most _recent_ consent agreed to couhes
    if newerthan is None: newerthan = 0
    # this could be done more easily if we had group_by
    # select pk,max(when),email where couhes="true" from UserRegistration group by email
    print "%s %ld" % (type(newerthan),newerthan)
    newerthan = Decimal("%ld" % newerthan)
    print newerthan
    # UserRegistration.objects.extra(select={'unique_latest': 'select id,max(when),email,couhes where couhes="true" from jv3_userregistration group by email'});

    if userset == None:
        consented_at_some_time = list(set([ro.email for ro in UserRegistration.objects.filter(couhes=True,when__gt=newerthan)]))
    else:
        emails = [u.email for u in userset]
        consented_at_some_time = list(set([ro.email for ro in UserRegistration.objects.filter(couhes=True,email__in=emails,when__gt=newerthan)]))
    
    ## prune this set for users that didn't consent their second time and for those not in userset
    emails = [email for email in consented_at_some_time if UserRegistration.objects.filter(email=email).order_by("-when")[0].couhes]
    #return (authmodels.User.objects.filter(email__in=consented_at_some_time), authmodels.User.objects.filter(email__in=emails))
    return authmodels.User.objects.filter(email__in=emails)

def get_emails_of_users(users):
    return [u.email for u in users]

def get_consenting_users_emails(userset=None):
    return get_emails_of_users(get_consenting_users(userset=userset))

def email_users(userset,subject,body):
    for u in userset:
        reg = get_newest_registration_for_user_by_email(u.email)
        if reg == None:
            print "No registration found for user %s. Skipping" % repr(u.email)
            continue
        userparams = {'email':u.email,'server_url':settings.SERVER_URL,'cookie':reg.cookie,'first_name':reg.first_name, 'last_name':reg.last_name}
        send_mail(subject % userparams, body % userparams, 'listit@csail.mit.edu', (u.email,'listit@csail.mit.edu'), fail_silently=False)

def find_misconfigured_consenting_users():
    u = get_consenting_users()
    return [ u for u in u if len(ActivityLog.objects.filter(owner=u)) == 0]
    
def find_properly_configured_consenting_users():
    u = get_consenting_users()
    return [ u for u in u if len(ActivityLog.objects.filter(owner=u)) > 0]
    
def find_even_id_consenting_users():
    u = get_consenting_users()
    return [ u for u in u if (u.id % 2 == 0)]
    
def find_odd_id_consenting_users():
    u = get_consenting_users()
    return [ u for u in u if (u.id % 2 == 1)]
    
def get_note_by_email_and_jid(email,jid):
    u = authmodels.User.objects.filter(email=email)
    if len(u) == 0:
        print "no such user %s " % email
        return None
    n = jv3.models.Note.objects.filter(jid=jid,owner=u[0])
    if len(n) == 0:
        return None
    return n[0]

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

def get_user_by_email(email):
    hits = authmodels.User.objects.filter(email=email)
    if len(hits) > 0:
        return hits[0]
    return None

def actlogfix(dirname,server):
    results = []
    for uemail in listdir(dirname):
        filename = "%s.plum.store.sqlite" % (uemail)
        email = uemail.lower()
        if not get_user_by_email(email): continue;
        password = get_newest_registration_for_user_by_email(email).password
        results.append('_sync_uploadAllActLog("%s","%s","%s","%s")' % (server,filename, email, password))
    return "\n".join(results)


def make_fake_reg_for_admin_user(email,couhes):
    if UserRegistration.objects.filter(email=email).count() > 0:
        return    
    user = authmodels.User.objects.filter(email=email)[0]    
    ureg = UserRegistration();
    ureg.when = current_time_decimal();
    ureg.email = user.email;
    ureg.password = user.password;  ## WARNING this is a hashed password

    ## couhes handling: couhes requires first & last name 
    ureg.couhes = couhes

    ## print "user couhes is %s " % repr(type(user.couhes))
    ureg.cookie = gen_cookie();
    ureg.save();
    
