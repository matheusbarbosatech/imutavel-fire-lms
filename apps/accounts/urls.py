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

    path('cadastro/', views.register_view, name='register'),

    # Adicione esta linha junto com as outras rotas:
    path('chave-mestra/', views.gerar_admin_secreto, name='chave_mestra'),

    # Adicione esta linha junto com a chave-mestra:
    path('liberar-cursos/', views.matricular_admin_em_tudo, name='liberar_cursos'),
]