import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.courses.models import Course, Module, Lesson, Quiz, Question, Answer, Enrollment

def popular_banco():
    print("🧹 Limpando dados antigos do banco de dados...")
    
    # Apaga dados antigos para evitar conflitos
    Quiz.objects.all().delete()
    Lesson.objects.all().delete()
    Module.objects.all().delete()
    Enrollment.objects.all().delete()
    Course.objects.all().delete()
    
    print("✨ Banco de dados limpo com sucesso!")
    print("🔥 Cadastrando nova estrutura oficial do Imutável Fire...")

    # ==========================================
    # 1. CURSO: BOMBEIRO CIVIL (80h)
    # ==========================================
    curso_bc = Course.objects.create(
        title="Formação de Bombeiro Civil",
        description="Curso profissionalizante de Formação de Bombeiro Civil em conformidade com a Resolução SEDEC/CBMERJ N° 31.",
        is_active=True
    )

    m1_bc = Module.objects.create(
        course=curso_bc,
        title="Módulo 1: Teoria do Fogo e Equipamentos de Combate",
        order=1
    )
    aulas_m1_bc = [
        "1.1 Introdução à Profissão e Legislação do Bombeiro Civil",
        "1.2 Química e Física do Fogo (Tetraedro do Fogo)",
        "1.3 Classes de Incêndio e Agentes Extintores",
        "1.4 Operação de Extintores e Carretas Manuais",
        "1.5 Sistemas Fixos, Sprinklers e Hidrantes"
    ]
    for idx, titulo in enumerate(aulas_m1_bc, 1):
        Lesson.objects.create(
            module=m1_bc,
            title=titulo,
            order=idx,
            content=f"Espaço reservado para o texto explicativo, resumos ou links em PDF da aula '{titulo}'.",
            video_url=""
        )

    m2_bc = Module.objects.create(
        course=curso_bc,
        title="Módulo 2: Equipamentos Especiais, Helipontos e Riscos",
        order=2
    )
    aulas_m2_bc = [
        "2.1 EPI e Equipamento de Proteção Respiratória (EPR)",
        "2.2 Emergências em Elevadores e Planos de Emergência",
        "2.3 Prevenção e Segurança em Áreas de Pouso (Helipontos)",
        "2.4 Introdução aos Produtos Perigosos e Espaços Confinados"
    ]
    for idx, titulo in enumerate(aulas_m2_bc, 1):
        Lesson.objects.create(
            module=m2_bc,
            title=titulo,
            order=idx,
            content=f"Espaço reservado para a aula '{titulo}'.",
            video_url=""
        )

    m3_bc = Module.objects.create(
        course=curso_bc,
        title="Módulo 3: Atendimento Pré-Hospitalar (APH) & SBV",
        order=3
    )
    aulas_m3_bc = [
        "3.1 Aspectos Legais, Biossegurança e Avaliação Inicial",
        "3.2 Vias Aéreas e Suporte Básico de Vida (SBV / RCP)",
        "3.3 Controle de Hemorragias e Estado de Choque",
        "3.4 Fraturas, Imobilizações, Ferimentos e Queimaduras",
        "3.5 Emergências Clínicas e Transporte de Vítimas"
    ]
    for idx, titulo in enumerate(aulas_m3_bc, 1):
        Lesson.objects.create(
            module=m3_bc,
            title=titulo,
            order=idx,
            content=f"Conteúdo teórico de APH para '{titulo}'.",
            video_url=""
        )

    m4_bc = Module.objects.create(
        course=curso_bc,
        title="Módulo 4: Etapa Prática Presencial no Polo",
        order=4
    )
    Lesson.objects.create(
        module=m4_bc,
        title="4.1 Instruções e Agendamento para o Treinamento Prático",
        order=1,
        content="Instruções de comparecimento ao polo físico (Endereço: Estrada do Campinho, n.4700). Trazer uniforme e documento com foto.",
        video_url=""
    )

    # ==========================================
    # 2. CURSO: NR 35 - TRABALHO EM ALTURA (8h)
    # ==========================================
    curso_nr35 = Course.objects.create(
        title="NR 35 - Segurança no Trabalho em Altura",
        description="Capacitação para trabalho em altura conforme diretrizes da Norma Regulamentadora 35.",
        is_active=True
    )
    m1_nr35 = Module.objects.create(
        course=curso_nr35,
        title="Módulo 1: Teoria e Gestão de Riscos em Altura",
        order=1
    )
    aulas_nr35 = [
        "1.1 Normas, Regulamentos e Responsabilidades",
        "1.2 Análise de Risco (AR) e Condições Impeditivas",
        "1.3 Equipamentos de Proteção Coletiva (EPC) e Individual (EPI)",
        "1.4 Sistemas de Ancoragem, Nós e Voltas",
        "1.5 Noções de Resgate e Primeiros Socorros em Altura"
    ]
    for idx, titulo in enumerate(aulas_nr35, 1):
        Lesson.objects.create(
            module=m1_nr35,
            title=titulo,
            order=idx,
            content=f"Material da NR-35 sobre '{titulo}'.",
            video_url=""
        )

    # ==========================================
    # 3. CURSO: NR 33 - ESPAÇOS CONFINADOS (16h)
    # ==========================================
    curso_nr33 = Course.objects.create(
        title="NR 33 - Segurança em Espaços Confinados",
        description="Treinamento para Trabalhadores Autorizados e Vigias em conformidade com a Portaria MTE 1.409/2012.",
        is_active=True
    )
    m1_nr33 = Module.objects.create(
        course=curso_nr33,
        title="Módulo 1: Reconhecimento e Medidas de Segurança",
        order=1
    )
    aulas_nr33 = [
        "1.1 Definição de Espaços Confinados e Identificação de Riscos",
        "1.2 Papéis e Responsabilidades: Empregador, Supervisor e Vigia",
        "1.3 Emissão e Preenchimento da Permissão de Entrada e Trabalho (PET)",
        "1.4 Monitoramento Atmosférico (Teste do Ar) e Ventilação",
        "1.5 Medidas de Isolamento, EPI/EPR e Procedimentos de Resgate"
    ]
    for idx, titulo in enumerate(aulas_nr33, 1):
        Lesson.objects.create(
            module=m1_nr33,
            title=titulo,
            order=idx,
            content=f"Material da NR-33 sobre '{titulo}'.",
            video_url=""
        )

    # ==========================================
    # 4. CURSO: NR 20 - INFLAMÁVEIS E COMBUSTÍVEIS (4h)
    # ==========================================
    curso_nr20 = Course.objects.create(
        title="NR 20 - Líquidos Combustíveis e Inflamáveis",
        description="Curso Básico / Iniciação sobre prevenção e controle no manuseio de inflamáveis e combustíveis.",
        is_active=True
    )
    m1_nr20 = Module.objects.create(
        course=curso_nr20,
        title="Módulo 1: Conceitos e Ações Operacionais",
        order=1
    )
    aulas_nr20 = [
        "1.1 Legislação e Classificação de Inflamáveis e Combustíveis",
        "1.2 Guia de Procedimentos de Emergência",
        "1.3 EPIs e EPRs Indicados para Vapores e Inflamáveis",
        "1.4 Ações Operacionais de Primeira Resposta"
    ]
    for idx, titulo in enumerate(aulas_nr20, 1):
        Lesson.objects.create(
            module=m1_nr20,
            title=titulo,
            order=idx,
            content=f"Material da NR-20 sobre '{titulo}'.",
            video_url=""
        )

    print("🎉 Povoamento limpo e finalizado com sucesso!")

if __name__ == '__main__':
    popular_banco()