from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('curso/<slug:slug>/', views.course_detail, name='course_detail'),
    path('aula/<int:pk>/', views.lesson_view, name='lesson_view'),
    path('instrutor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('api/progress/update/', views.api_progress_update, name='api_progress_update'),
]