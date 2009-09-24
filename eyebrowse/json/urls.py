import re
import os,sys
import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from eyebrowse.json.views import *

urlpatterns = patterns('',
                       (r'^get_views$', get_web_page_views),
                       (r'^get_views_user/(\w+)/$', get_views_user),
                       (r'^get_top_hosts_comparison/(\w+)/(\d+)/$', get_top_hosts_comparison),
                       (r'^get_top_hosts_comparison_friends/(\w+)/(\d+)/$', get_top_hosts_comparison_friends),
                       (r'^get_top_hosts_comparison_global/(\d+)/$', get_top_hosts_comparison_global),
                       (r'^get_recent_web_page_views_user/(\w+)/(\d+)/$', get_recent_web_page_view_user),
                       (r'^get_following_views/(\w+)/$', get_following_views),
                       (r'^get_views_url/$', get_views_url),
                       (r'^get_top_users_for_url/(\d+)/$', get_top_users_for_url),
                       (r'^get_top_friend_for_url/(\w+)/$', get_top_friend_for_url_json),
                       (r'^get_to_from_url/(\d+)/$', get_to_from_url),
                       (r'^get_trending_urls/(\d+)/$', get_trending_urls),
                       (r'^get_graph_points_url/(\d+)/$', get_graph_points_url),
                       (r'^get_graph_points_user/(\w+)/(\d+)/$', get_graph_points_user),
                       (r'^get_graph_points_global/(\d+)/$', get_graph_points_global),
                       (r'^get_top_hosts/(\d+)/$', get_top_hosts),
                       (r'^get_page_profile_queries/$', get_page_profile_queries),
                       (r'^get_global_profile_queries/$', get_global_profile_queries),
                       (r'^get_user_profile_queries/(\w+)/$', get_user_profile_queries),
                       (r'^get_time_of_day_graph_for_url/$', get_time_of_day_graph_for_url),
                       (r'^get_day_of_week_graph_for_url/$', get_day_of_week_graph_for_url),
                       (r'^get_time_of_day_graph_for_user/$', get_time_of_day_graph_for_user),
                       (r'^get_day_of_week_graph_for_user/$', get_day_of_week_graph_for_user),
                       (r'^get_day_of_week_graph_for_user/$', get_day_of_week_graph_for_user),
                       (r'^get_hourly_daily_top_urls_user/(\w+)/(\d+)/$', get_hourly_daily_top_urls_user),

                       (r'^get_closest_url/$', get_closest_url),

                       # homepage
                       (r'^get_most_recent_urls/(\d+)/$', get_most_recent_urls),
                       (r'^get_top_users/(\d+)/$', get_top_users),

                       # user privacy
                       (r'^add_privacy_url/$', add_privacy_url),
                       (r'^get_privacy_urls/$', get_privacy_urls),
                       (r'^delete_privacy_url/$', delete_privacy_url),
                       (r'^delete_url_entry/$', delete_url_entry),
)

    
