from django.urls import path
from . import views

urlpatterns = [
    # A Landing Page agora é a tela principal
    path('', views.landing_page, name='landing_page'),
    
    # O formulário de matrícula mudou para /inscricao/
    path('inscricao/', views.passo_1, name='passo_1'),
    path('inscricao/2/', views.passo_2, name='passo_2'),
    path('inscricao/3/', views.passo_3, name='passo_3'),
    path('inscricao/4/', views.passo_4, name='passo_4'),
    path('inscricao/sucesso/', views.sucesso, name='sucesso'),
]