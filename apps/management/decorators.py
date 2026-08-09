from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Decorador customizado para garantir que apenas Admins/Superusers
    acessem rotas de gestão do sistema.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
            
        is_admin = getattr(request.user, 'role', '') == 'ADMIN' or request.user.is_superuser
        if not is_admin:
            messages.error(request, "Acesso restrito a administradores.")
            return redirect('courses:dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view