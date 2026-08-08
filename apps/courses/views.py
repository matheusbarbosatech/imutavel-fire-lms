import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import CourseModel, Enrollment, Module, Lesson, StudentProgress, Comment
from apps.certificates.models import Certificate
from apps.accounts.models import Notification


@login_required
def student_dashboard(request):
    """
    Dashboard do aluno com os cursos matriculados, notificações e
    alerta de certificados/reciclagens que vencem em até 30 dias.
    """
    user = request.user
    enrollments = Enrollment.objects.filter(student=user).select_related('course')

    # Alerta de Vencimento de Reciclagem (Certificados que expiram nos próximos 30 dias)
    now = timezone.now()
    in_30_days = now + timedelta(days=30)
    expiring_certificates = Certificate.objects.filter(
        student=user,
        expires_at__range=[now, in_30_days],
        is_valid=True
    ).select_related('course')

    unread_notifications = Notification.objects.filter(user=user, is_read=False)

    return render(request, 'courses/student_dashboard.html', {
        'enrollments': enrollments,
        'expiring_certificates': expiring_certificates,
        'unread_notifications': unread_notifications
    })


@login_required
def course_detail(request, slug):
    """
    Grade curricular do curso com módulos, aulas e progresso do aluno.
    """
    course = get_object_or_404(CourseModel, slug=slug, is_active=True)
    get_object_or_404(Enrollment, student=request.user, course=course)

    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    completed_lesson_ids = set(
        StudentProgress.objects.filter(student=request.user, completed=True).values_list('lesson_id', flat=True)
    )

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids
    })


@login_required
def lesson_view(request, pk):
    """
    Player de aula com suporte a vídeo/PDF/texto, marcação de conclusão e fórum de dúvidas.
    """
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    get_object_or_404(Enrollment, student=request.user, course=course)

    progress, _ = StudentProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    # Conclusão Manual da Aula
    if request.method == 'POST' and 'toggle_complete' in request.POST:
        progress.completed = not progress.completed
        if progress.completed and progress.watched_seconds == 0:
            progress.watched_seconds = lesson.duration_seconds
        progress.save()
        messages.success(request, 'Status da aula atualizado!')
        return redirect('courses:lesson_view', pk=lesson.id)

    # Envio de Dúvida/Comentário no Fórum da Aula
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_text = request.POST.get('comment_text', '').strip()
        parent_id = request.POST.get('parent_id', None)
        parent_comment = Comment.objects.filter(pk=parent_id).first() if parent_id else None

        if comment_text:
            Comment.objects.create(
                lesson=lesson,
                user=request.user,
                parent=parent_comment,
                text=comment_text
            )
            messages.success(request, 'Sua dúvida foi publicada no fórum!')
            return redirect('courses:lesson_view', pk=lesson.id)

    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    completed_lesson_ids = set(
        StudentProgress.objects.filter(student=request.user, completed=True).values_list('lesson_id', flat=True)
    )

    all_lessons = list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order'))
    current_index = all_lessons.index(lesson)
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None

    comments = lesson.comments.filter(parent__isnull=True).select_related('user').prefetch_related('replies__user')

    return render(request, 'courses/lesson_view.html', {
        'lesson': lesson,
        'course': course,
        'progress': progress,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'comments': comments
    })


@csrf_exempt
@login_required
def api_progress_update(request):
    """
    API para atualização automática de tempo assistido / progresso via AJAX.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            watched_seconds = data.get('watched_seconds', 0)

            lesson = get_object_or_404(Lesson, pk=lesson_id)
            progress, _ = StudentProgress.objects.get_or_create(
                student=request.user,
                lesson=lesson
            )

            if watched_seconds > progress.watched_seconds:
                progress.watched_seconds = watched_seconds

            # Se assistiu mais de 90% da aula, marca automaticamente como concluída
            if lesson.duration_seconds > 0 and (progress.watched_seconds / lesson.duration_seconds) >= 0.9:
                progress.completed = True

            progress.save()
            return JsonResponse({'status': 'success', 'completed': progress.completed})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid method'}, status=405)


@login_required
def instructor_dashboard(request):
    """
    Painel de acompanhamento do instrutor/administrador.
    """
    if request.user.role not in ['INSTRUCTOR', 'ADMIN'] and not request.user.is_staff:
        messages.error(request, 'Acesso restrito a instrutores e administradores.')
        return redirect('courses:student_dashboard')

    courses = CourseModel.objects.all()
    return render(request, 'courses/instructor_dashboard.html', {
        'courses': courses
    })