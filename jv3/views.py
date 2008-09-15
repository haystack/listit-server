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
from jv3.models import Note
import jv3.utils
from jv3.models import ActivityLog, UserRegistration, CouhesConsent, ChangePasswordRequest, BugReport
from jv3.utils import gen_cookie, makeChangePasswordRequest, nonblank, get_most_recent, gen_confirm_newuser_email_body, gen_confirm_change_password_email, logevent, current_time_decimal, basicauth_get_user_by_emailaddr, make_username
import time
from django.template.loader import get_template


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
            print  "request user is none"
            logevent(request,'Note.read',401,{"requesting user:":jv3.utils.decode_emailaddr(request)})
            return self.responder.error(request, 401, "Incorrect user/password combination")
        
        print "fooo!"
        print "request user is %s " % repr(request_user)
        #qs_user = Note.objects.filter(owner=request_user).exclude(deleted=True)
        qs_user = Note.objects.filter(owner=request_user)  ## i realize this is controversial, but is necessary for sync to update !
        logevent(request,'Note.read',200)
        return self.responder.list(request, qs_user)

    def create(self,request):
        
        # MERGED create and update method for server, so that we don't have to do a PUT
        ResourceForm = forms.form_for_model(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        form = ResourceForm(data)

        # get user being authenticated
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'Note.create POST',401, jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, "Incorrect user/password combination")

        form.data['owner'] = request_user;                 ## clobber this whole-sale from authenticating user
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        
        if len(matching_notes) == 0:
            ## CREATE a new note
            # If the data contains no errors, save the model,
            if form.is_valid() :
                new_model = form.save()
                model_entry = self.entry_class(self, new_model)
                response = model_entry.read(request)
                response.status_code = 201
                response['Location'] = model_entry.get_url()
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
                response['Location'] = self.get_url()
                # announce success
                logevent(request,'Note.update',200,form.data['jid'])
                return response
            # Otherwise return a 400 Bad Request error.
            logevent(request,'Note.create',400,form.errors)
            print "UPDATE form errors %s " % repr(form.errors)
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
        ResourceForm = forms.form_for_model(Note, form=self.form_class)
        data = self.receiver.get_put_data(request)
        form = ResourceForm(data)
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'Note.delete',401, jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, "Incorrect user/password combination")
        
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        
        if len(matching_notes) == 0:
            return self.responder.error(request, 404, ErrorDict({"jid":"Note with jid %d not found"  % form.data["jid"]}));

        for to_die in matching_notes:
            to_die.delete()

        return HttpResponse(_("Object successfully deleted."), self.responder.mimetype)
    

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
    userid = request.GET['email'];
    print " userid is %s " % repr(userid)
    if len(authmodels.User.objects.filter(username=userid)) > 0:
        response = HttpResponse("User exists", "text/html");
        response.status_code = 200;
        return response
    response = HttpResponse("User does not exist", "text/html");
    response.status_code = 404;
    return response

def createuser(request):
    username = request.POST['username'];
    passwd = request.POST['password'];
    print " userid is %s, password is %s " % (repr(username),repr(passwd))
    if len(authmodels.User.objects.filter(username=username)) > 0:
        response = HttpResponse("User exists", "text/html");
        response.status_code = 405;
        logevent(request,'createuser',205,username)
        return response
    
    user = UserRegistration();
    user.when = current_time_decimal();
    user.email = username;
    user.password = passwd;

    ## couhes handling: couhes requires first & last name 
    user.couhes = (request.POST['couhes'] == 'true'); ## assume this is boolean
    user.first_name = request.POST['firstname']; 
    user.last_name = request.POST['lastname']; 
    
    print "user couhes is %s " % repr(type(user.couhes))
    user.cookie = gen_cookie();
    user.save();
    
    print "New user registration is %s " % repr(user);
    send_mail('Did you register for Listit?', gen_confirm_newuser_email_body(user) , 'listit@csail.mit.edu', (user.email,), fail_silently=False)
    response = HttpResponse("UserRegistration created successfully", "text/html");    
    response.status_code = 200;
    logevent(request,'createusr',201,user)
    return response

def confirmuser(request):
    cookie = request.GET['cookie'];
    matching_registrations = UserRegistration.objects.filter(cookie=cookie)
    if len(matching_registrations) > 0:
        ## create user
        newest_registration = get_most_recent(matching_registrations)
        ## check to see if already registered
        if len(authmodels.User.objects.filter(email=newest_registration.email)) > 0:
            user = authmodels.User.objects.filter(email=newest_registration.email)[0]
            logevent(request,'confirmuser','alreadyregistered',cookie)
            return render_to_response('jv3/confirmuser.html', {"message": "I think already know you, %s.  You should have no trouble logging in.  Let us know if you have problems! " % newest_registration.email,
                                                               'username':user.email, 'password':newest_registration.password, 'server':settings.SERVER_URL});
        
        user = authmodels.User();
        user.username = make_username(newest_registration.email);  ## intentionally a dupe, since we dont have a username. WE MUST be sure not to overflow it (max_chat is default 30)
        user.email = newest_registration.email;
        user.set_password(newest_registration.password);
        user.save();
        
        ## handle couhes reg
        if (newest_registration.couhes):
            assert nonblank(newest_registration.first_name) and nonblank(newest_registration.last_name), "Couhes requires non blank first and last names"
            user.first_name = newest_registration.first_name;
            user.last_name = newest_registration.last_name;
            user.save();
            
            ## now make couhes consetnform
            cc = CouhesConsent()
            cc.owner = user;
            cc.signed_date = newest_registration.when;
            cc.save()

        logevent(request,'confirmuser',200,user)
        return render_to_response('jv3/confirmuser.html', {'message': "Okay, thank you for confirming that you are a human, %s.  You can now synchronize with List.it. " % user.email,
                                                           'username':user.email, 'password':newest_registration.password, 'server':settings.SERVER_URL});
    
    response = render_to_response('jv3/confirmuser.html', {'message': "Oops, could not figure out what you are talking about!"});
    response.status_code = 405;
    logevent(request,'confirmuser',405,request)
    return response

def reconsent(request):
    email = request.GET['email']
    newest_registration  = get_most_recent(UserRegistration.objects.filter(email=email))
    if not newest_registration == None:
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
                           

def changepassword_request(request): ## GET view, parameter username
    username = request.GET['username'];
    matching_users = authmodels.User.objects.filter(username=username)
    if len(matching_users) == 0:
        response = HttpResponse("Unknown user, did you register previously for List.it under a different email address?", "text/html");    
        response.status_code = 404;
        logevent(request,'changepassword_request',404,repr(request))
        return response;    
    req = makeChangePasswordRequest(username);
    send_mail('Confirm List.it change password request', gen_confirm_change_password_email(req) , 'listit@csail.mit.edu', (matching_users[0].email,), fail_silently=False)
    response = render_to_response('jv3/changepassword_request.html', {'message': "(I just sent email to you at %s)" % matching_users[0].email})
    logevent(request,'changepassword_request',200,repr((username,req.cookie,)))
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
    matching_user = authmodels.User.objects.filter(username=reqobject.username)
    if len(matching_user) == 0:
        response = HttpResponse("Sorry, I did not know about the user you are asking about: %s " % repr(reqobject.username),"text/html")
        response.status_code = 404;
        logevent(request,'changepassword',404,repr(request))
        return response;    
    matching_user[0].set_password(password)
    matching_user[0].save()
    reqobject.delete()
    response = render_to_response('jv3/confirmuser.html', {'message': "Your password hs been updated successfully, %s." % matching_user[0].username})
    logevent(request,'changepassword',200,repr(cookie))
    return response;    

## utilities -- NOT views

class ActivityLogCollection(Collection):

    def read(self,request):
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.read',401,{"requesting user:":jv3.utils.decode_emailaddr(request)})
            return self.responder.error(request, 401, "Incorrect user/password combination")
            
        user_activity = ActivityLog.objects.filter(owner=request_user)
        if (request.GET['type'] == 'get_max_log_id'):
            ## return the max id (used by the client to determine which records
            ## need to be retrieved.
            most_recent_activity = get_most_recent(user_activity);
            if most_recent_activity == None: most_recent_activity = 0;
            print "most_recent " + repr(most_recent_activity)
            if most_recent_activity:
                logevent(request,'ActivityLog.read',200,{"data":repr(most_recent_activity.when)})
                return HttpResponse(JSONEncoder().encode({'value':int(most_recent_activity.when)}), self.responder.mimetype)
            logevent(request,'ActivityLog.,read',404,{"data":"no log entries"})
            return self.responder.error(request, 404, ErrorDict({"value":"No activity found"}));
        else:
            ## retrieve the entire activity log            
            return self.responder.list(request, qs_user)


    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = basicauth_get_user_by_emailaddr(request);
        if not request_user:
            logevent(request,'ActivityLog.create POST',401,jv3.utils.decode_emailaddr(request))
            return self.responder.error(request, 401, "Incorrect user/password combination")

        user_activity = ActivityLog.objects.filter(owner=request_user)
        committed = [];

        ## debug stuff
        #print "\n\n\n\n"
        ##print "ACTLOG request user is  %s " % repr(request_user)
        #print "ACTLOG posted items is %s %s " % (repr(type(request.POST)),repr(request.POST))
        #print "ACTLOG posted raw_post_data is %s " % repr(request.raw_post_data)

        # manually handle deserialization because
        #for items in request.POST
        #print "ACTLOG items is [%d]:%s " % (len(items),repr(items))
        for item in JSONDecoder().decode(request.raw_post_data): #serializers.deserialize('json',request.raw_post_data):
            #print "item is %s " % repr(item)
            try:
                if len(user_activity.filter(when=item['id'])) > 0:
                    print "skipping committing duplicate entry %d " % item['id'];
                    continue
                entry = ActivityLog();
                entry.owner = request_user;
                entry.when = item['id'];
                entry.action = item['type'];
                entry.noteid = item.get("noteid",None);
                entry.noteText = item.get("noteText",None);
                entry.search = item.get("search",None);
                entry.save();
                committed.append(item['id']);
            except StandardError, error:
                print "Error with entry %s " % repr(error)
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
    if len(authmodels.User.objects.filter(email=registration.email)) == 0:
        return None
    return (authmodels.User.objects.filter(email=registration.email)[0], registration)
    
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
