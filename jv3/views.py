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

logging.basicConfig(filename=os.sep.join([tempfile.gettempdir(),"listit-view-error-"+repr(int(time.time()))]),level=logging.DEBUG)

# Create your views here.
class SPOCollection(Resource):
    def read(self, request):
        import jv3.models
        spos = jv3.models.SPO.objects.all()
        context = {'spos':spos}
        return render_to_response('jv3/spos.html', context)

class NoteCollection(Collection):

    ## read is covered by the superclass
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        request_user = basicauth_get_user_by_emailaddr(request);        
        if not request_user:
            logevent(request,'Note.read',401,{"requesting user:":jv3.utils.decode_emailaddr(request)})
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        qs_user = None
        if request.GET.has_key("jid"):
            ## user has asked for only one note, yo.
            qs_user = Note.objects.filter(owner=request_user,jid=int(request.GET["jid"]))
        else:
            qs_user = Note.objects.filter(owner=request_user)
            
        logevent(request,'Note.read',200)
        return self.responder.list(request, qs_user)

    def create(self,request):
        ## THIS CODE IS DEPRECATED // the SLOW method. IF YOU MAKE ANY CHANGES HERE
        ## MAKE SURE THE CHANGES ARE REFLECTED in note_update_batch below
        
        # MERGED create and update method for server, so that we don't have to do a PUT
        #  forms.form_for_model(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        form = NoteForm(data)

        # get user being authenticated
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'Note.create POST',401, jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        form.data['owner'] = request_user.id;                 ## clobber this whole-sale from authenticating user
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        
        if len(matching_notes) == 0:
            ## CREATE a new note
            # If the data contains no errors, save the model,
            if form.is_valid() :
                new_model = form.save()
                model_entry = self.entry_class(self, new_model)
                response = model_entry.read(request)
                response.status_code = 201
                ## response['Location'] ## = model_entry.get_url()
                logevent(request,'Note.create',200,form.data['jid'])
                return response
            ## something didn't pass form validation
            logevent(request,'Note.create',400,form.errors)
            ##print "CREATE form errors %s " % repr(form.errors)
            return self.responder.error(request, 400, form.errors);
        else:
            ## UPDATE an existing note
            ## check if the client version needs updating
            if len(matching_notes) > 1:
                print "# of Matching Notes : %d " % len(matching_notes)

            if (matching_notes[0].version > form.data['version']):
                errormsg = "Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  % (form.data["jid"],matching_notes[0].version,form.data["version"])
                print "NOT UPDATED error -- server: %d, YOU %d " % (matching_notes[0].version,form.data['version'])
                return self.responder.error(request, 400, ErrorDict({"jid":errormsg}))
            
            # If the data contains no errors, migrate the changes over to
            # the version of the note in the db, increment the version number
            # and announce success
            if form.is_valid() :
                for key in Note.update_fields:
                    matching_notes[0].__setattr__(key,form.data[key])
                # increment version number
                matching_notes[0].version = form.data['version'] + 1 ## matching_notes[0].version + 1;
                # save!
                # print "SAVING %s, is it deleted? %s " % (repr(matching_notes[0]),repr(matching_notes[0].deleted))
                matching_notes[0].save()
                response = self.read(request)
                response.status_code = 200
                ## this BREAKS with 1.0 ## response['Location'] = self.get_url()
                # announce success
                logevent(request,'Note.update',200,form.data['jid'])
                return response
            # Otherwise return a 400 Bad Request error.
            logevent(request,'Note.create',400,form.errors)
            ## debug
            formerrors = form.errors
            print "UPDATE form errors %s " % repr(form.errors)
            ## end debug
            return self.responder.error(request, 400, form.errors);
        pass

    def update(self,request):
        assert False, "Internal error: You are using an outdated client."

    def delete(self, request):
        """
        Deletes the Note in the model with the particular jid of the note passed in.  Only the jid matters;
        all other fields are ignored.

        If a note with such a JID does not exist, return 404.
        Called with HTTP DELETE
        """
        #ResourceForm = forms.form_for_model(Note, form=self.form_class)
        data = self.receiver.get_put_data(request)
        #form = ResourceForm(data)
        form = NoteForm(data)
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'Note.delete',401, jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))
        
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        
        if len(matching_notes) == 0:
            return self.responder.error(request, 404, ErrorDict({"jid":"Note with jid %d not found"  % form.data["jid"]}));

        for to_die in matching_notes:
            to_die.delete()

        return HttpResponse(_("Object successfully deleted."), self.responder.mimetype)
    

def notes_post_multi(request):
    ## mirrored from NoteCollections.create upstairs but updated to handle
    ## new batch sync protocol from listit 0.4.0 and newer.
    
    ## changes to protocol:
    ## call it with a list of notes { [ {id: 123981231, text:"i love you"..} ...  ] )
    ## returns a success with a list { committed: [{ success: <code>, jid: <id> }] ... } unless something really bad happened

    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401;
        return response
    
    responses = []
    ## print "raw post data: %s " % repr(request.raw_post_data)
    if not request.raw_post_data:
        response = HttpResponse(JSONEncoder().encode({'committed':[]}), "text/json")
        response.status_code = 200;
        return response

    for datum in JSONDecoder().decode(request.raw_post_data):
        ## print "datum : %s "% repr(datum)
        ## print datum
        form = NoteForm(datum)
        form.data['owner'] = request_user.id;                 ## clobber this whole-sale from authenticating user
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        if len(matching_notes) == 0:
            ## CREATE a new note
            # If the data contains no errors, save the model,
            if form.is_valid() :
                new_model = form.save()
                responses.append({"jid":form.data['jid'],"status":201})
                logevent(request,'Note.create',200,form.data['jid'])        
                continue
            ## something didn't pass form validation
            logevent(request,'Note.create',400,form.errors)
            responses.append({"jid":form.data['jid'],"status":400})
            continue
        else:
            # print "UPDATE an existing note"
            ## check if the client version needs updating
            if len(matching_notes) > 1:
                print "# of Matching Notes : %d " % len(matching_notes)
            if (matching_notes[0].version > form.data['version']):
                responses.append({"jid":form.data['jid'],"status":400})
                continue            
            # If the data contains no errors, migrate the changes over to
            # the version of the note in the db, increment the version number
            # and announce success
            if form.is_valid() :
                for key in Note.update_fields:
                    matching_notes[0].__setattr__(key,form.data[key])
                # increment version number
                matching_notes[0].version = form.data['version'] + 1 ## matching_notes[0].version + 1;
                # save!
                # print "SAVING %s, is it deleted? %s " % (repr(matching_notes[0]),repr(matching_notes[0].deleted))
                matching_notes[0].save()
                responses.append({"jid":form.data['jid'],"status":201})
            else:                    
                # Otherwise return a 400 Bad Request error.
                responses.append({"jid":form.data['jid'],"status":400})
                logevent(request,'Note.create',400,form.errors)
                pass
        pass
    ##print responses
    response = HttpResponse(JSONEncoder().encode({'committed':responses}), "text/json")
    response.status_code = 200;
    return response

    
# no longer necessary since we are no longer using session auth--
# 
# from django.contrib.auth import authenticate, login
# from django.utils.translation.trans_null import _
# def login_view(request):
#     username = request.POST['username']
#     password = request.POST['password']
#     user = authenticate(username=username, password=password)
#     if user is not None:
#         if user.is_active:
#             login(request, user)
#             return HttpResponse(_("Login successful."));
#             # Redirect to a success page.
#         else:
#             # Return a 'disabled account' error message
#             return HttpResponse(_("Account disabled."));
#             pass        
#     return HttpResponse(_("Login unsuccessful."));

## a view new user/user management
def userexists(request):
    email = request.GET['email'];
    if get_user_by_email(email) :
        response = HttpResponse("User exists", "text/html");
        response.status_code = 200;
        return response    
    response = HttpResponse("User does not exist", "text/html");
    response.status_code = 404;
    return response

def login(request):
    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        resp = json_response({"code":401,'autherror':"Incorrect user/password combination"})
        resp.status_code = 401;
        return resp
    resp = json_response({"code":200,"study1":is_consenting_study1(request_user),"study2":is_consenting_study2(request_user)})
    resp.status_code = 200;
    print "returning resp %s // %s " % (repr(is_consenting_study1(request_user)),repr(is_consenting_study2(request_user)))
    return resp

def set_consenting_view(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        resp = json_response({"code":401,'autherror':"Incorrect user/password combination"})
        resp.status_code = 401;
        return resp

    value = JSONDecoder().decode(request.raw_post_data)['consenting']
    print "set_consenting %s " % repr(value)
    set_consenting(request_user,value)
    resp = json_response({"code":200})
    resp.status_code = 200;
    return resp


require_account_confirmation = False
joeuser_name = "List.It User"

def _make_user_from_registration(reg):
    ## check to see if already registered
    if get_user_by_email(reg.email):
        user = get_user_by_email(reg.email)
        return user
        
    user = authmodels.User();
    user.username = make_username(reg.email);  ## intentionally a dupe, since we dont have a username. WE MUST be sure not to overflow it (max_chat is default 30)
    user.email = reg.email;
    user.first_name = joeuser_name;
    user.set_password(reg.password);
    user.save();
    
    ## handle couhes reg
    if (reg.couhes):
        ## assert nonblank(reg.first_name) and nonblank(reg.last_name), "Couhes requires non blank first and last names"
        user.first_name = reg.first_name;
        user.last_name = reg.last_name;
        user.save();
        ## now make couhes consetnform
        cc = CouhesConsent()
        cc.owner = user;
        cc.signed_date = reg.when;
        cc.save()

    return user    

def createuser(request):
    ## as of 8.13, we now no longer require email confirmation -- we create users immediately
    ## on signup.
    
    email = request.POST['username'];
    passwd = request.POST['password'];
    
    if get_user_by_email(email) :
        response = HttpResponse("User exists", "text/html");
        response.status_code = 405;
        logevent(request,'createuser',205,email)
        return response

    user_reg = UserRegistration();
    user_reg.when = current_time_decimal();
    user_reg.email = email;
    user_reg.password = passwd;  ## this is unfortunate.
    
    ## couhes handling: couhes requires first & last name 
    user_reg.couhes = (request.POST['couhes'] == 'true'); ## assume this is boolean
    user_reg.first_name = request.POST.get('firstname',''); 
    user_reg.last_name = request.POST.get('lastname',''); 
    
    ## print "user couhes is %s " % repr(type(user.couhes))
    user_reg.cookie = gen_cookie();
    user_reg.save();

    if require_account_confirmation:
        print "New user registration is %s " % repr(user_reg);
        send_mail('Did you register for Listit?', gen_confirm_newuser_email_body(user_reg) , 'listit@csail.mit.edu', (user_reg.email,), fail_silently=False)
        response = HttpResponse("UserRegistration created successfully", "text/html");    
        response.status_code = 200;
        logevent(request,'createusr',201,user_reg)
        return response

    ## else
    user = _make_user_from_registration(user_reg)
    response = HttpResponse("User created successfully", "text/html");    
    response.status_code = 200;
    logevent(request,'createusr',201,user_reg)
    return response        

def __is_unconfirmed(u):
    return user.first_name == joeuser_name

def confirmuser(request):
    cookie = request.GET['cookie'];
    matching_registrations = UserRegistration.objects.filter(cookie=cookie)
    if len(matching_registrations) > 0:
        newest_registration = get_most_recent(matching_registrations)
        user= _make_user_from_registration(newest_registration)
        user.first_name = newest_registration.first_name
        user.last_name = newest_registration.last_name
        user.save()
        logevent(request,'confirmuser',200,user)
        return render_to_response('jv3/confirmuser.html', {'message': "Okay, thank you for confirming that you are a human, %s.  You can now synchronize with List.it. " % user.email,
                                                           'username':user.email, 'password':newest_registration.password, 'server':settings.SERVER_URL});
    
    response = render_to_response('jv3/confirmuser.html', {'message': "Oops, could not figure out what you are talking about!"});
    response.status_code = 405;
    logevent(request,'confirmuser',405,request)
    return response



## this method was used in an email sent out by initial study long ago --
def reconsent(request):
    email = request.GET['email']
    newest_registration  = get_most_recent(UserRegistration.objects.filter(email__iexact=email))
    if newest_registration:
        logevent(request,'reconsent',200,newest_registration)
        newest_registration.couhes = True
        newest_registration.when = current_time_decimal() ## update time 
        newest_registration.save()
        return render_to_response('jv3/confirmuser.html',
                                  {'message': "Great! Thank you for signing back up for our study. If you would like to set up your client or re-install list it, use the links below. ",
                                   "username":email, 'password':newest_registration.password, 'server':settings.SERVER_URL})
    response = render_to_response('/500.html');
    response.status_code = 500;
    logevent(request,'reconsent',500,request)
    return response
##
                           

def changepassword_request(request): ## GET view, parameter username
    email = request.GET['username'];
    matching_user = get_user_by_email(email)
    if not matching_user:
        response = HttpResponse("Unknown user, did you register previously for List.it under a different email address?", "text/html");    
        response.status_code = 404
        logevent(request,'changepassword_request',404,repr(request))
        return response;    
    req = makeChangePasswordRequest(email)
    send_mail('Confirm List.it change password request', gen_confirm_change_password_email(req) , 'listit@csail.mit.edu', (matching_user.email,), fail_silently=False)
    response = render_to_response('jv3/changepassword_request.html', {'message': "(I just sent email to you at %s)" % matching_user.email})
    logevent(request,'changepassword_request',200,repr((email,req.cookie,)))

    response.status_code = 200

    return response

def changepassword_confirm(request): ## GET view, parameter cookie
    cookie = request.GET['cookie'];
    matching_requests = ChangePasswordRequest.objects.filter(cookie=cookie)
    if len(matching_requests) == 0:
        response = HttpResponse("Sorry, I did not know about your request to change your password.","text/html")
        response.status_code = 405
        logevent(request,'changepassword',404,repr(request))
        return response  
    reqobject = matching_requests[0];
    response = render_to_response('jv3/changepasswordform.html', {'cookie':cookie,'username':reqobject.username})
    logevent(request,'changepassword_confirm',200,reqobject.username)
    return response

def changepassword(request): ## POST view, parameters cookie and password
    cookie = request.POST['cookie'];
    password = request.POST['password'];
    assert cookie != None and len(password) > 0, "Cookie cannot be null"
    assert password != None and len(password) > 0, "Password cannot be null"
    matching_requests = ChangePasswordRequest.objects.filter(cookie=cookie)
    if len(matching_requests) == 0:
        response = HttpResponse("Sorry, I did not know about your request to change your password.","text/html")
        response.status_code = 405;
        logevent(request,'changepassword',405,repr(request))
        return response;
    reqobject = matching_requests[0];
    matching_user = get_user_by_email(reqobject.username)
    if not matching_user:
        response = HttpResponse("Sorry, I did not know about the user you are asking about: %s " % repr(reqobject.username),"text/html")
        response.status_code = 404;
        logevent(request,'changepassword',404,repr(request))
        return response;    
    matching_user.set_password(password)
    matching_user.save()
    reqobject.delete()
    response = render_to_response('jv3/confirmuser.html', {'message': "Your password hs been updated successfully, %s." % matching_user.email})
    logevent(request,'changepassword',200,repr(cookie))
    return response;    

## utilities -- NOT views

## If thing is new:
## 

## note = RedactedNote()
## ... must check
## note.save()

class ActivityLogCollection(Collection):

    def read(self,request):
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.read',401,{"requesting user:":jv3.utils.decode_emailaddr(request)})
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combintion"}))

        clientid = self._get_client(request)
        if (request.GET['type'] == 'get_max_log_id'):
            ## "what is the last thing i sent?"
            try:
                return self._handle_max_log_request(request_user,clientid);
            except:
                print sys.exc_info()
                logging.error(str(sys.exc_info()))
            return HttpResponse(JSONEncoder().encode({'value':0, 'num_logs':0}))
        
        return HttpResponse(JSONEncoder().encode([]), self.responder.mimetype)

    def _handle_max_log_request(self,user,clientid):
        ## return the max id (used by the client to determine which recordsneed to be retrieved.)
        maxdate,count = self._get_max_helper(user,clientid)
        print "  returning ",maxdate,count
        return HttpResponse(JSONEncoder().encode({'value':long(maxdate), 'num_logs':long(count)}))


    @staticmethod
    def _get_cached_activity_log_stats(user,clientid):
        if clientid is not None:
            return CachedActivityLogStats.objects.filter(user=user,client=clientid)
        return CachedActivityLogStats.objects.filter(user=user)

    @staticmethod
    def _get_activity_logs(user,clientid):
        if clientid is not None:
            return ActivityLog.objects.filter(owner=user,client=clientid)
        return ActivityLog.objects.filter(owner=user)    
            
    # uses new caching table awesomeness
    def _get_max_helper(self,user,clientid):
        if self._get_cached_activity_log_stats(user,clientid).count() == 0:
            print "actloghelper nothing cached for",user,clientid,
            user_activity = self._get_activity_logs(user,clientid)
            most_recent_activity = get_most_recent(user_activity)
            # compute manually
            if most_recent_activity:
                maxdate,count = long(most_recent_activity.when),len(user_activity)
                self._set_maxdate_count_for_user(user,clientid,maxdate)
                return maxdate,count
            return 0,0
        print "actloghelper cached ",user,clientid, "!",
        cals = self._get_cached_activity_log_stats(user,clientid).order_by('-count')[0]
        return cals.maxdate,cals.count
    
    def _set_maxdate_count_for_user(self,user,clientid,maxdate):
        tablerecs = self._get_cached_activity_log_stats(user,clientid)
        if tablerecs.count() > 0:
            cal = tablerecs.order_by('-count')[0]
        else:
            cal = CachedActivityLogStats(user=user,client=clientid)
        cal.maxdate = maxdate
        cal.count = self._get_activity_logs(user,clientid).count()
        cal.save()
        pass

    def _get_client(self,request):
        if request.GET.has_key('client'):  return request.GET['client']
        return None
    
    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))
        
        # clientid = self._get_client(request) # this doesn't work, emax
        clientid = None
        maxdate,count = self._get_max_helper(request_user,clientid) # overcount
        committed = [];
        incoming = JSONDecoder().decode(request.raw_post_data)
        print "activity log",request_user," received ",len(incoming)

        dupes = 0
        
        for item in incoming: 
            #print "item is %s " % repr(item)
            try:
                if ActivityLog.objects.filter(owner=request_user,when=item['id'],action=item['type']).count() > 0:
                    # print "actlog skipping ~ "
                    dupes = dupes + 1
                    continue
                entry = ActivityLog();
                entry.owner = request_user;
                entry.when = item['id'];
                entry.action = item['type'];
                entry.noteid = item.get("noteid",None);
                entry.noteText = item.get("noteText",None);
                entry.search = item.get("search",None);
                entry.client = item.get("client",None); ## added in new rev
                clientid = item.get("client")
                entry.save();
                committed.append(long(item['id']));

                maxdate = max(maxdate,long(item['id']))
                
            except StandardError, error:
                print "Error with entry %s item %s " % (repr(error),repr(item))

        print "actlog dupes ", request_user, " ", dupes

        self._set_maxdate_count_for_user(request_user,clientid,maxdate)
        response = HttpResponse(JSONEncoder().encode({'committed':committed}), self.responder.mimetype)
        response.status_code = 200;
        logevent(request,'commitActivityLog',200,repr(committed))
        return response

def submit_bug_report(request):
    username = request.POST['username']
    description = request.POST['description']
    if len(username.strip()) > 0 and len(description.strip()) > 0:
        report = BugReport()
        report.when = current_time_decimal();
        report.username = username
        report.description = description
        report.save()
        return HttpResponse('Thank you for your report.', 'text/html');
    response = HttpResponse('Please provide your username and a description', 'text/html');
    response.status_code = 400
    return response

def get_user_and_registration_from_cookie(cookie,request):
    registration = get_most_recent(UserRegistration.objects.filter(cookie=cookie))
    # user not found?
    if (not registration or len(UserRegistration.objects.filter(cookie=cookie)) == 0):
        return None
    matching_user = get_user_by_email(registration.email)
    if not matching_user:
        return None
    return (matching_user, registration)
    
def get_survey(request):
    # generates a personalized survey based on the contents of survey
    import jv3.study.survey
    cookie = request.GET['cookie']
    (user,registration) = get_user_and_registration_from_cookie( cookie, request )
    
    if not user:
        print "no such user from cookie %s " % request.GET['cookie']
        response = render_to_response('/500.html');
        response.status_code = 500;
        return response
    
    questions = [];
    survey = jv3.study.survey.get_survey_for_user(user)
    
    if not survey:
        print "no survey for user %s " % repr(user)
        response = render_to_response('/404.html');
        response.status_code = 404;
        return response
    
    for q in survey:
        questions.append(q);
        if q.has_key("qid") and len(jv3.models.SurveyQuestion.objects.filter(user=user,qid=q["qid"])) == 0:
            ## allocate a placeholder in the database to store our result
            q_model = jv3.models.SurveyQuestion()
            q_model.qid = q["qid"]
            q_model.user = user
            q_model.response = ""
            q_model.save()               
        elif q.has_key("qid"):            
            for sq in jv3.models.SurveyQuestion.objects.filter(user=user,qid=q["qid"]):
                q['response'] = sq.response
        else:
            ## textual
            pass

    return HttpResponse(get_template("jv3/surveyform.html").render({}) % {'email':user.email,
                                                                          'first_name':registration.first_name,
                                                                          'last_name':registration.last_name,
                                                                          'server':settings.SERVER_URL,
                                                                          'cookie': cookie,
                                                                          'questions': unicode(JSONEncoder().encode(questions)) },"text/html")

def post_survey(request):
    (user,registration) = get_user_and_registration_from_cookie(request.POST['cookie'],request)
    
    if (not user):
        print "no such user registration for cookie %s " % repr(cookie)
        response = render_to_response('/500.html');
        response.status_code = 500;
        return response
    
    ## save result
    for q in JSONDecoder().decode(request.POST['questions']):
        question_model = jv3.models.SurveyQuestion.objects.filter(user=user,qid=q["qid"])
        assert len(question_model) == 1, "Survey questions matching qid %s %d " % (repr(q["qid"]),len(question_model))
        question_model[0].response = q["response"]
        question_model[0].save()

    response = HttpResponse('Successful', 'text/html');
    response.status_code = 200
    return response        

def done_survey(request):
    (user,registration) = get_user_and_registration_from_cookie(request.POST['cookie'],request)
    if (not user):
        print "no such user registration for cookie %s " % repr(cookie)
        response = render_to_response('/500.html');
        response.status_code = 500;
        return response
    
    done = jv3.models.SurveyDoneDeclaration()
    done.user = user
    done.when = current_time_decimal();
    done.save()
    
    response = HttpResponse('Successful', 'text/html');
    response.status_code = 200
    return response        
    


def extract_zen_notes_data(note):
    return {"noteText":note.contents,
            "edited":note.edited,
            "pk":note.id,
            "jid":note.jid,
            "col":80,
            "row":1,
            "version":note.version,
            "deleted": note.deleted,  # ?? "false",
            "created":note.created};


def extract_zen_notes_data_extras(note):
    if (note.contents.find('#hide') != -1):
        archiveState = 'archiveNote'
        startVis = 'none'
    else:
        archiveState = 'regularNote'
        startVis = ''
        
    return {"noteText":note.contents,
            "edited":note.edited,
            "pk":note.id,
            "jid":note.jid,
            "col":80,
            "row":1,
            "version":note.version,
            "deleted":"false",
            "created":note.created,
            "archiveState": archiveState,
            "startVisibility": startVis};

def sort_user_notes(request_user):
    ## Sort and return user's notes
    if Note.objects.filter(owner=request_user,jid="-1").count() > 0:
        ## we want to determine order using magic note
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
    else:
        # sort by creation date ?
        notes = Note.objects.filter(owner=request_user,deleted=False).order_by("-created").exclude(jid=-1)
    return notes
    

def get_zen(request):
    iphone = True
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401 ## removed semi-colon??
        return response
    
    notes = sort_user_notes(request_user)
    
    startIndex = int(request.GET.get("START_INDEX", 0))
    noteLength = len(notes)
    endIndex = int(request.GET.get("END_INDEX", -1))
    if endIndex == -1:
        iphone = False
        endIndex = noteLength

    additionalNotesWaiting = True
    if iphone and (endIndex >= noteLength):
        additionalNotesWaiting = False;
    
    ## make magic happen
    ndicts = [ extract_zen_notes_data_extras(note) for note in notes[startIndex:endIndex] ]
    deltaIndex = endIndex - startIndex

    iconType = request.GET.get("ICON", 'none')
    if iconType == 'X':  ## For zen site
        ##print "Called from /zen/ site"
        htmlblob = "\n".join([ "<div class='note' name='%(archiveState)s' style='display:%(startVisibility)s'><img class='deleteX' src='x.png' alt='Delete' onClick='zenNoteAjax.saveEditedNote(\"%(jid)s\", true)'/> <textarea name='note' id='%(jid)s' edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onFocus='zenNoteView.noteClicked(\"%(jid)s\")' cols='%(col)s' rows='%(row)s' hasFocus='false' hasSelect='false' onBlur='zenNoteView.noteBlur(\"%(jid)s\")' style='overflow:hidden'>%(noteText)s</textarea></div>" % n for n in ndicts ])
    else:                ## For tags site
        ##print "Called from /tags/ site"
        htmlblob = "\n".join([ "<div class='note' name='%(archiveState)s' style='display:%(startVisibility)s'><img class='deleteX' src='arrow-left.png' alt='Delete' onMouseOver='zenNoteView.dispNoteOptions(\"%(jid)s\", true)' onmouseout=\"zenNoteView.noteOptions.startTimer();\"/> <textarea name='note' id='%(jid)s' edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onFocus='zenNoteView.noteClicked(\"%(jid)s\")' cols='%(col)s' rows='%(row)s' hasFocus='false' hasSelect='false' onBlur='zenNoteView.noteBlur(\"%(jid)s\")' style='overflow:hidden'>%(noteText)s</textarea></div>" % n for n in ndicts ])
    
    if iphone and additionalNotesWaiting:
        htmlblob += "\n <button id='requestMore' onClick='zeniPhone.requestMore()'>Get %s more notes</div>" % (deltaIndex)
    elif iphone:
        htmlblob += "\n <button id='requestMore' style='display:none' onClick='zeniPhone.requestMore()'>Get %s more notes</div>" % (deltaIndex)
    response = HttpResponse(htmlblob, 'text/html');
    response.status_code = 200
    return response


def put_zen(request):
    ## copied from notes_post_multi, altered for better edit posting
    ## Purpose: allow notes to be posted, if server has newer version, join texts and return new note
    ##
    ## mirrored from NoteCollections.create upstairs but updated to handle
    ## new batch sync protocol from listit 0.4.0 and newer.
    
    ## changes to protocol:
    ## call it with a list of notes { [ {id: 123981231, text:"i love you"..} ...  ] )
    ## returns a success with a list { committed: [{ success: <code>, jid: <id> }] ... } unless something really bad happened
    
    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401;
        return response

    responses = []
    updateResponses = []
    if not request.raw_post_data:
        response = HttpResponse(JSONEncoder().encode({'committed':[]}), "text/json")
        response.status_code = 200;
        return response
    
    for datum in JSONDecoder().decode(request.raw_post_data):
        form = NoteForm(datum)
        form.data['owner'] = request_user.id;
        ## clobber this whole-sale from authenticating user
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        if len(matching_notes) == 0:
            ## Save new note
            if form.is_valid() :
                new_model = form.save()
                responses.append({"jid":form.data['jid'],"status":201})
                logevent(request,'Note.create',200,form.data['jid'])
                continue
            logevent(request,'Note.create',400,form.errors)
            responses.append({"jid":form.data['jid'],"status":400})
            continue
        else:
            ## UPDATE an existing note: check if the client version needs updating
            if (matching_notes[0].version > form.data['version']):
                if form.is_valid():
                    for key in Note.update_fields: ## key={contents,created,deleted,edited}
                        if key == "contents":
                            newContent = "Two versions of this note:\nSubmitted Copy:\n%s\n\nServer Copy:\n%s" % (form.data[key], matching_notes[0].contents)
                            ##print "Key: %s, Data: %s" % (key, newContent)
                            matching_notes[0].__setattr__(key, newContent)
                        else:
                            ##print "Key: %s, Data: %s" % (key, form.data[key])
                            matching_notes[0].__setattr__(key, form.data[key])
                    newVersion = max(matching_notes[0].version, form.data['version']) + 1
                    ##print newVersion
                    matching_notes[0].version = newVersion ## Saved note is MOST-up-to-date, ie:(max(both versions)+1)
                    matching_notes[0].save()
                    updateResponses.append({"jid":form.data['jid'],"content": newContent, "version": newVersion,"status":201})
                    continue
                continue            
            # If the data contains no errors, migrate the changes over to the version of the note in the db,
            # increment the version number and announce success
            if form.is_valid() :
                ##print "6a: update server note"
                for key in Note.update_fields:
                    matching_notes[0].__setattr__(key,form.data[key])
                matching_notes[0].version = form.data['version'] + 1 
                matching_notes[0].save()
                responses.append({"jid":form.data['jid'],"status":201})
            else:
                responses.append({"jid":form.data['jid'],"status":400})
                logevent(request,'Note.create',400,form.errors)
                
    response = HttpResponse(JSONEncoder().encode({'committed':responses, 'update':updateResponses}), "text/json")
    response.status_code = 200;
    return response


def get_iphone(request):
    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401 ## removed semi-colon??
        return response

    notes = sort_user_notes(request_user)
        
    numNotes = len(notes)
    startIndex = int(request.GET.get("START_INDEX", 0))
    endIndex = int(request.GET.get("END_INDEX", None))
    if not endIndex:
        endIndex = numNotes
    notesLeft = numNotes - endIndex

    ndicts = [ extract_zen_notes_data(note) for note in notes[startIndex:endIndex] ]
    deltaIndex = endIndex - startIndex
    htmlblob = "\n".join(["<li><div name='note' style='overflow:hidden;' id='%(jid)s' edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onClick='gid(\"%(jid)s\").blur(); zenNoteView.noteClicked(\"%(jid)s\")'><pre>%(noteText)s</pre></div></li>" % n for n in ndicts ]) # onBlur='zenNoteView.noteBlur(\"%(jid)s\")' 
    if notesLeft > 0:       ## height:25px was in style for new notes (=2 lines visible without pre tags)
        htmlblob += "<li><div id='reqMore'><button id='requestMore' onClick='zenAjax.requestMore()'>Get %s of %s more notes</button></div></li>" % (min(deltaIndex, notesLeft), notesLeft)
    response = HttpResponse(htmlblob, 'text/html')
    response.status_code = 200
    return response

def post_usage_statistics(request):
    print "usage stats"
    print request.raw_post_data
    try:
        slog = ServerLog()    
        request_user = basicauth_get_user_by_emailaddr(request);    
        if request_user:
            slog.user = request_user
        slog.when = current_time_decimal()
        slog.action = "usage_statistics"
        slog.info = request.raw_post_data
        slog.host = ""
        slog.url="post_diagnostics"
        slog.request=""
        slog.save()
        return json_response("[]", 200);
    except:
        excinfo = sys.exc_info()
        response = HttpResponse(repr(excinfo), 'text/html');
        response.status_code = 500
        return response


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
    


## Chrome Extension Get/Post Methods

def get_json_notes(request):
    request_user = basicauth_get_user_by_emailaddr(request)
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401
        return response
    
    ## Filter out notes that have already been redacted
    notes = Note.objects.filter(owner=request_user,
                                deleted=0).order_by("-created")

    
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


def post_json_get_updates(request):
    ## Verify User
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

    ## 1) put_zen method of updating client's modified notes
    responses = []
    updateResponses = []
    payload = JSONDecoder().decode(request.raw_post_data)
  
    for datum in payload['modifiedNotes']:
        form = NoteForm(datum)
        form.data['owner'] = request_user.id;
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        if len(matching_notes) == 0: ## Save new note
            if form.is_valid() :
                new_model = form.save()
                responses.append({"jid":form.data['jid'],"version":form.data['version'],"status":201})
                logevent(request,'Note.create',200,form.data['jid'])
            else:
                logevent(request,'Note.create',400,form.errors)
                responses.append({"jid":form.data['jid'],"status":400})
        else:
            ## UPDATE an existing note: check if the client version needs updating
            if (matching_notes[0].version > form.data['version']):
                if form.is_valid():
                    for key in Note.update_fields: ## key={contents,created,deleted,edited}
                        if key == "contents":
                            newContent = "Two versions of this note:\nSubmitted Copy:\n%s\n\nServer Copy:\n%s" % (form.data[key], matching_notes[0].contents)
                            matching_notes[0].__setattr__(key, newContent)
                        else:
                            matching_notes[0].__setattr__(key, form.data[key])
                    newVersion = max(matching_notes[0].version, form.data['version']) + 1
                    matching_notes[0].version = newVersion
                    ## Saved note is MOST-up-to-date, ie:(max(both versions)+1)
                    matching_notes[0].save()
                    updateResponses.append({"jid":form.data['jid'],
                                            "content": newContent,
                                            "version": newVersion, "status":201})
                    continue
                continue            
            # If the data contains no errors,
            if form.is_valid(): # update server note
                for key in Note.update_fields:
                    matching_notes[0].__setattr__(key,form.data[key])
                matching_notes[0].version = form.data['version']+1 
                matching_notes[0].save()
                responses.append({"jid":form.data['jid'],
                                  "version":form.data['version']+1,
                                  "status":201})
            else:
                responses.append({"jid":form.data['jid'],"status":400})
                logevent(request,'Note.create',400,form.errors)
                pass
            pass
        pass

    ## 2) Figure out which of Client's unmodified notes has been updated on server
    updateFinal = []  
    for jid, ver in payload['unmodifiedNotes'].items():
        notes = Note.objects.filter(jid=jid,owner=request_user)
        if notes.count() >= 1 and notes[0].version > ver:
            note = extract_zen_notes_data(notes[0])
            updateFinal.append({"jid":note['jid'],"version":note['version'],
                                "contents":note['noteText'],
                                "deleted":note['deleted'], "created":str(note['created']),
                                "edited":str(note['edited']),
                                "modified":0})

    ## 3) Return notes only server knows about!
    clientJIDs = map(lambda x:int(x['jid']), payload['modifiedNotes'])
    clientJIDs.extend(map(lambda x:int(x), payload['unmodifiedNotes'].keys()))
    serverNotes = map(lambda x:x, Note.objects.filter(owner=request_user, deleted=0).exclude(jid__in=clientJIDs).order_by("-created"))
    ndicts = [ extract_zen_notes_data(note) for note in serverNotes ]
    ndicts.reverse()
    servNotes = []
    for note in ndicts:
        servNotes.append(
            {"jid":note['jid'],"version":note['version'], "contents":note['noteText'],
             "deleted":note['deleted'], "created":str(note['created']),
             "edited":str(note['edited']),
             "modified":0})
        
    response = HttpResponse(JSONEncoder().encode({"committed":responses,
                                                  "update":updateResponses,
                                                  "updateFinal":updateFinal,
                                                  'unknownNotes':servNotes}), "text/json")
    response.status_code = 200;
    return response
