from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'cpf', 'role', 'cbmerj_registration', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'cpf', 'cbmerj_registration']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Civis e Profissionais', {
            'fields': ('cpf', 'rg', 'cbmerj_registration', 'role', 'current_session_key')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Civis e Profissionais', {
            'fields': ('first_name', 'last_name', 'email', 'cpf', 'rg', 'cbmerj_registration', 'role')
        }),
    )