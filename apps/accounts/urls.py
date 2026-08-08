from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Autenticação e Sessão
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),

    # Perfil, Documentos de Matrícula e Declarações Institucionais
    path('perfil/', views.profile_view, name='profile'),
    path('declaracao/<str:doc_type_code>/', views.download_declaration, name='download_declaration'),
]