import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from eyebrowse.views import *
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *

admin.autodiscover()

lib = os.path.join(
    os.path.dirname(__file__), 'lib'
)

profile_uploads = os.path.join(
    os.path.dirname(__file__), 'profiles'
)

urlpatterns = patterns('',
                       url(r'^$', index),

                       # browsing
                       (r'^list/$', list),
                       (r'^days/$', day),
                       (r'^report/$', report),
                       (r'^graph/$', graph),

                       # user pages
                       (r'^user/(\w+)/$', user_page),
                       (r'^friends/(\w+)/$', friends_page),
                       (r'^friend/add/$', friend_add),
                       (r'^friend/invite/$', friend_invite),
                       (r'^friend/accept/(\w+)/$', friend_accept),

                       # session management
                       (r'^login/$', 'django.contrib.auth.views.login'),#login_page),
                       (r'^accounts/login/$', 'django.contrib.auth.views.login'),#login_page),
                       (r'^register/$', register_page),
                       (r'^register/success/$', direct_to_template,
                        { 'template': 'registration/register_success.html' }),
                       (r'^logout/$', logout_page),

                       # search
                       (r'^search/$', user_search_page),

                       # ajax
                       (r'^get_views$', get_web_page_views),
                       (r'^get_time_per_page$', get_time_per_page),
                       (r'^get_top_pages/(\w+)/(\d+)/$', get_top_pages),

                       # home
                       (r'^faq/$', faq),

                       # account management
                       (r'^profile/(\w+)/$', profile_save_page),

                       (r'^lib/(?P<path>.*)$', 'django.views.static.serve',
                        { 'document_root': lib }),

                       (r'^uploads/(?P<path>.*)$', 'django.views.static.serve',
                        { 'document_root': profile_uploads }),

                       # admin
                       #  (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       #  (r'^admin/', include(admin.site.urls)),
)
