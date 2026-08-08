from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Aluno'
        INSTRUCTOR = 'INSTRUCTOR', 'Instrutor'
        ADMIN = 'ADMIN', 'Administrador'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Perfil de Acesso'
    )
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True, verbose_name='CPF')
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name='RG')
    cbmerj_registration = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Registro Profissional CBMERJ'
    )
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name='Foto 3x4')
    blood_type = models.CharField(max_length=5, blank=True, null=True, verbose_name='Tipo Sanguíneo')
    current_session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='Chave da Sessão Atual'
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class StudentDocument(models.Model):
    class DocType(models.TextChoices):
        RG = 'RG', 'Documento de Identidade (RG/CNH)'
        CPF = 'CPF', 'CPF'
        RESIDENCE = 'RESIDENCE', 'Comprovante de Residência'
        ASO = 'ASO', 'ASO / Atestado Médico de Aptidão Física'
        DIPLOMA = 'DIPLOMA', 'Comprovante de Escolaridade'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollment_documents')
    doc_type = models.CharField(max_length=20, choices=DocType.choices, verbose_name='Tipo de Documento')
    file = models.FileField(upload_to='student_documents/', verbose_name='Arquivo Anexo')
    is_verified = models.BooleanField(default=False, verbose_name='Verificado pela Secretaria')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento de Matrícula'
        verbose_name_plural = 'Documentos de Matrícula'

    def __str__(self):
        return f"{self.user.username} - {self.get_doc_type_display()}"


class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name='Código da Conquista')
    name = models.CharField(max_length=100, verbose_name='Nome da Medalha')
    description = models.TextField(verbose_name='Descrição da Conquista')
    icon_class = models.CharField(max_length=50, default='bi-award', verbose_name='Ícone Bootstrap')

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name='Título')
    message = models.TextField(verbose_name='Mensagem')
    icon = models.CharField(max_length=50, default='bi-bell', verbose_name='Ícone')
    is_read = models.BooleanField(default=False, verbose_name='Lida?')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"