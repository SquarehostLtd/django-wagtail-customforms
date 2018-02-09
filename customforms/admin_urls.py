from django.urls import path

#from .views import chooser, forms, multiple
from . import views

app_name = 'customforms'
urlpatterns = [
    path('', views.index, name='index'),
    path('submit/<int:form_id>/', views.submit, name='submit'),
    path('submissions/<int:page_id>/', views.list_submissions, name='list_submissions'),
    path('submissions/<int:page_id>/delete/', views.delete_submissions, name='delete_submissions'),

    path('chooser/', views.chooser, name='chooser'),
    path('chooser/<int:form_id>/', views.form_chosen, name='form_chosen'),
    path('chooser/upload/', views.chooser_upload, name='chooser_upload'),
]
