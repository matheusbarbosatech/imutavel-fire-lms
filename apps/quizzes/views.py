import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Quiz, Question, Option, QuizAttempt
from apps.certificates.models import Certificate
from apps.certificates.utils import generate_certificate_pdf
from apps.accounts.models import Badge, UserBadge, Notification


@login_required
def take_quiz(request, quiz_id):
    """
    Processa a realização do simulado, calcula a nota, exibe o gabarito detalhado
    com justificativa, emite o certificado em PDF e atribui conquistas (badges).
    (Envio de e-mail removido do projeto).
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    questions = list(quiz.questions.all().prefetch_related('options'))

    if request.method == 'POST':
        correct_count = 0
        total_questions = len(questions)
        detailed_feedback = []

        for question in questions:
            selected_option_id = request.POST.get(f'question_{question.id}')
            selected_option = Option.objects.filter(pk=selected_option_id).first() if selected_option_id else None
            correct_option = question.options.filter(is_correct=True).first()

            is_correct = selected_option and selected_option.is_correct
            if is_correct:
                correct_count += 1

            detailed_feedback.append({
                'question': question,
                'selected_option': selected_option,
                'correct_option': correct_option,
                'is_correct': is_correct
            })

        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        passed = score >= quiz.passing_score

        # Registra a tentativa no banco de dados
        QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            passed=passed
        )

        # Se aprovado, gera certificado e badges
        if passed:
            cert, created = Certificate.objects.get_or_create(student=request.user, course=quiz.course)
            base_url = f"{request.scheme}://{request.get_host()}"
            generate_certificate_pdf(cert, base_url=base_url)

            # 1. Notificação em Tela no Sistema
            Notification.objects.create(
                user=request.user,
                title="Certificado Liberado!",
                message=f"Você foi aprovado no simulado do curso {quiz.course.title} com nota {score:.1f}%!",
                icon="bi-award-fill"
            )

            # 2. Gamificação / Concessão Automática de Badges
            badge_course, _ = Badge.objects.get_or_create(
                code="FIRST_COURSE",
                defaults={
                    'name': "Operacional Formado",
                    'description': "Concluiu seu primeiro treinamento profissional.",
                    'icon_class': "bi-trophy-fill"
                }
            )
            UserBadge.objects.get_or_create(user=request.user, badge=badge_course)

            if score == 100:
                badge_perfect, _ = Badge.objects.get_or_create(
                    code="PERFECT_SCORE",
                    defaults={
                        'name': "Gabarito Perfeito",
                        'description': "Atingiu 100% de aproveitamento no simulado final.",
                        'icon_class': "bi-star-fill"
                    }
                )
                UserBadge.objects.get_or_create(user=request.user, badge=badge_perfect)

        # Busca o histórico para exibir na tela (caso tenha falhado antes)
        attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-completed_at')

        return render(request, 'quizzes/quiz_result.html', {
            'quiz': quiz,
            'score': score,
            'passed': passed,
            'detailed_feedback': detailed_feedback,
            'attempts': attempts
        })

    attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-completed_at')

    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'attempts': attempts
    })