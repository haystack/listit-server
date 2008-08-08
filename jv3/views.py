from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _
from django.core import serializers

from django.utils.simplejson import JSONEncoder, JSONDecoder
import django.contrib.auth.models as authmodels
from django_restapi.authentication import basicauth_get_user 
from server.django_restapi.resource import Resource
from server.django_restapi.model_resource import InvalidModelData
from server.jv3.models import SPO
from server.jv3.models import Note
from server.jv3.models import Sighting, ActivityLog
import time

# Create your views here.
class SPOCollection(Resource):
    def read(self, request):
        spos = SPO.objects.all()
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
        request_user = basicauth_get_user(request);
        print "request user is %s " % repr(request_user)
        qs_user = Note.objects.filter(owner=request_user).exclude(deleted=True)
        return self.responder.list(request, qs_user)
    
    def create(self,request):
        """
        Creates a Note with attributes given by POST, then  redirects to the resource URI.

        Uses 'jid' field as (client side) primary key, so does not permit the creation
        of a note with matching jid -- throwing an error 400 if this happens.        
        """
        # Create form filled with POST data
        ResourceForm = forms.form_for_model(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        form = ResourceForm(data)

        request_user = basicauth_get_user(request);        
        print "request user is  %s " % repr(request_user)
        print "form data before %s " % repr(form.data);
        form.data['owner'] = request_user;                 ## clobber this whole-sale from authenticating user
        print "form data after %s " % repr(form.data);
        
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        if len(matching_notes) > 0:
            return self.responder.error(request, 400,
                                        ErrorDict({"jid":"A note with jid %d already exists. Use Update/Delete (PUT, not POST)" % form.data["jid"]}));
        
        # If the data contains no errors, save the model,
        if form.is_valid() :
            new_model = form.save()
            model_entry = self.entry_class(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response['Location'] = model_entry.get_url()
            return response

        ## something didn't pass form validation
        return self.responder.error(request, 400, form.errors);
    
    def update(self,request):
        """
        Commit changes to an existing note in the DB. it Must already exist in the
        DB or we'll issue a 404. A commit is only permitted if the version being
        committed has merged (on the client side) the latest version of the note
        we're talking about.
        Once the note's changes have been committed, increment the version #.
        """
        
        ResourceForm = forms.form_for_model(Note, form=self.form_class)
        data = self.receiver.get_put_data(request)
        form = ResourceForm(data)

        request_user = basicauth_get_user(request);        
        form.data['owner'] = request_user;  ## clobber owner id whole-sale from authenticating user
        
        matching_notes = Note.objects.filter(jid=form.data['jid'],owner=request_user)
        
        if len(matching_notes) == 0:
            return self.responder.error(request,
                                        404,
                                        ErrorDict({"jid": "Note with jid %d not found"  % form.data["jid"]}));

        if (matching_notes[0].version != form.data['version']):
            return self.responder.error(request,
                                        400,
                                        ErrorDict({"jid":"Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  % (form.data["jid"],
                                                                                                                                                    matching_notes[0].version,
                                                                                                                                                    form.data["version"])}))        

        # If the data contains no errors, migrate the changes over to
        # the version of the note in the db, increment the version number
        # and announce success
        if form.is_valid() :
            for key in Note.update_fields:
                matching_notes[0].__setattr__(key,form.data[key])

            #matching_notes[0]['deleted'] = form.data.get('deleted',False) 
            # increment version number
            matching_notes[0].version = matching_notes[0].version + 1;
            # save!
            matching_notes[0].save()
            response = self.read(request)
            response.status_code = 200
            response['Location'] = self.get_url()
            # announce success
            return response
        
        # Otherwise return a 400 Bad Request error.
        return self.responder.error(request, 400, form.errors);

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
        request_user = basicauth_get_user(request);
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

class  SightingsCollection(Collection):
    ## read is covered by the superclass
    def read(self, request):
        """
        Returns a representation of the queryset.
        The format depends on which responder (e.g. JSONResponder)
        is assigned to this ModelResource instance. Usually called by a
        HTTP request to the factory URI with method GET.
        """
        #request_user = basicauth_get_user(request);        
        #qs_user = Note.objects.filter(owner=request_user)
        return self.responder.list(request, self.queryset)

def sightings_new(request):
    ## for posting from GPSTracker: 
    ## http://www.websmithing.com/portal/Programming/tabid/55/articleType/ArticleView/articleId/2/Google-Map-GPS-Cell-Phone-Tracker.aspx
    sighting = Sighting()
    sighting.lat = request.GET['lat'];
    sighting.lon = request.GET['lng'];
    sighting.when = int(time.time()*1000);
    sighting.dirr = request.GET['dir'];
    sighting.mph= request.GET['mph'];
    sighting.save();
    image_data = open('/z/www/red.png','rb').read();
    # print "data len is %d " % len(image_data)
    return  HttpResponse(image_data, mimetype='image/png');

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
    
    rpd = request.raw_post_data;
    print "rpd is %s " % repr(rpd);
    username = request.POST['username'];
    passwd = request.POST['password'];
    print " userid is %s, password is %s " % (repr(username),repr(passwd))
    if len(authmodels.User.objects.filter(username=username)) > 0:
        response = HttpResponse("User exists", "text/html");
        response.status_code = 405;
        return response
    user = authmodels.User();
    user.username = username;
    user.email = username;
    user.set_password(passwd); 
    user.save();
    print "user is %s " % repr(user);
    response = HttpResponse("User created successfully", "text/html");
    response.status_code = 200;
    return response

class ActivityLogCollection(Collection):

    def read(self,request):
        request_user = basicauth_get_user(request);
        if (not request_user):
            return self.responder.error(request, 405, ErrorDict({"user":"User username/password incorrect, or unknown user"}))
            
        user_activity = ActivityLog.objects.filter(owner=request_user)
        if (request.GET['type'] == 'get_max_log_id'):
            ## return the max id (used by the client to determine which records
            ## need to be retrieved.
            most_recent_activity = self.get_most_recent(user_activity);
            if most_recent_activity == None: most_recent_activity = 0;
            print "most_recent " + repr(most_recent_activity)
            if most_recent_activity:
                return HttpResponse(JSONEncoder().encode({'value':most_recent_activity.when}), self.responder.mimetype)
            return self.responder.error(request, 404, ErrorDict({"value":"No activity found"}));
        else:
            ## retrieve the entire activity log            
            return self.responder.list(request, qs_user)

    def get_most_recent(self,act):
        if act == None or len(act) == 0:
            return None
        def comp(x,y):
            if x.when >= y.when:
                return x;
            return y;
        return reduce(comp,act);        

    def create(self,request):
        """
        lets the user post new activity in a giant single array of activity log elements
        """
        request_user = basicauth_get_user(request);
        if (not request_user): return self.responder.error(request, 405, ErrorDict({"user":"User username/password incorrect, or unknown user"}))
        user_activity = ActivityLog.objects.filter(owner=request_user)
        committed = [];

        ## debug stuff
        print "request user is  %s " % repr(request_user)
        print "posted item is %s " % repr(request.POST);
        print "posted raw_post_data is %s " % repr(request.raw_post_data);

        # manually handle deserialization because 
        for items in request.POST:            
            # print "item is %s " % repr(items)
            for item in JSONDecoder().decode(items): #serializers.deserialize('json',items):
                #print "deseritem is %s " % repr(item)
                try:
                    if len(user_activity.filter(when=item['id'])) > 0:
                        print "skipping committing duplicate entry %d " % item['id'];
                        continue
                    entry = ActivityLog();
                    entry.owner = request_user;
                    entry.when = item['id'];
                    entry.action = item['type'];
                    entry.noteid = item.get("obj",None);
                    entry.noteText = item.get("objText",None);
                    entry.save();
                    committed.append(item['id']);
                except StandardError, error:
                    print "Error with entry " % repr(entry)
            pass

        response = HttpResponse(JSONEncoder().encode({'committed':committed}), self.responder.mimetype)
        response.status_code = 200;
        return response

        
