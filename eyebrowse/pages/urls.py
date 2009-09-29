import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *
from eyebrowse.pages.views import *

urlpatterns = patterns('',
                       (r'^$', index),

                       # browsing
                       (r'^list/(\w+)/$', list),
                       (r'^days/(\w+)/$', day),
                       (r'^report/(\w+)/$', report),
                       (r'^graph/(\w+)/$', graph),
                       (r'^graphs/(\w+)/$', graph),
                       (r'^daybyday/(\w+)/$', daybyday),
                       #(r'^friends/(\w+)/$', friends),
                       (r'^users/$', users),
                       (r'^search/$', page_profile),
                       (r'^ticker/$', ticker),
                       
                       # user pages
                       (r'^profile/(\w+)/?$', user_page),
                       (r'^user/(\w+)?$', user_page),                       
                       (r'^friends/manage/(\w+)/$', friends_page),
                       (r'^friend/add$', friend_add),
                       (r'^friend/save$', friend_save),
                       (r'^friend/invite/$', friend_invite),
                       (r'^friend/accept/(\w+)/$', friend_accept),
                       (r'^friend/unfollow/(\w+)/$', friend_unfollow),
                       
                       # session management
                       (r'^login/$', 'django.contrib.auth.views.login'),
                       (r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       (r'^register/$', register_page),
                       (r'^register/success/$', register_success_page),
                       (r'^logout/$', logout_page),

                       # search
                       (r'^search/$', user_search_page),

                       # home
                       (r'^help/$', help),
                       (r'^about/$', about),
                       (r'^terms/$', terms),

                       # account management
                       (r'^profile_old/$', profile_save_page),
                       (r'^settings/$',  privacy_settings_page),
                       (r'^userprivacy/$', userprivacy),

                       # plugin iframe
                       (r'^iframe$', plugin_iframe),
)
