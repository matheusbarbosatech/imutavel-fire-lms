from django.db import models
from django.conf import settings


class Course(models.Model):
    """Modelo principal dos cursos do LMS."""
    title = models.CharField(max_length=200, verbose_name="Título do Curso")
    description = models.TextField(verbose_name="Descrição do Curso")
    is_active = models.BooleanField(default=True, verbose_name="Curso Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Module(models.Model):
    """Módulos / Unidades de ensino pertencentes a um curso."""
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='modules',
        verbose_name="Curso"
    )
    title = models.CharField(max_length=200, verbose_name="Título do Módulo")
    order = models.PositiveIntegerField(default=1, verbose_name="Ordem de Exibição")

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Aulas contendo teoria, links de vídeos e anexos de materiais complementares."""
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='lessons',
        verbose_name="Módulo"
    )
    title = models.CharField(max_length=200, verbose_name="Título da Aula")
    content = models.TextField(blank=True, verbose_name="Conteúdo Teórico / Texto")
    video_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="URL do Vídeo (YouTube/Vimeo/Drive)"
    )
    
    # 📎 Campo flexível para qualquer tipo de material (PDF, ZIP, DOCX, PNG, PPTX, etc.)
    attachment = models.FileField(
        upload_to='materials/', 
        blank=True, 
        null=True, 
        verbose_name="Material Complementar (PDF, ZIP, DOCX, etc.)"
    )
    
    order = models.PositiveIntegerField(default=1, verbose_name="Ordem de Exibição")

    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    """Matrículas dos alunos em cada curso."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name="Aluno"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name="Curso"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Matrícula")
    is_active = models.BooleanField(default=True, verbose_name="Matrícula Ativa")

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} -> {self.course.title}"


class Quiz(models.Model):
    """Avaliação / Questionário associado a uma aula ou módulo."""
    lesson = models.OneToOneField(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='quiz',
        verbose_name="Aula Relacionada",
        blank=True,
        null=True
    )
    title = models.CharField(max_length=200, verbose_name="Título da Avaliação")
    min_score = models.PositiveIntegerField(default=70, verbose_name="Nota Mínima para Aprovação (%)")

    class Meta:
        verbose_name = "Avaliação / Quiz"
        verbose_name_plural = "Avaliações / Quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    """Perguntas pertencentes a um Quiz."""
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='questions',
        verbose_name="Quiz"
    )
    text = models.TextField(verbose_name="Enunciado da Pergunta")

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}..."


class Answer(models.Model):
    """Opções de resposta para cada pergunta."""
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='answers',
        verbose_name="Pergunta"
    )
    text = models.CharField(max_length=255, verbose_name="Texto da Resposta")
    is_correct = models.BooleanField(default=False, verbose_name="Opção Correta")

    class Meta:
        verbose_name = "Opção de Resposta"
        verbose_name_plural = "Opções de Resposta"

    def __str__(self):
        correta = " (Correta)" if self.is_correct else ""
        return f"{self.text}{correta}"


class LessonProgress(models.Model):
    """Rastreamento de conclusão de aulas por aluno."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name="Aluno"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name="Aula"
    )
    completed = models.BooleanField(default=False, verbose_name="Concluída?")
    completed_at = models.DateTimeField(auto_now=True, verbose_name="Data de Conclusão")

    class Meta:
        verbose_name = "Progresso de Aula"
        verbose_name_plural = "Progresso de Aulas"
        unique_together = ('student', 'lesson')

    def __str__(self):
        status = "Concluída" if self.completed else "Pendente"
        return f"{self.student.get_full_name() or self.student.username} - {self.lesson.title} ({status})"


class LessonComment(models.Model):
    """Comentários e dúvidas dos alunos por aula."""
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Aula"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_comments',
        verbose_name="Usuário"
    )
    text = models.TextField(verbose_name="Dúvida / Comentário")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data do Comentário")

    class Meta:
        verbose_name = "Dúvida/Comentário da Aula"
        verbose_name_plural = "Dúvidas/Comentários das Aulas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} em {self.lesson.title}: {self.text[:30]}"