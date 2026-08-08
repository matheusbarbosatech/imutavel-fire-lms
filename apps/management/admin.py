from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Colunas que vão aparecer na lista
    list_display = ['id', 'get_student_name', 'get_course_title', 'amount', 'due_date', 'status', 'payment_method']
    
    # Filtros laterais para facilitar a busca
    list_filter = ['status', 'payment_method', 'due_date']
    
    # Barra de pesquisa (busca por nome do aluno ou CPF)
    search_fields = ['enrollment__student__first_name', 'enrollment__student__cpf', 'enrollment__course__title']
    
    # Campos somente leitura
    readonly_fields = ['created_at']

    # Organização do formulário
    fieldsets = (
        ('Dados da Cobrança', {
            'fields': ('enrollment', 'amount', 'due_date', 'status', 'payment_method')
        }),
        ('Liquidação', {
            'fields': ('payment_date', 'notes')
        }),
        ('Auditoria', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # Funções para exibir dados relacionados facilmente na lista
    def get_student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    get_student_name.short_description = 'Aluno'

    def get_course_title(self, obj):
        return obj.enrollment.course.title
    get_course_title.short_description = 'Curso'