from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('meus-certificados/', views.my_certificates_view, name='my_certificates'),
    path('validar/<str:code>/', views.verify_certificate_view, name='verify_certificate'),
]