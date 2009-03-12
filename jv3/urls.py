from django.conf.urls.defaults import *
import django.contrib.auth.views
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from django_restapi.receiver import *
from jv3.models import SPO, SPOForm, Note, NoteForm, ActivityLog
from jv3.views import SPOCollection, NoteCollection, ActivityLogCollection, userexists, createuser, confirmuser, submit_bug_report, reconsent
from jv3.views import changepassword, changepassword_request, changepassword_confirm, notes_post_multi
from django_restapi.authentication import HttpBasicAuthentication, HttpDigestAuthentication, djangouser_auth
from jv3.views import get_survey, post_survey, done_survey

class XMLReceiverSetOwner(XMLReceiver):
    def __init__(self, user):
        self.format = 'xml'
        self.user = user

    def get_data(self, request, method):
        d = super(XMLReceiverSetOwner, self).get_data(request, method)
        ##d['owner'] = User.objects
        print dir(request)
        print 'here d=', d
        return d

class JSONReceiverSetOwner(JSONReceiver):
    def get_data(self, request, method):
        d = super(JSONReceiverSetOwner, self).get_data(request, method)
        return d

fullxml_spo_resource = Collection(
    queryset = SPO.objects.all(), 
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ['owner', 'version', 'subj', 'pred', 'obj'],
    form_class=SPOForm,
    receiver = XMLReceiver(),
    responder = XMLResponder(),
)
fulljson_spo_resource = Collection(
    queryset = SPO.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ['owner', 'version', 'subj', 'pred', 'obj'],
    form_class=SPOForm,
    receiver = JSONReceiver(),
    responder = JSONResponder()
)

def filtered_xml_resource(queryset):
    return Collection(
        queryset=queryset,
        permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
        expose_fields = ['owner', 'version', 'subj', 'pred', 'obj'],
        form_class=SPOForm,
        receiver=XMLReceiver(),
        responder=XMLResponder())
def filtered_json_resource(queryset):
    return Collection(
        queryset=queryset,
        permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
        expose_fields = ['owner', 'version', 'subj', 'pred', 'obj'],
        form_class=SPOForm,
        receiver=JSONReceiver(),
        responder=JSONResponder())

def xml_by_version(request, version):
    c = filtered_xml_resource(SPO.objects.filter(version=version))
    return c(request)
def xml_by_subj(request, subj):
    c = filtered_xml_resource(SPO.objects.filter(subj=subj))
    return c(request)
def xml_by_pred(request, pred):
    c = filtered_xml_resource(SPO.objects.filter(pred=pred))
    return c(request)
def xml_by_obj(request, obj):
    c = filtered_xml_resource(SPO.objects.filter(obj=obj))
    return c(request)
def json_by_subj(request, subj):
    c = filtered_json_resource(SPO.objects.filter(subj=subj))
    return c(request)
def json_by_pred(request, pred):
    c = filtered_json_resource(SPO.objects.filter(pred=pred))
    return c(request)
def json_by_obj(request, obj):
    c = filtered_json_resource(SPO.objects.filter(obj=obj))
    return c(request)


fullnotes_json_resource = NoteCollection(
    queryset = Note.objects.all(), 
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ['owner','jid','version','created','contents','edited', 'deleted'],
    #authentication = HttpBasicAuthentication(), #HttpDigestAuthentication(djangouser_auth),
    form_class=NoteForm,
    receiver = JSONReceiver(),
    responder = JSONResponder(),
)


actlog_view = ActivityLogCollection(
    queryset=ActivityLog.objects.all(),
    permitted_methods= ('GET','POST',),
    expose_fields = ['when','action','noteid','noteText'],
    responder=JSONResponder(),
    receiver=JSONReceiver())

urlpatterns = patterns('server.jv3.views.',
    (r'^all$', SPOCollection()),
    (r'^all/xml$', fullxml_spo_resource),
    (r'^all/json$', fulljson_spo_resource),
    (r'^entry/(\d+)/xml$', fullxml_spo_resource),
    (r'^entry/(\d+)/json$', fulljson_spo_resource),
    (r'^version/(.+)/xml$', xml_by_version),
    (r'^subj/(.+)/xml$', xml_by_subj),
    (r'^pred/(.+)/xml$', xml_by_pred),
    (r'^obj/(.+)/xml$', xml_by_obj),
    (r'^subj/(.+)/json$', json_by_subj),
    (r'^pred/(.+)/json$', json_by_pred),
    (r'^obj/(.+)/json$', json_by_obj),
    (r'^notes$', fullnotes_json_resource),   # GET
    (r'^notes/$', fullnotes_json_resource), ## POST
    (r'^notespostmulti/$', notes_post_multi), ## updated protocol for listit 0.4.0, much faster
    (r'^notelog$', actlog_view),
    (r'^notelog/$', actlog_view),
    (r'^newuser$', lambda request: render_to_response('jv3/newuser.html')),
    (r'^userexists$', userexists),
    (r'^createuser/$', createuser), ## POST
    (r'^confirmuser$', confirmuser),

    (r'^reconsent$', reconsent),
    
    (r'^changepasswordrequest', changepassword_request), ## GET
    (r'^changepasswordconfirm', changepassword_confirm), ## GET
    (r'^changepassword/$', changepassword), ## POST
    (r'^reportabug/$', submit_bug_report), ## POST

    (r'^get_survey$', get_survey), ## POST
    (r'^post_survey/$', post_survey), ## POST
    (r'^done_survey/$', done_survey), ## POST
                       
    #(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'jv3/login.html', 'module_name':'jv3'}),
    #(r'^login$', login_view),                       
)
