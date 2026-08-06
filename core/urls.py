from django.urls import path
from . import views

urlpatterns = [
    path('', views.passo_1, name='passo_1'),        # Página inicial
    path('2/', views.passo_2, name='passo_2'),      # Passo 2: Contato
    path('3/', views.passo_3, name='passo_3'),      # Passo 3: Documentos
    path('4/', views.passo_4, name='passo_4'),      # Passo 4: Assinatura
    path('sucesso/', views.sucesso, name='sucesso'), # Página de sucesso
]