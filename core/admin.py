import csv
from django.http import HttpResponse
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
    search_fields = ['nome', 'cpf', 'email']
    inlines = [DocInline]
    readonly_fields = ['ip_registro', 'user_agent', 'aceitou_termos', 'criado_em']
    actions = ['aprovar', 'rejeitar', 'exportar_csv']

    def aprovar(self, req, qs):
        qs.update(status='approved')
        self.message_user(req, f"{qs.count()} matrículas aprovadas.")
    aprovar.short_description = "✅ Aprovar selecionados"

    def rejeitar(self, req, qs):
        qs.update(status='rejected')
        self.message_user(req, f"{qs.count()} matrículas rejeitadas.")
    rejeitar.short_description = "❌ Rejeitar selecionados"

    def exportar_csv(self, request, queryset):
        # utf-8-sig garante que os acentos fiquem perfeitos no Excel
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="alunos_imutavel_fire.csv"'
        
        writer = csv.writer(response, delimiter=';') # Ponto e vírgula é melhor para Excel em português
        writer.writerow(['Nome', 'CPF', 'RG', 'Nascimento', 'E-mail', 'Telefone', 'Status', 'Data da Matrícula'])
        
        for mat in queryset:
            writer.writerow([
                mat.nome, mat.cpf, mat.rg, mat.nascimento, 
                mat.email, mat.telefone, mat.get_status_display(), 
                mat.criado_em.strftime("%d/%m/%Y %H:%M")
            ])
        return response
    exportar_csv.short_description = "📊 Exportar lista para Excel (CSV)"