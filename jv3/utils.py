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
import time
import random

current_time_decimal = lambda : int(time.time()*1000);

def logevent(request,action,result=None,info=None,changepasswordrequest=None,registration=None):
    event = ServerLog()
    event.action = action
    event.result = repr(result)
    event.info = repr(info)
    event.when = int(time.time()*1000);
    event.url = request.get_full_path()
    event.host = request.get_host()
    user = basicauth_get_user(request);
    if user:  event.user = user
    event.changepasswordrequest = changepasswordrequest
    event.registration = registration
    event.save()

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

    You or someone tried to register for Listit (http://projects.csail.mit.edu/jourknow/listit)
    using your the email address %s.

    If you are that person, click here to get started!
    
    %s

    Thanks,

    the Listit Team at MIT CSAIL.
    """ % (userreg.email, url);

## not a view
def gen_confirm_change_password_email(userreg):
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
    def comp(x,y):
        if x.when >= y.when:
            return x;
        return y;
    return reduce(comp,act);        

def decimal_time_to_str(msecs):
    return time.ctime(float(msecs)/1000.0)

def basicauth_get_user_by_emailaddr(request):
    """
    If we use this, then we do not have to rely on session authentication 
    """
    if not request.META.has_key('HTTP_AUTHORIZATION'): return False
    (authmeth, auth) = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
    if authmeth.lower() != 'basic':
        return False
    auth = auth.strip().decode('base64')
    emailaddr, password = auth.split(':', 1)
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(email=emailaddr)
        if user.check_password(password):
            return user;
    except User.DoesNotExist:
        pass
    return False



USERNAME_MAXCHARS = 30

def make_username(email):
    proposed = email[:USERNAME_MAXCHARS]
    while len(authmodels.User.objects.filter(username=proposed)) > 0:
        proposed = email[:(USERNAME_MAXCHARS-10)]+gen_cookie(10)
    return proposed
    
