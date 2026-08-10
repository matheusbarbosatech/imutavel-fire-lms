from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Module, Lesson, Enrollment, LessonProgress, LessonComment, Quiz
from apps.certificates.utils import issue_certificate_for_user
import traceback


@login_required
def student_dashboard_view(request):
    """Painel do Aluno: Exibe todos os cursos, matrículas ativas e progresso real."""
    try:
        user = request.user
        enrollments = Enrollment.objects.filter(student=user, is_active=True).select_related('course')
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        available_courses = Course.objects.filter(is_active=True).exclude(id__in=enrolled_course_ids)

        enrollments_data = []
        for enrollment in enrollments:
            course = enrollment.course
            total_lessons = Lesson.objects.filter(module__course=course).count()
            completed_lessons = LessonProgress.objects.filter(
                student=user, 
                lesson__module__course=course, 
                completed=True
            ).count()
            
            percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
            
            # Se completou 100% das aulas, assegura emissão do certificado
            if percentage == 100 and total_lessons > 0:
                issue_certificate_for_user(user, course)

            enrollments_data.append({
                'enrollment': enrollment,
                'course': course,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percentage': percentage,
            })

        context = {
            'enrollments_data': enrollments_data,
            'enrollments': enrollments,
            'available_courses': available_courses,
        }
        return render(request, 'courses/student_dashboard.html', context)
    except Exception as e:
        print("❌ ERRO NO DASHBOARD DO ALUNO:")
        print(traceback.format_exc())
        all_courses = Course.objects.filter(is_active=True)
        return render(request, 'courses/student_dashboard.html', {
            'enrollments_data': [],
            'enrollments': [],
            'available_courses': all_courses
        })


@login_required
def course_detail_view(request, course_id):
    """Detalhes de um curso específico com seus módulos, aulas e status de conclusão."""
    try:
        course = get_object_or_404(Course, id=course_id)
        modules = course.modules.all().prefetch_related('lessons')
        
        user_completed_lesson_ids = set(
            LessonProgress.objects.filter(
                student=request.user, 
                lesson__module__course=course, 
                completed=True
            ).values_list('lesson_id', flat=True)
        )

        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_count = len(user_completed_lesson_ids)
        progress_percentage = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

        context = {
            'course': course,
            'modules': modules,
            'user_completed_lesson_ids': user_completed_lesson_ids,
            'progress_percentage': progress_percentage,
            'total_lessons': total_lessons,
            'completed_count': completed_count,
        }
        return render(request, 'courses/course_detail.html', context)
    except Exception as e:
        print("❌ ERRO NO DETALHE DO CURSO:")
        print(traceback.format_exc())
        return redirect('courses:student_dashboard')


@login_required
def lesson_detail_view(request, lesson_id):
    """Visualização da aula, vídeo, material complementar, avaliação e dúvidas."""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        module = lesson.module
        course = module.course
        quiz = Quiz.objects.filter(lesson=lesson).first()

        progress, _ = LessonProgress.objects.get_or_create(
            student=request.user, 
            lesson=lesson
        )

        comments = lesson.comments.select_related('user').all()

        # Obter todas as aulas do curso em ordem cronológica para determinar Aula Anterior e Próxima Aula
        all_lessons = list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id'))
        prev_lesson = None
        next_lesson = None

        for idx, l in enumerate(all_lessons):
            if l.id == lesson.id:
                if idx > 0:
                    prev_lesson = all_lessons[idx - 1]
                if idx < len(all_lessons) - 1:
                    next_lesson = all_lessons[idx + 1]
                break

        context = {
            'lesson': lesson,
            'module': module,
            'course': course,
            'quiz': quiz,
            'is_completed': progress.completed,
            'comments': comments,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
        }
        return render(request, 'courses/lesson_detail.html', context)
    except Exception as e:
        print("❌ ERRO NO DETALHE DA AULA:")
        print(traceback.format_exc())
        messages.error(request, f"Erro ao acessar a aula: {e}")
        return redirect('courses:student_dashboard')


@login_required
def toggle_lesson_completion_view(request, lesson_id):
    """Alterna o status de conclusão da aula pelo aluno."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress, created = LessonProgress.objects.get_or_create(
        student=request.user, 
        lesson=lesson
    )
    progress.completed = not progress.completed
    progress.save()

    if progress.completed:
        messages.success(request, f'Aula "{lesson.title}" marcada como concluída!')
        
        # Verifica se o curso foi 100% concluído
        course = lesson.module.course
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = LessonProgress.objects.filter(
            student=request.user, 
            lesson__module__course=course, 
            completed=True
        ).count()
        if completed_lessons == total_lessons and total_lessons > 0:
            issue_certificate_for_user(request.user, course)
            messages.info(request, f'🎉 Parabéns! Você concluiu 100% do curso "{course.title}" e seu certificado foi gerado!')
    else:
        messages.info(request, f'Aula "{lesson.title}" desmarcada.')

    return redirect('courses:lesson_detail', lesson_id=lesson.id)


@login_required
def post_lesson_comment_view(request, lesson_id):
    """Permite ao aluno postar uma dúvida/comentário na aula."""
    if request.method == 'POST':
        text = request.POST.get('comment_text', '').strip()
        if text:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            LessonComment.objects.create(
                lesson=lesson,
                user=request.user,
                text=text
            )
            messages.success(request, 'Sua dúvida/comentário foi enviada com sucesso!')
    return redirect('courses:lesson_detail', lesson_id=lesson_id)