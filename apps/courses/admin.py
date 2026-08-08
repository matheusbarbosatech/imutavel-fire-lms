from django.contrib import admin
from .models import CourseModel, Module, Lesson, Enrollment, StudentProgress

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1

@admin.register(CourseModel)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'workload_hours', 'min_passing_score', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title']
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'content_type', 'duration_seconds', 'order']
    list_filter = ['content_type', 'module__course']
    search_fields = ['title', 'youtube_video_id']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_at']
    list_filter = ['status', 'course']
    search_fields = ['student__username', 'student__cpf', 'student__email']

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'watched_seconds', 'completed', 'last_accessed_at']
    list_filter = ['completed']
    search_fields = ['student__username', 'lesson__title']