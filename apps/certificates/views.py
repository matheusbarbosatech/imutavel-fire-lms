import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages

from .models import Certificate
from .utils import generate_certificate_pdf

# 🟢 IMPORT CORRIGIDO PARA A NOVA FUNÇÃO EM PDF
from .card_generator import generate_pvc_card_pdf

from apps.courses.models import CourseModel, StudentProgress, Lesson, Enrollment
from apps.quizzes.models import Quiz, QuizAttempt


@login_required
def emit_certificate(request, course_slug):
    """
    Verifica a elegibilidade do aluno e emite/exibe o certificado em PDF e a Carteirinha PVC.
    """
    course = get_object_or_404(CourseModel, slug=course_slug, is_active=True)
    get_object_or_404(Enrollment, student=request.user, course=course)

    # 1. Valida progresso de aulas
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = StudentProgress.objects.filter(
        student=request.user,
        lesson__module__course=course,
        completed=True
    ).count()

    is_lessons_complete = (total_lessons > 0) and (completed_lessons >= total_lessons)

    # 2. Valida aprovação no simulado (se existir)
    quiz = Quiz.objects.filter(course=course, is_active=True).first()
    has_passed_quiz = True
    if quiz:
        has_passed_quiz = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            passed=True
        ).exists()

    if not is_lessons_complete or not has_passed_quiz:
        return render(request, 'certificates/not_eligible.html', {
            'course': course,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'is_lessons_complete': is_lessons_complete,
            'has_passed_quiz': has_passed_quiz,
            'quiz': quiz
        })

    # 3. Cria ou recupera o certificado
    cert, created = Certificate.objects.get_or_create(
        student=request.user,
        course=course
    )

    base_url = f"{request.scheme}://{request.get_host()}"

    # Gera o PDF Vetorial se ainda não existir
    pdf_full_path = os.path.join(settings.MEDIA_ROOT, cert.pdf_file_path) if cert.pdf_file_path else None
    if not cert.pdf_file_path or not pdf_full_path or not os.path.exists(pdf_full_path):
        generate_certificate_pdf(cert, base_url=base_url)

    # 🟢 CHAMA A NOVA FUNÇÃO DE CARTEIRINHA EM PDF
    pvc_card_rel_path = generate_pvc_card_pdf(request.user, cert, base_url=base_url)

    return render(request, 'certificates/certificate_view.html', {
        'cert': cert,
        'course': course,
        'pvc_card_path': pvc_card_rel_path
    })


@login_required
def download_pvc_card(request, auth_code):
    """Gera e faz o download do PDF da Carteirinha PVC A4."""
    cert = get_object_or_404(Certificate, auth_code=auth_code, student=request.user)
    base_url = f"{request.scheme}://{request.get_host()}"
    
    # 🟢 CHAMA A NOVA FUNÇÃO DE CARTEIRINHA EM PDF
    card_rel_path = generate_pvc_card_pdf(request.user, cert, base_url=base_url)
    file_path = os.path.join(settings.MEDIA_ROOT, card_rel_path)

    if os.path.exists(file_path):
        # 🟢 RETORNA COMO APPLICATION/PDF
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf', filename=f"Carteirinha_{cert.auth_code}.pdf")
    else:
        raise Http404("O PDF da credencial PVC não pôde ser gerado.")


@login_required
def download_certificate_pdf(request, auth_code):
    """Permite ao aluno baixar o arquivo PDF do certificado."""
    cert = get_object_or_404(Certificate, auth_code=auth_code, student=request.user)
    
    if not cert.pdf_file_path:
        raise Http404("Arquivo de certificado não encontrado.")

    file_path = os.path.join(settings.MEDIA_ROOT, cert.pdf_file_path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf', filename=f"Certificado_{cert.auth_code}.pdf")
    else:
        raise Http404("Arquivo do PDF não foi localizado no servidor.")


@login_required
def my_documents(request):
    """Central 'Meus Documentos': exibe certificados e credenciais PVC."""
    certificates = Certificate.objects.filter(student=request.user).select_related('course')
    return render(request, 'certificates/my_documents.html', {
        'certificates': certificates
    })


def validate_certificate_public(request, auth_code):
    """Página Pública de Validação de Documentos."""
    cert = Certificate.objects.filter(auth_code=auth_code, is_valid=True).select_related('student', 'course').first()

    return render(request, 'certificates/validate_public.html', {
        'cert': cert,
        'auth_code': auth_code,
        'is_authentic': cert is not None
    })