from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Module, Lesson, Enrollment


@login_required
def student_dashboard_view(request):
    """Painel do Aluno: Exibe todos os cursos e suas matrículas ativas."""
    if request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN':
        enrollments = Enrollment.objects.all().select_related('course')
        available_courses = Course.objects.all()
    else:
        enrollments = Enrollment.objects.filter(student=request.user, is_active=True).select_related('course')
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        available_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)

    context = {
        'enrollments': enrollments,
        'available_courses': available_courses,
    }
    return render(request, 'courses/student_dashboard.html', context)


@login_required
def course_detail_view(request, course_id):
    """Detalhes de um curso específico com seus módulos e aulas."""
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def lesson_detail_view(request, lesson_id):
    """Visualização da aula, conteúdo teórico, vídeo e material complementar."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    module = lesson.module
    course = module.course

    context = {
        'lesson': lesson,
        'module': module,
        'course': course,
    }
    return render(request, 'courses/lesson_detail.html', context)