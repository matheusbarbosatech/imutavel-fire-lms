from django.contrib.auth import logout
from django.contrib import messages

class PreventConcurrentLoginsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_key = request.session.session_key
            stored_key = request.user.current_session_key

            # Se a chave da sessão for diferente da registrada no login mais recente, força o logout
            if stored_key and current_key != stored_key:
                logout(request)
                messages.error(
                    request, 
                    'Sua conta foi acessada em outro dispositivo ou navegador. Sessão encerrada por segurança.'
                )
        
        response = self.get_response(request)
        return response