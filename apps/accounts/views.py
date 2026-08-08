from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser

def login_view(request):
    """Página de Login dos usuários/alunos."""
    if request.user.is_authenticated:
        return redirect('courses:student_dashboard')
        
    if request.method == 'POST':
        email_digitado = request.POST.get('username') 
        senha_digitada = request.POST.get('password')
        
        user = authenticate(request, username=email_digitado, password=senha_digitada)
        
        if user is not None:
            login(request, user)
            return redirect('courses:student_dashboard')
        else:
            messages.error(request, 'E-mail ou senha incorretos. Verifique seus dados e tente novamente.')
            
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Encerra a sessão do usuário."""
    logout(request)
    messages.success(request, 'Você saiu da plataforma com segurança.')
    return redirect('accounts:login')


def register_view(request):
    """Auto-cadastro de novos alunos com tratamento de exceções completo."""
    if request.user.is_authenticated:
        return redirect('courses:student_dashboard')
        
    if request.method == 'POST':
        nome = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        cpf = request.POST.get('cpf', '').strip()
        senha = request.POST.get('password', '')

        # 1. Validações básicas antes de chamar o banco
        if not nome or not email or not senha:
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
            return redirect('accounts:register')

        # 2. Checa se e-mail já está cadastrado
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado. Tente fazer login ou recupere sua senha.')
            return redirect('accounts:register')
            
        try:
            # 3. Instancia o novo aluno
            user = CustomUser(
                email=email,
                first_name=nome,
                cpf=cpf,
                role='STUDENT'
            )
            
            # Força o username a ser o e-mail para evitar falhas de restrição de unicidade
            user.username = email
                
            user.set_password(senha)
            user.save()
            
            # 4. Faz login e manda para os cursos
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo(a) ao Imutável Fire.')
            return redirect('courses:student_dashboard')
            
        except Exception as e:
            # Emite a mensagem exata de erro tratada no alerta da tela
            messages.error(request, f'Erro no banco de dados ao salvar cadastro: {str(e)}')
            return redirect('accounts:register')
            
    return render(request, 'accounts/register.html')


@login_required
def profile_view(request):
    """Visualização e edição do perfil do usuário logado."""
    return render(request, 'accounts/profile.html')