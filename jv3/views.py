from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django_restapi.model_resource import Collection
from django.forms.util import ErrorDict
from django.utils.translation.trans_null import _

import django.contrib.auth.models as authmodels
from server.django_restapi.resource import Resource
from server.django_restapi.model_resource import InvalidModelData
from server.jv3.models import SPO
from server.jv3.models import Note

# Create your views here.
class SPOCollection(Resource):
    def read(self, request):
        spos = SPO.objects.all()
        context = {'spos':spos}
        return render_to_response('jv3/spos.html', context)


class NoteCollection(Collection):
    # use default implementation
    # def read(self,request):
    #         print "read  request %s " % repr(request)
    #         #return render_to_response('jv3/spos.html',{'spos':Note.objects.all()});
    #         return self.responder.list(Note.objects.all,request
    
    def create(self,request):
        """
        Creates a resource with attributes given by POST, then
        redirects to the resource URI. 
        """
        ## debug XX print "CREATE with request %s " % repr(request)
        # Create form filled with POST data
        ResourceForm = forms.form_for_model(self.queryset.model, form=self.form_class)
        data = self.receiver.get_post_data(request)
        form = ResourceForm(data)

        # print "form data is " + repr(form.data)
        matching_notes = Note.objects.filter(jid=form.data['jid'])
        #print "matching notes is " + repr(len(matching_notes)) + " : " + repr(matching_notes)

        if len(matching_notes) > 0:
            return self.responder.error(request,
                                        400,
                                        ErrorDict({"jid":"A note with jid %d already exists. Use Update/Delete (PUT, not POST)" % form.data["jid"]}));
                    #raise InvalidModelData(errors=ErrorDict({"jid":"A note with jid %d already exists. Use Update/Delete (PUT, not POST)"}))  
        
        # If the data contains no errors, save the model,
        # return a "201 Created" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        # print "IsValid? %s Form is %s" % (repr(form.is_valid()),repr(dir(form)))
        if form.is_valid() :
            new_model = form.save()
            model_entry = self.entry_class(self, new_model)
            response = model_entry.read(request)
            response.status_code = 201
            response['Location'] = model_entry.get_url()
            return response

        return self.responder.error(request,
                                    400,
                                    form.errors);
        # Otherwise return a 400 Bad Request error.
        ## raise InvalidModelData(form.errors)
    
    def update(self,request):
        #print "update with request %s " % repr(request)
        # Create a form from the model/PUT data
        
        ResourceForm = forms.form_for_model(Note, form=self.form_class)
        data = self.receiver.get_put_data(request)
        form = ResourceForm(data)
        matching_notes = Note.objects.filter(jid=form.data['jid'])
        
        if len(matching_notes) == 0:
            return self.responder.error(request,
                                        404,
                                        ErrorDict({"jid": "Note with jid %d not found"  % form.data["jid"]}));
            ## raise InvalidModelData(errors=ErrorDict({"jid":"Note with jid %d not found"  % form.data["jid"]}))

        if (matching_notes[0].version != form.data['version']):
            return self.responder.error(request,
                                        400,
                                        ErrorDict({"jid":"Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  % (form.data["jid"],
                                                                                                                                                    matching_notes[0].version,
                                                                                                                                                    form.data["version"])}))        
        #raise InvalidModelData(errors=ErrorDict({"jid":"Versions for jid %d not compatible (local:%d, received: %d). Do you need to update? "  %
        #(form.data["jid"],matching_notes[0].version,form.data["version"])}));

        # If the data contains no errors, save the model,
        # return a "200 Ok" response with the model's
        # URI in the location header and a representation
        # of the model in the response body.
        if form.is_valid() :
            for key in Note.update_fields:
                matching_notes[0].__setattr__(key,form.data[key])
            # increment version number
            matching_notes[0].version = matching_notes[0].version + 1;
            # save!
            matching_notes[0].save()
            ##form.save()
            response = self.read(request)
            response.status_code = 200
            response['Location'] = self.get_url()
            return response
        
        # Otherwise return a 400 Bad Request error.
        #raise InvalidModelData(form.errors)
        return self.responder.error(request, 400, form.errors);

    def delete(self, request):
        """
        Deletes the model associated with the current entry.
        Usually called by a HTTP request to the entry URI
        with method DELETE.
        """
        ResourceForm = forms.form_for_model(Note, form=self.form_class)
        data = self.receiver.get_put_data(request)
        form = ResourceForm(data)
        matching_notes = Note.objects.filter(jid=form.data['jid'])
        
        if len(matching_notes) == 0:
            return self.responder.error(request, 404, ErrorDict({"jid":"Note with jid %d not found"  % form.data["jid"]}));
            ##raise InvalidModelData(errors=ErrorDict({"jid":"Note with jid %d not found"  % form.data["jid"]}))

        for to_die in matching_notes:
            to_die.delete()

        return HttpResponse(_("Object successfully deleted."), self.responder.mimetype)
    
    
    
