from django.conf.urls import url

from . import views

app_name='analyzer'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^parse/$', views.index, name='parse')
]
