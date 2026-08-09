from django.contrib import admin
from .models import StudentQuizAttempt


@admin.register(StudentQuizAttempt)
class StudentQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('course', 'module', 'lesson', 'score', 'passed', 'created_at')
    list_filter = ('passed', 'course')
    search_fields = ('course__title',)