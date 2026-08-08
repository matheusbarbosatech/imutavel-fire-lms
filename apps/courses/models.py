from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Course(models.TextChoices):
    NR_REGULATORY = 'NR_REGULATORY', 'Norma Regulamentadora (NR)'
    CIVIL_FIREFIGHTER = 'CIVIL_FIREFIGHTER', 'Bombeiro Civil'
    LIFEGUARD = 'LIFEGUARD', 'Guardião de Piscina'
    FREE_COURSE = 'FREE_COURSE', 'Curso Livre'

class CourseModel(models.Model):
    title = models.CharField(max_length=255, verbose_name='Título do Curso')
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=30, choices=Course.choices, default=Course.FREE_COURSE, verbose_name='Categoria')
    workload_hours = models.PositiveIntegerField(verbose_name='Carga Horária (Horas)')
    min_passing_score = models.DecimalField(max_length=4, max_digits=5, decimal_places=2, default=70.00, verbose_name='Nota Mínima (%)')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição do Curso')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class Module(models.Model):
    course = models.ForeignKey(CourseModel, on_delete=models.CASCADE, related_name='modules', verbose_name='Curso')
    title = models.CharField(max_length=255, verbose_name='Título do Módulo')
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem de Exibição')

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - Módulo {self.order}: {self.title}"


class Lesson(models.Model):
    class ContentType(models.TextChoices):
        VIDEO = 'VIDEO', 'Vídeo (YouTube)'
        PDF = 'PDF', 'Apostila / PDF'
        TEXT = 'TEXT', 'Texto / Leitura'

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name='Módulo')
    title = models.CharField(max_length=255, verbose_name='Título da Aula')
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.VIDEO, verbose_name='Tipo de Conteúdo')
    youtube_video_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID do Vídeo no YouTube', help_text='Exemplo: dQw4w9WgXcQ (Apenas o ID da URL)')
    pdf_storage_path = models.CharField(max_length=500, blank=True, null=True, verbose_name='Caminho/URL do PDF')
    text_content = models.TextField(blank=True, null=True, verbose_name='Conteúdo em Texto')
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name='Duração da Aula (em segundos)', help_text='Duração total do vídeo para cálculo de presença.')
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem da Aula')

    class Meta:
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - Aula {self.order}: {self.title}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        ACTIVE = 'ACTIVE', 'Ativa'
        SUSPENDED = 'SUSPENDED', 'Suspensa'
        COMPLETED = 'COMPLETED', 'Concluída'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Aluno')
    course = models.ForeignKey(CourseModel, on_delete=models.RESTRICT, related_name='enrollments', verbose_name='Curso')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING, verbose_name='Status da Matrícula')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Data da Matrícula')

    # Adicione esta linha (O interruptor de acesso):
    is_active = models.BooleanField(default=True, verbose_name="Matrícula Ativa?")
    
    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} - {self.course.title} ({self.get_status_display()})"


class StudentProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress', verbose_name='Aluno')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress', verbose_name='Aula')
    completed = models.BooleanField(default=False, verbose_name='Concluída')
    watched_seconds = models.PositiveIntegerField(default=0, verbose_name='Tempo Assistido (Segundos)')
    last_accessed_at = models.DateTimeField(auto_now=True, verbose_name='Último Acesso')

    class Meta:
        verbose_name = 'Progresso do Aluno'
        verbose_name_plural = 'Progressos dos Alunos'
        unique_together = ('student', 'lesson')

    def __str__(self):
        status = "Concluída" if self.completed else "Em Andamento"
        return f"{self.student.username} | {self.lesson.title} - {status}"

class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments', verbose_name='Aula')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_comments', verbose_name='Usuário')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='Resposta ao Comentário')
    text = models.TextField(verbose_name='Comentário / Dúvida')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data do Comentário')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentário da Aula'
        verbose_name_plural = 'Comentários das Aulas'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} em {self.lesson.title}"    