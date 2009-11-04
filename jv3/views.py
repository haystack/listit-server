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
import jv3.utils
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, BugReport, ServerLog
from jv3.utils import gen_cookie, makeChangePasswordRequest, nonblank, get_most_recent, gen_confirm_newuser_email_body, gen_confirm_change_password_email, logevent, current_time_decimal, basicauth_get_user_by_emailaddr, make_username, get_user_by_email, is_consenting_study1, is_consenting_study2, json_response, set_consenting
import time
from django.template.loader import get_template
import sys

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
            print "CREATE form errors %s " % repr(form.errors)
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
            print "CREATE form errors %s " % repr(form.errors)
            continue
        else:
            ## UPDATE an existing note
            ## check if the client version needs updating
            if len(matching_notes) > 1:  print "# of Matching Notes : %d " % len(matching_notes)

            if (matching_notes[0].version > form.data['version']):
                errormsg = "Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  % (form.data["jid"],matching_notes[0].version,form.data["version"])
                print "NOT UPDATED error -- server: %d, YOU %d " % (matching_notes[0].version,form.data['version'])
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
    print responses
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
        response.status_code = 404;
        logevent(request,'changepassword_request',404,repr(request))
        return response;    
    req = makeChangePasswordRequest(email)
    send_mail('Confirm List.it change password request', gen_confirm_change_password_email(req) , 'listit@csail.mit.edu', (matching_user.email,), fail_silently=False)
    response = render_to_response('jv3/changepassword_request.html', {'message': "(I just sent email to you at %s)" % matching_user.email})
    logevent(request,'changepassword_request',200,repr((email,req.cookie,)))
    return response;

def changepassword_confirm(request): ## GET view, parameter cookie
    cookie = request.GET['cookie'];
    matching_requests = ChangePasswordRequest.objects.filter(cookie=cookie)
    if len(matching_requests) == 0:
        response = HttpResponse("Sorry, I did not know about your request to change your password.","text/html")
        response.status_code = 405;
        logevent(request,'changepassword',404,repr(request))
        return response;    
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



class ActivityLogCollection(Collection):

    def read(self,request):
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.read',401,{"requesting user:":jv3.utils.decode_emailaddr(request)})
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))
            
        user_activity = ActivityLog.objects.filter(owner=request_user)
        if (request.GET['type'] == 'get_max_log_id'):
            ## "what is the last thing i sent?"
            return self._handle_max_log_request(user_activity,request);
        else:
            ## retrieve the entire activity log            
            return self.responder.list(request, qs_user)

    def _handle_max_log_request(self,user_activity,request):
        ## return the max id (used by the client to determine which recordsneed to be retrieved.)
        try:
            most_recent_activity = get_most_recent(user_activity.filter(client=self._get_client(request)))
            if most_recent_activity:
                #print "MOST RECENT ACTIVITY matching client  %s - %s " % (self._get_client(request),most_recent_activity.when)
                return HttpResponse(JSONEncoder().encode({'value':int(most_recent_activity.when)}), self.responder.mimetype)
            return self.responder.error(request, 404, ErrorDict({"value":"No activity found"}));
        except:
            print sys.exc_info()
    
    def _get_client(self,request):
        if request.GET.has_key('client'):
            print request.GET['client']
            return request.GET['client']
        return None                

    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, ErrorDict({"autherror":"Incorrect user/password combination"}))

        user_activity = ActivityLog.objects.filter(owner=request_user,client=self._get_client(request))
        committed = [];
        incoming = JSONDecoder().decode(request.raw_post_data)
        #print "incoming activity logs ~~ %d" % (len(incoming))
        #if len(incoming) > 0:
        #    print "starting at ~~ %s" % (repr(incoming[0]))
        for item in incoming: #serializers.deserialize('json',request.raw_post_data):
            #print "item is %s " % repr(item)
            try:
                if len(user_activity.filter(when=item['id'])) > 0:
                    print "activity log : skipping duplicate %d " % item['id'];
                    continue
                ##print "Committing %s item %s " % (entry.owner.email,repr(item))
                entry = ActivityLog();
                entry.owner = request_user;
                entry.when = item['id'];
                entry.action = item['type'];
                entry.noteid = item.get("noteid",None);
                entry.noteText = item.get("noteText",None);
                entry.search = item.get("search",None);
                entry.client = item.get("client",None); ## added in new rev
                entry.save();
                committed.append(item['id']);
            except StandardError, error:
                print "Error with entry %s item %s " % (repr(error),repr(item))
        pass

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
            "deleted":"false",
            "created":note.created};        
            

def get_zen(request):
    iphone = True
    print 0
    request_user = basicauth_get_user_by_emailaddr(request)
    print 1.5
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401 ## removed semi-colon??
        return response
    print 1
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
        
    else:
        # sort by creation date ?
        notes = Note.objects.filter(owner=request_user,deleted=False).order_by("-created").exclude(jid=-1)
    print 2
    
    startIndex = int(request.GET.get("START_INDEX", 0))
    print "Start Index: %s" % startIndex
    ##startIndex = urllib.unquote(startIndex)
    print 3
    noteLength = len(notes)
    endIndex = int(request.GET.get("END_INDEX", -1))
    if endIndex == -1:
        iphone = False
        endIndex = noteLength

    additionalNotesWaiting = True
    if iphone and (endIndex >= noteLength):
        additionalNotesWaiting = False;
    ##endIndex = urllib.unquote(endIndex)
    print "Almost!"
    
    ## make magic happen
    ndicts = [ extract_zen_notes_data(note) for note in notes[startIndex:endIndex] ]

    print "Almost2"

    deltaIndex = endIndex - startIndex

    htmlblob = "\n".join([ "<div class='note'> <img class='deleteX' src='x.png' alt='Delete' onClick='zenNoteAjax.saveEditedNote(\"%(jid)s\",true)'/><textarea name='note' id='%(jid)s' edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onClick='zenNoteView.noteClicked(\"%(jid)s\")' cols='%(col)s' rows='%(row)s' hasFocus='false' hasSelect='false' onBlur='zenNoteView.noteBlur(\"%(jid)s\")' style='overflow:hidden'>%(noteText)s</textarea></div>" % n for n in ndicts ])
    if iphone and additionalNotesWaiting:
        htmlblob += "\n <button id='requestMore' onClick='zeniPhone.requestMore()'>Get %s more notes</div>" % (deltaIndex)
    elif iphone:
        htmlblob += "\n <button id='requestMore' style='display:none' onClick='zeniPhone.requestMore()'>Get %s more notes</div>" % (deltaIndex)
        
    print "Almost3"
    response = HttpResponse(htmlblob, 'text/html');
    print "Almost4"
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

    print "0"

    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401;
        return response

    print "1"
    
    responses = []
    updateResponses = []
    ## print "raw post data: %s " % repr(request.raw_post_data)
    if not request.raw_post_data:
        response = HttpResponse(JSONEncoder().encode({'committed':[]}), "text/json")
        response.status_code = 200;
        return response

    print "2"
        
    for datum in JSONDecoder().decode(request.raw_post_data):
        ## print "datum : %s "% repr(datum)
        ## print datum
        form = NoteForm(datum)
        form.data['owner'] = request_user.id;                 ## clobber this whole-sale from authenticating user
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        print "3"
        if len(matching_notes) == 0:
            print "4a: no matching notes, make new note"
            ## CREATE a new note
            # If the data contains no errors, save the model,
            if form.is_valid() :
                print "Creating new note with JID: %s" % (form.data[jid])
                new_model = form.save()
                responses.append({"jid":form.data['jid'],"status":201})
                logevent(request,'Note.create',200,form.data['jid'])
                continue
            print "4b: website note form not valid"
            ## something didn't pass form validation
            logevent(request,'Note.create',400,form.errors)
            responses.append({"jid":form.data['jid'],"status":400})
            print "CREATE form errors %s " % repr(form.errors)
            continue
        else:
            print "4b: update old note"
            ## UPDATE an existing note
            ## check if the client version needs updating
            if len(matching_notes) > 1:  print "# of Matching Notes : %d " % len(matching_notes)
            
            if (matching_notes[0].version > form.data['version']):
                print "5a: client ver needs updating, form.is_valid() is: %s" % (form.is_valid()) 
                ## Change to return {jid,contents,created,deleted,edited}
                if form.is_valid():
                    for key in Note.update_fields: ## key={contents,created,deleted,edited}
                        if key == "contents":
                            newContent = "Two versions of this note:\nSubmitted Copy:\n%s\n\nServer Copy:\n%s" % (form.data[key], matching_notes[0].contents)
                            print "Key: %s, Data: %s" % (key, newContent)
                            matching_notes[0].__setattr__(key, newContent)
                        else:
                            print "Key: %s, Data: %s" % (key, form.data[key])
                            matching_notes[0].__setattr__(key, form.data[key])
                    ## Now return to user jid,created,deleted,edited and new contents of note!
                    # increment version number
                    newVersion = max(matching_notes[0].version, form.data['version']) + 1
                    matching_notes[0].version = newVersion ## Saved note is MOST-up-to-date, ie:(max(both versions)+1)
                    # save!
                    # print "SAVING %s, is it deleted? %s " % (repr(matching_notes[0]),repr(matching_notes[0].deleted))
                    matching_notes[0].save()
                    updateResponses.append({"jid":form.data['jid'],"content": newContent, "version": newVersion,"status":201})
                    continue
                ## Original Code Below
                ##errormsg = "Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  % (form.data["jid"],matching_notes[0].version,form.data["version"])
                ##print "NOT UPDATED error -- server: %d, YOU %d " % (matching_notes[0].version,form.data['version'])
                ##responses.append({"jid":form.data['jid'],"status":201}) ##was 400
                continue            
            # If the data contains no errors, migrate the changes over to
            # the version of the note in the db, increment the version number
            # and announce success
            if form.is_valid() :
                print "6a: update server note"
                for key in Note.update_fields:
                    matching_notes[0].__setattr__(key,form.data[key])
                    print "Key: %s, Data: %s" % (key, form.data[key])

                # increment version number
                matching_notes[0].version = form.data['version'] + 1 ## matching_notes[0].version + 1;
                # save!
                # print "SAVING %s, is it deleted? %s " % (repr(matching_notes[0]),repr(matching_notes[0].deleted))
                matching_notes[0].save()
                responses.append({"jid":form.data['jid'],"status":201})
            else:
                print "6b: client note not valid"
                # Otherwise return a 400 Bad Request error.
                responses.append({"jid":form.data['jid'],"status":400})
                logevent(request,'Note.create',400,form.errors)
                pass
        pass
    print "7: almost done"
    print responses
    response = HttpResponse(JSONEncoder().encode({'committed':responses, 'update':updateResponses}), "text/json")
    response.status_code = 200;
    print "8: returning!"
    return response

def get_iphone(request):
    print "get_iphone started"
    request_user = basicauth_get_user_by_emailaddr(request);
    if not request_user:
        logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
        response = HttpResponse(JSONEncoder().encode({'autherror':"Incorrect user/password combination"}), "text/json")
        response.status_code = 401 ## removed semi-colon??
        return response
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
    else:
        # sort by creation date ?
        notes = Note.objects.filter(owner=request_user,deleted=False).order_by("-created").exclude(jid=-1)
    startIndex = int(request.GET.get("START_INDEX", 0))
    endIndex = int(request.GET.get("END_INDEX", -1))
    
    ## make magic happen
    ndicts = [ extract_zen_notes_data(note) for note in notes[startIndex:endIndex] ]


    deltaIndex = endIndex - startIndex

    htmlblob = "\n".join([ "<li><div name='note' id='%(jid)s' edited='%(edited)s' created='%(created)s' version='%(version)s' deleted='%(deleted)s' pk='%(pk)s' onClick='zenNoteView.noteClicked(\"%(jid)s\")' onBlur='zenNoteView.noteBlur(\"%(jid)s\")'>%(noteText)s</div></li>" % n for n in ndicts ])
    htmlblob += "<li><div><button id='requestMore' onClick='zeniPhone.requestMore()'>Get %s more notes</button></div></li>" % (deltaIndex)
    response = HttpResponse(htmlblob, 'text/html');
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
    
    
    
        
