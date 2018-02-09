from __future__ import absolute_import, unicode_literals

from django.urls import path

from . import views


app_name = 'customforms'
urlpatterns = [
    path('', views.index, name='index'),
    path('submissions/<int:page_id>/', views.list_submissions, name='list_submissions'),
    path('submissions/<int:page_id>/delete/', views.delete_submissions, name='delete_submissions')
]
