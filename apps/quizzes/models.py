from django.db import models
from apps.courses.models import Course, Module, Lesson

from django.conf import settings

# Caso este app possua modelos próprios de Quiz/Tentativa de alunos:
class StudentQuizAttempt(models.Model):
    """Registro de tentativas de alunos nos quizzes."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quiz_attempts')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tentativa - {self.course.title} ({self.score}%)"