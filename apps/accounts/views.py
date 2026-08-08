from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser

def login_view(request):
    # Se o usuário já estiver logado, manda pro painel
    if request.user.is_authenticated:
        return redirect('courses:student_dashboard')
        
    if request.method == 'POST':
        # O HTML envia os dados como 'username' e 'password'
        email_digitado = request.POST.get('username') 
        senha_digitada = request.POST.get('password')
        
        # Tenta validar no banco de dados
        user = authenticate(request, username=email_digitado, password=senha_digitada)
        
        if user is not None:
            login(request, user)
            return redirect('courses:student_dashboard')
        else:
            # Em vez de erro 500, devolve um alerta visual
            messages.error(request, 'E-mail ou senha incorretos. Verifique seus dados.')
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Você saiu do sistema com sucesso.')
    return redirect('accounts:login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('courses:student_dashboard')
        
    if request.method == 'POST':
        nome = request.POST.get('first_name')
        email = request.POST.get('email')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('password')
        
        # 1. Verifica se o e-mail já existe no banco
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está em uso. Tente fazer login ou recupere sua senha.')
            return redirect('accounts:register')
            
        try:
            # 2. Cria o usuário com segurança
            user = CustomUser(
                email=email,
                first_name=nome,
                cpf=cpf,
                role='STUDENT' # Define como ALUNO automaticamente
            )
            
            # Alguns sistemas do Django ainda exigem o preenchimento do username em background
            if hasattr(user, 'username'):
                user.username = email 
                
            user.set_password(senha) # Criptografa a senha (NUNCA salvar em texto puro)
            user.save()
            
            # 3. Loga o usuário e manda pra plataforma
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo(a) ao Imutável Fire.')
            return redirect('courses:student_dashboard')
            
        except Exception as e:
            # Se algo grave acontecer no banco, exibe o erro exato na tela sem derrubar o site
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return redirect('accounts:register')
            
    return render(request, 'accounts/register.html')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')