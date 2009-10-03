import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from eyebrowse.json.views import *

urlpatterns = patterns('',
                       (r'^get_most_shared_hosts/(\d+)/$', get_most_shared_hosts), # settings page

                       (r'^get_closest_url/$', get_closest_url),

                       (r'^get_homepage$', get_homepage),    
                       (r'^get_ticker$', get_ticker),                      
                       (r'^get_users_page$', get_users_page),                      
                       (r'^get_profile$', get_profile),                                            
                       (r'^get_pagestats$', get_pagestats),                       
                       (r'^get_pulse$', get_pulse),                       

                       (r'^get_latest_views$', get_latest_views), # graphs
                       (r'^get_to_from_url/(\d+)/$', get_to_from_url_plugin), #for plugin                     
                       (r'^get_views_user/(\w+)/$', get_views_user_json), # for graphs 
                       (r'^get_hourly_daily_top_urls_user/(\w+)/(\d+)/$', get_hourly_daily_top_urls_user), # graphs
                       #(r'^get_top_friend_and_number_friends_for_url/(\w+)$', get_top_friend_and_number_friends_for_url), # test
)

    
