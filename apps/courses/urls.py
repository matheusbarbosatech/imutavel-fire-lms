from django.urls import path
from . import views, api_views

app_name = 'courses'

urlpatterns = [
    path('dashboard/', views.student_dashboard_view, name='dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/toggle-complete/', views.toggle_lesson_completion_view, name='toggle_lesson_completion'),
    path('lesson/<int:lesson_id>/comment/', views.post_lesson_comment_view, name='post_lesson_comment'),
    
    # Endpoints de API REST Mobile & Sync
    path('api/courses/', api_views.api_courses_list, name='api_courses_list'),
    path('api/courses/create/', api_views.api_create_course, name='api_create_course'),
    path('api/lessons/<int:lesson_id>/', api_views.api_lesson_detail, name='api_lesson_detail'),
    path('api/sync-progress/', api_views.api_sync_progress, name='api_sync_progress'),
    
    # Endpoints de Autenticação Mobile (Login, Cadastro, Esqueci Senha)
    path('api/auth/login/', api_views.api_auth_login, name='api_auth_login'),
    path('api/auth/register/', api_views.api_auth_register, name='api_auth_register'),
    path('api/auth/forgot-password/', api_views.api_auth_forgot_password, name='api_auth_forgot_password'),
    
    # Endpoints de Secretaria Virtual e Documentos
    path('api/student/documents/', api_views.api_student_documents, name='api_student_documents'),

    # Endpoints REST para Admin, Financeiro & Instrutor
    path('api/admin/dashboard/', api_views.api_admin_dashboard, name='api_admin_dashboard'),
    path('api/admin/financial/', api_views.api_admin_financial, name='api_admin_financial'),
    path('api/admin/enrollment-toggle/', api_views.api_admin_toggle_enrollment, name='api_admin_toggle_enrollment'),
    path('api/instructor/dashboard/', api_views.api_instructor_dashboard, name='api_instructor_dashboard'),
    path('api/instructor/materials/', api_views.api_instructor_materials, name='api_instructor_materials'),
    
    # Download direto do APK
    path('download-app/', api_views.download_app_view, name='download_app'),
]