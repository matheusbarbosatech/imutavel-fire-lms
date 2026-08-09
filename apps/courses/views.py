from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Module, Lesson, Enrollment
import traceback


@login_required
def student_dashboard_view(request):
    """Painel do Aluno: Exibe todos os cursos e suas matrículas ativas."""
    try:
        user = request.user
        
        # Filtra as matrículas ativas do aluno
        enrollments = Enrollment.objects.filter(student=user, is_active=True).select_related('course')
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        available_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)

        context = {
            'enrollments': enrollments,
            'available_courses': available_courses,
        }
        return render(request, 'courses/student_dashboard.html', context)
    except Exception as e:
        print("❌ ERRO NO DASHBOARD DO ALUNO:")
        print(traceback.format_exc())
        
        # Fallback gracioso para evitar Erro 500
        all_courses = Course.objects.filter(is_active=True)
        return render(request, 'courses/student_dashboard.html', {
            'enrollments': [],
            'available_courses': all_courses
        })


@login_required
def course_detail_view(request, course_id):
    """Detalhes de um curso específico com seus módulos e aulas."""
    try:
        course = get_object_or_404(Course, id=course_id)
        modules = course.modules.all().prefetch_related('lessons')
        
        context = {
            'course': course,
            'modules': modules,
        }
        return render(request, 'courses/course_detail.html', context)
    except Exception as e:
        print("❌ ERRO NO DETALHE DO CURSO:")
        print(traceback.format_exc())
        return redirect('courses:student_dashboard')


@login_required
def lesson_detail_view(request, lesson_id):
    """Visualização da aula, conteúdo teórico, vídeo, material complementar e avaliação."""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        module = lesson.module
        course = module.course
        quiz = getattr(lesson, 'quiz', None)

        context = {
            'lesson': lesson,
            'module': module,
            'course': course,
            'quiz': quiz,
        }
        return render(request, 'courses/lesson_detail.html', context)
    except Exception as e:
        print("❌ ERRO NO DETALHE DA AULA:")
        print(traceback.format_exc())
        return redirect('courses:student_dashboard')