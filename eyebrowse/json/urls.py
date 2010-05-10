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

                       (r'^get_homepage$', get_homepage),    
                       (r'^get_users_page$', get_users_page),                      
                       (r'^get_profile$', get_profile),                                            

                       (r'^get_trending_sites$', get_trending_sites),                       
                       (r'^get_latest_sites_for_filter$', get_latest_sites_for_filter),                       
                       (r'^get_top_users_for_filter$', get_top_users_for_filter),                       

                       (r'^get_latest_views$', get_latest_views),

                       #(r'^get_plugin_stats$', get_plugin_stats),                       
                       #(r'^get_pagestats$', get_pagestats),                       
                       #(r'^get_closest_url/$', get_closest_url),
                       #(r'^get_hourly_daily_top_urls_user/(\w+)/(\d+)/$', get_hourly_daily_top_urls_user), # graphs
                       #(r'^get_JSON_top_and_trending_pages$', get_JSON_top_and_trending_pages), # plugin 
                       #(r'^get_JSON_eyebrowse_social_page$', get_JSON_eyebrowse_social_page), # plugin 
                       #(r'^get_to_from_url/(\d+)/$', get_to_from_url_plugin), #for plugin                   
)

    
