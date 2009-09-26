import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from eyebrowse.json.views import *

urlpatterns = patterns('',
                       (r'^get_views_user/(\w+)/$', get_views_user_json),
                       (r'^get_most_shared_hosts/(\d+)/$', get_most_shared_hosts),
                       (r'^get_recent_web_page_views_user/(\w+)/(\d+)/$', get_recent_web_page_view_user),
                       (r'^get_most_recent_urls/(\d+)/$', get_most_recent_urls),
                       (r'^get_top_users_for_url/(\d+)/$', get_top_users_for_url),
                       (r'^get_hourly_daily_top_urls_user/(\w+)/(\d+)/$', get_hourly_daily_top_urls_user),
                       (r'^get_following_views/(\w+)/$', get_following_views),
                       (r'^get_top_hosts_comparison_friends/(\w+)/(\d+)/$', get_top_hosts_comparison_friends),

                       (r'^get_closest_url/$', get_closest_url),

                       (r'^get_homepage$', get_homepage),    
                       (r'^get_ticker$', get_ticker),                      
                       (r'^get_users_page$', get_users_page),                      
                       (r'^get_profile$', get_profile),                                            
                       (r'^get_pagestats$', get_pagestats),                       

                       (r'^get_to_from_url/(\d+)/$', get_to_from_url_plugin), #for old plugin                     
)

    
