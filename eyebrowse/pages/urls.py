import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import *
from eyebrowse.pages.views import *
from eyebrowse.pages.export import *

urlpatterns = patterns('',
                       (r'^$', index),

                       # browsing
                       #(r'^list/(\w+)/$', list),
                       #(r'^report/(\w+)/$', report),
                       #(r'^daybyday/(\w+)/$', daybyday),
                       #(r'^friends/(\w+)/$', friends),
               
                       (r'^days/(\w+)/?$', day),
                       (r'^graph/(\w+)/?$', graph),
                       (r'^pulse/?$', pulse),
                       (r'^graphs/(\w+)/$', graph),
                       (r'^users/?$', users),
                       (r'^search/?$', page_profile),
                       (r'^pathways/?$', page_profile),
                       (r'^ticker/?$', ticker),
                       
                       # user pages
                       (r'^profile/(\w+)/?$', user_page),
                       (r'^lifestream/?$', localviz),
                       (r'^addfeeds/?$', addfeeds),
                       (r'^user/(\w+)/?$', user_page),                       
                       (r'^friends/manage/(\w+)/?$', friends_page),
                       (r'^friend/add$', friend_add),
                       (r'^friend/save$', friend_save),
                       (r'^friend/invite/$', friend_invite),
                       (r'^friend/accept/(\w+)/$', friend_accept),
                       (r'^friend/unfollow/(\w+)/$', friend_unfollow),
                       
                       # session management
                       (r'^login/?$', 'django.contrib.auth.views.login'),
                       (r'^accounts/login/?$', 'django.contrib.auth.views.login'),
                       (r'^register/?$', register_page),
                       (r'^register/success/?$', register_success_page),
                       (r'^logout/?$', logout_page),

                       # search
                       #(r'^search/$', user_search_page),

                       # home
                       (r'^help/?$', help),
                       (r'^about/?$', about),
                       (r'^terms/?$', terms),

                       # account management
                       (r'^profile_old/?$', profile_save_page),
                       (r'^settings/?$',  privacy_settings_page),
                       (r'^accounts/profile/?$',  privacy_settings_page),
                       #(r'^userprivacy/?$', userprivacy),

                       # plugin
                       (r'^iframe/?$', plugin_iframe),
                       (r'^newtab/?$', new_tab),

                       # zamiang browser
                       (r'^zamiang/?$', zamiang_browser),

                       # export
                       (r'^my_eyebrowse_data.zip$', get_user_pageviews_as_csv_view)
)
