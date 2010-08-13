from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django_restapi.responder import *



admin.autodiscover()

urlpatterns = patterns('')

if settings.LISTIT_SERVER:
    print "adding listit server"
    if not settings.DEVELOPMENT:
        ## deployment
        print "DEPLOY"
        urlpatterns = patterns('',
                               (r'^jv3/', include('jv3.urls')),
                               (r'^plum/', include('plum.urls')))
    else:
        import jv3.urls
        print "DEVELOP"
        ## development
        urlpatterns = patterns('',
                               (r'^listit/jv3/', include('jv3.urls')),
                               (r'^listit/plum/', include('plum.urls')))

        ## stats server is only available in development mode
        if hasattr(settings,"STATS_SERVER") and settings.STATS_SERVER:
            urlpatterns += patterns('', (r'^listit/stats/', include('jv3.stats.urls')))

if hasattr(settings,"EYEBROWSE_SERVER") and settings.EYEBROWSE_SERVER:
    import eyebrowse.urls
    print "enabling eyebrowse"
    urlpatterns += eyebrowse.urls.urlpatterns

if settings.DEVELOPMENT:
    ## add these at the end to lower priorities
    urlpatterns += patterns('',
                            (r'^admin/login/$', 'django.contrib.auth.views.login'), # login only used for special admin purposes
                            (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                            (r'^admin/(.*)', admin.site.root),
                            (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}))        
