from django.db import models
from django.conf import settings
from apps.courses.models import Course


class Certificate(models.Model):
    """Modelo para armazenamento e validação de Certificados emitidos."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name="Aluno"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name="Curso"
    )
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Código de Autenticidade"
    )
    issued_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Data de Emissão"
    )
    pdf_file = models.FileField(
        upload_to='certificates/', 
        blank=True, 
        null=True, 
        verbose_name="Arquivo PDF do Certificado"
    )

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"

    def __str__(self):
        return f"Certificado {self.code} - {self.student.get_full_name() or self.student.username}"