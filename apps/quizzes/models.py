from django.db import models
from django.conf import settings
from apps.courses.models import CourseModel, Module


class Quiz(models.Model):
    course = models.ForeignKey(
        CourseModel, 
        on_delete=models.CASCADE, 
        related_name='quizzes', 
        verbose_name='Curso'
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='quizzes', 
        blank=True, 
        null=True, 
        verbose_name='Módulo (Opcional)'
    )
    title = models.CharField(max_length=255, verbose_name='Título do Simulado')
    passing_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=70.00, 
        verbose_name='Nota Mínima de Aprovação (%)'
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=30, 
        verbose_name='Tempo Limite (Minutos)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Simulado / Prova'
        verbose_name_plural = 'Simulados e Provas'

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='questions', 
        verbose_name='Simulado'
    )
    text = models.TextField(verbose_name='Enunciado da Questão')
    explanation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Justificativa / Comentário do Professor'
    )
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem de Exibição')

    class Meta:
        ordering = ['order']
        verbose_name = 'Questão'
        verbose_name_plural = 'Questões'

    def __str__(self):
        return f"Questão {self.order} - {self.quiz.title}"


class Option(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='options', 
        verbose_name='Questão'
    )
    text = models.CharField(max_length=500, verbose_name='Texto da Alternativa')
    is_correct = models.BooleanField(default=False, verbose_name='É a resposta correta?')

    class Meta:
        verbose_name = 'Alternativa'
        verbose_name_plural = 'Alternativas'

    def __str__(self):
        prefix = "✓" if self.is_correct else "✗"
        return f"[{prefix}] {self.text[:50]}"


class QuizAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='quiz_attempts', 
        verbose_name='Aluno'
    )
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='attempts', 
        verbose_name='Simulado'
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Nota Obtida (%)')
    passed = models.BooleanField(default=False, verbose_name='Aprovado?')
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Conclusão')

    class Meta:
        ordering = ['-completed_at']
        verbose_name = 'Tentativa de Simulado'
        verbose_name_plural = 'Tentativas de Simulados'

    def __str__(self):
        status = "Aprovado" if self.passed else "Reprovado"
        return f"{self.student.get_full_name() or self.student.username} - {self.quiz.title} ({status}: {self.score}%)"