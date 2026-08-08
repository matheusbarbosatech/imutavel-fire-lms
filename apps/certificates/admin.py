from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['auth_code', 'student', 'course', 'issued_at', 'is_valid']
    list_filter = ['is_valid', 'course']
    search_fields = ['auth_code', 'student__username', 'student__cpf', 'student__email']
    readonly_fields = ['auth_code', 'issued_at']