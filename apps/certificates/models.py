import uuid
import hashlib
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.courses.models import CourseModel


class Certificate(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name='Aluno'
    )
    course = models.ForeignKey(
        CourseModel, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name='Curso'
    )
    auth_code = models.CharField(
        max_length=64, 
        unique=True, 
        db_index=True, 
        verbose_name='Código Hash de Autenticidade'
    )
    qr_code_image = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name='Caminho do QR Code'
    )
    pdf_file_path = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        verbose_name='Caminho do Arquivo PDF'
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Emissão')
    expires_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='Data de Validade / Reciclagem'
    )
    is_valid = models.BooleanField(default=True, verbose_name='Documento Válido')

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        unique_together = ('student', 'course')

    def save(self, *args, **kwargs):
        if not self.auth_code:
            raw_data = f"{self.student.cpf or self.student.username}-{self.course.id}-{uuid.uuid4()}"
            self.auth_code = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()[:16].upper()

        if not self.expires_at:
            # Por padrão, define a validade para 1 ano (365 dias) após a emissão para NRs/CBMERJ
            self.expires_at = timezone.now() + timedelta(days=365)

        super().save(*args, **kwargs)

    def __str__(self):
        student_name = self.student.get_full_name() or self.student.username
        return f"Certificado [{self.auth_code}] - {student_name} ({self.course.title})"