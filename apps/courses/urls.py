from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('dashboard/', views.student_dashboard_view, name='dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail_view, name='lesson_detail'),
    path('lesson/<int:lesson_id>/toggle-complete/', views.toggle_lesson_completion_view, name='toggle_lesson_completion'),
    path('lesson/<int:lesson_id>/comment/', views.post_lesson_comment_view, name='post_lesson_comment'),
]