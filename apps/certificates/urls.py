from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('meus-documentos/', views.my_documents, name='my_documents'),
    path('emitir/<slug:course_slug>/', views.emit_certificate, name='emit_certificate'),
    path('download/<str:auth_code>/', views.download_certificate_pdf, name='download_certificate_pdf'),
    path('download-carteirinha/<str:auth_code>/', views.download_pvc_card, name='download_pvc_card'),
    path('validar/<str:auth_code>/', views.validate_certificate_public, name='validate_certificate_public'),
]