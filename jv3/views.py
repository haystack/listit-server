from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

import django.contrib.auth.models as authmodels
from server.django_restapi.resource import Resource
from server.jv3.models import SPO

# Create your views here.
class SPOCollection(Resource):
    def read(self, request):
        spos = SPO.objects.all()
        context = {'spos':spos}
        return render_to_response('jv3/spos.html', context)
