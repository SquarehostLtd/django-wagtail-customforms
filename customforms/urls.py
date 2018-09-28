from __future__ import absolute_import, unicode_literals

from django.urls import path

from . import views


app_name = 'customforms'
urlpatterns = [
    path('submit/<int:form_id>/', views.submit, name='submit'),
]
