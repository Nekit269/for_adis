from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views


urlpatterns = [
    #re_path(r'^message$', views.pprint),
    #re_path(r'^$', views.home),
    #path('admin/', admin.site.urls),
    #path(r'', views.home),
    re_path(r'^message$', views.message),
    re_path(r'^login$', views.login),
    re_path(r'^create_account$', views.registration),
    re_path(r'^save_history$', views.save_history),
    re_path(r'^load_history$', views.load_history),
    re_path(r'^save_settings$', views.save_settings),
    re_path(r'^load_settings$', views.load_settings),
]