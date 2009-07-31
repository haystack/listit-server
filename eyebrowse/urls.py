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
                       (r'^list/(\w+)/$', list),
                       (r'^days/(\w+)/$', day),
                       (r'^report/(\w+)/$', report),
                       (r'^graph/(\w+)/$', graph),

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
                       (r'^get_views_user/(\w+)/$', get_web_page_views_user),
                       (r'^get_time_per_page$', get_time_per_page),
                       #(r'^get_top_pages/(\w+)/$', get_top_pages),
                       (r'^get_top_pages/(\w+)/(\d+)/$', get_top_pages),
                       (r'^get_top_hosts_comparison/(\w+)/(\d+)/$', get_top_hosts_comparison),
                       (r'^get_users_most_recent_urls/(\w+)/(\d+)/$', get_users_most_recent_urls),
                       # homepage ajax
                       (r'^get_most_recent_urls/(\d+)/$', get_most_recent_urls),
                       (r'^get_trending_urls/(\d+)/$', get_trending_urls),
                       (r'^get_top_urls/(\d+)/$', get_top_urls),

                       # home
                       (r'^help/$', help),
                       (r'^about/$', about),
                       (r'^moreinfo/$', moreinfo),
                       (r'^terms/$', terms),

                       # account management
                       (r'^profile/(\w+)/$', profile_save_page),
                       (r'^settings/(\w+)/$',  privacy_settings_page),

                       (r'^lib/(?P<path>.*)$', 'django.views.static.serve',
                        { 'document_root': lib }),

                       (r'^uploads/(?P<path>.*)$', 'django.views.static.serve',
                        { 'document_root': profile_uploads }),

                       # admin
                       #  (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       #  (r'^admin/', include(admin.site.urls)),

                       #TEMPORARY
                       (r'^pluginhover/$', pluginhover),  
                       (r'^pluginlogin/$', pluginlogin),  
)
