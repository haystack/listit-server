from django.conf.urls.defaults import *
from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import *
from django_restapi.receiver import *
from server.jv3.models import SPO
from server.jv3.views import SPOCollection

fullxml_spo_resource = Collection(
    queryset = SPO.objects.all(), 
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ['subj', 'pred', 'obj'],
    receiver = XMLReceiver(),
    responder = XMLResponder(),
)
fulljson_spo_resource = Collection(
    queryset = SPO.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    expose_fields = ['subj', 'pred', 'obj'],
    receiver = JSONReceiver(),
    responder = JSONResponder()
)

def filtered_xml_resource(queryset):
    return Collection(
        queryset=queryset,
        permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
        expose_fields = ['subj', 'pred', 'obj'],
        receiver=XMLReceiver(),
        responder=XMLResponder())
def filtered_json_resource(queryset):
    return Collection(
        queryset=queryset,
        permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
        expose_fields = ['subj', 'pred', 'obj'],
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
)
