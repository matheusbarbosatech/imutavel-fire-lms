from django.contrib import admin
from .models import Quiz, Question, Option, QuizAttempt

class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'module', 'passing_score', 'is_active']
    list_filter = ['course', 'is_active']
    search_fields = ['title']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'text']
    list_filter = ['quiz']
    inlines = [OptionInline]

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'passed', 'completed_at']
    list_filter = ['passed', 'quiz']
    search_fields = ['student__username', 'student__cpf']