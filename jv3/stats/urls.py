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
from jv3.stats.stats import *

urlpatterns = patterns('jv3.stats',
    (r'^summary/(?P<startyear>\d{4})-(?P<startmonth>\d{2})-(?P<startday>\d+)$', summary),
    (r'^summary/(?P<startyear>\d{4})-(?P<startmonth>\d{2})-(?P<startday>\d+)/(?P<endyear>\d{4})-(?P<endmonth>\d{2})-(?P<endday>\d+)$', summary)
)

for fn in jv3.stats.stats.EXPORTS:
    urlpatterns += patterns('',(fn['name'], fn['fn']))
    print "urlpatterns %s " % repr((fn['name'], fn['fn']))
