from django.contrib import admin
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Matricula, Documento

class DocInline(admin.TabularInline):
    model = Documento
    extra = 0
    readonly_fields = ['arquivo']

@admin.register(Matricula)
class MatAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf', 'status', 'ip_registro', 'criado_em']
    list_filter = ['status', 'criado_em']
    inlines = [DocInline]
    readonly_fields = ['ip_registro', 'user_agent', 'aceitou_termos', 'criado_em']
    actions = ['aprovar', 'rejeitar']

    def aprovar(self, req, qs):
        qs.update(status='approved')
        for m in qs:
            try: send_mail('Matrícula Aprovada', f'Olá {m.nome}, sua matrícula foi aprovada!', settings.DEFAULT_FROM_EMAIL, [m.email])
            except: pass
        self.message_user(req, f"{qs.count()} aprovadas com e-mail enviado.")
    aprovar.short_description = "✅ Aprovar selecionados"

    def rejeitar(self, req, qs):
        qs.update(status='rejected')
        self.message_user(req, f"{qs.count()} rejeitadas.")
    rejeitar.short_description = "❌ Rejeitar selecionados"