from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('meus-certificados/', views.my_certificates_view, name='my_certificates'),
    path('validar/<str:code>/', views.verify_certificate_view, name='verify_certificate'),
    path('download-pdf/<int:certificate_id>/', views.download_certificate_pdf_view, name='download_pdf'),
    path('pvc-card/<int:certificate_id>/', views.download_pvc_card_view, name='download_pvc_card'),
]