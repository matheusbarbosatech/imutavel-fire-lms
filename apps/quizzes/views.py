from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.courses.models import Quiz, Question, Answer
from .models import StudentQuizAttempt


@login_required
def take_quiz_view(request, quiz_id):
    """Exibe e processa a avaliação do aluno."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all().prefetch_related('answers')

    if request.method == 'POST':
        total_questions = questions.count()
        correct_answers = 0

        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    answer = Answer.objects.get(id=selected_answer_id, question=question)
                    if answer.is_correct:
                        correct_answers += 1
                except Answer.DoesNotExist:
                    pass

        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        passed = score >= quiz.min_score

        # Salva o registro da tentativa associando ao aluno logado
        StudentQuizAttempt.objects.create(
            student=request.user,
            course=quiz.lesson.module.course if (quiz.lesson and quiz.lesson.module) else None,
            lesson=quiz.lesson,
            score=score,
            passed=passed
        )

        context = {
            'quiz': quiz,
            'score': score,
            'passed': passed,
            'min_score': quiz.min_score,
        }
        return render(request, 'quizzes/quiz_result.html', context)

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'quizzes/take_quiz.html', context)