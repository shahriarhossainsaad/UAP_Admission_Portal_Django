# admissions/urls.py
from django.urls import path
from . import views

app_name = 'admission'

urlpatterns = [
    path('', views.index, name='index'),
    path('info/', views.admission_info, name='admission_info'),             # /info/
    path('apply/', views.admission_online, name='admission_online'),       # /apply/
    path('apply/submit/', views.application_create, name='application_create'),  # POST target
    path('application/<uuid:pk>/', views.application_detail, name='application_detail'),

    # staff actions
    path('application/<uuid:pk>/accept/', views.accept_applicant, name='accept_applicant'),
    path('application/<uuid:pk>/reject/', views.reject_applicant, name='reject_applicant'),

    # auth
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
