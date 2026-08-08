from django.db import models
from apps.courses.models import Enrollment

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Atrasado'
        CANCELLED = 'CANCELLED', 'Cancelado'

    class Method(models.TextChoices):
        PIX = 'PIX', 'PIX'
        CREDIT_CARD = 'CREDIT_CARD', 'Cartão de Crédito'
        BOLETO = 'BOLETO', 'Boleto Bancário'
        CASH = 'CASH', 'Dinheiro em Espécie'
        MANUAL = 'MANUAL', 'Liberação Manual (Cortesia/Bolsa)'

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments', verbose_name='Matrícula')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    due_date = models.DateField(verbose_name='Data de Vencimento')
    payment_date = models.DateField(null=True, blank=True, verbose_name='Data do Pagamento')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='Status')
    payment_method = models.CharField(max_length=20, choices=Method.choices, default=Method.PIX, verbose_name='Método de Pagamento')
    notes = models.TextField(blank=True, null=True, verbose_name='Observações do Gestor')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

    def __str__(self):
        return f"Fatura #{self.id} - {self.enrollment.student.get_full_name()} (R$ {self.amount})"