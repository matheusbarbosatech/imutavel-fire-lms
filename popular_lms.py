import os
import sys
import django

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Configuração do ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.courses.models import Course, Module, Lesson, Quiz, Question, Answer, Enrollment
from django.contrib.auth import get_user_model

User = get_user_model()


def run_populate():
    print("🧹 [1/5] Limpando dados antigos dos cursos, módulos, aulas e quizzes...")
    Answer.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()
    Lesson.objects.all().delete()
    Module.objects.all().delete()
    Course.objects.all().delete()
    print("✅ Dados antigos limpos com sucesso!")

    print("\n🔥 [2/5] Cadastrando estrutura oficial de cursos com conteúdo rico e vídeos...")

    # =========================================================================
    # CURSO 1: Formação de Bombeiro Civil (80h)
    # =========================================================================
    course_bc = Course.objects.create(
        title="Formação de Bombeiro Civil - 80h",
        description="Treinamento oficial completo para prevenção, combate a incêndios, abandono de área, resgate técnico e atendimento pré-hospitalar (APH) conforme NBR 14608.",
        is_active=True
    )

    # --- Módulos & Aulas ---
    m1_bc = Module.objects.create(
        course=course_bc,
        title="Módulo 1: Teoria do Fogo, Química da Combustão e Prevenção",
        order=1
    )

    l1_bc = Lesson.objects.create(
        module=m1_bc,
        title="Aula 1: Química e Física do Fogo (Tetraedro da Combustão)",
        content="""
        <div class="space-y-4">
            <div class="bg-red-50 border-l-4 border-red-600 p-4 rounded-r-xl">
                <h4 class="font-extrabold text-red-900 text-base">🔥 Fundamentos da Combustão Profissional</h4>
                <p class="text-xs text-red-700 mt-1">O fogo é uma reação química de oxidação exotérmica auto-sustentável. Compreender seus componentes é a chave para o combate eficiente.</p>
            </div>

            <h4 class="font-bold text-slate-900 text-lg">Componentes do Tetraedro do Fogo</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="bg-slate-100 p-3.5 rounded-xl">
                    <strong class="text-slate-900 block font-bold text-sm mb-1">1. Combustível</strong>
                    É o material que queima. Pode ser sólido (madeira, tecido), líquido (gasolina, álcool) ou gasoso (GLP, GNV).
                </div>
                <div class="bg-slate-100 p-3.5 rounded-xl">
                    <strong class="text-slate-900 block font-bold text-sm mb-1">2. Comburente (Oxigênio)</strong>
                    O agente oxidante. Na atmosfera a concentração normal de O₂ é ~21%. Abaixo de 14% a maioria dos fogos se extingue.
                </div>
                <div class="bg-slate-100 p-3.5 rounded-xl">
                    <strong class="text-slate-900 block font-bold text-sm mb-1">3. Calor (Temperatura de Ignição)</strong>
                    Energia de ativação que eleva a temperatura do combustível gerando vapores inflamáveis.
                </div>
                <div class="bg-slate-100 p-3.5 rounded-xl">
                    <strong class="text-slate-900 block font-bold text-sm mb-1">4. Reação em Cadeia</strong>
                    A sequência de radicais livres formados pela quebra das moléculas que mantém a chama viva.
                </div>
            </div>

            <div class="bg-amber-50 border border-amber-200 p-4 rounded-2xl">
                <h5 class="font-extrabold text-amber-900 text-sm mb-2">📋 Checklist Operacional de Métodos de Extinção:</h5>
                <ul class="list-disc list-inside text-xs text-amber-800 space-y-1">
                    <td><strong>Resfriamento:</strong> Remoção do calor (ex: aplicação de jato de água).</td>
                    <td><strong>Abafamento:</strong> Isolamento do oxigênio/comburente (ex: tampa na panela, manta ignífuga).</td>
                    <td><strong>Isolamento / Retirada do Material:</strong> Remoção do combustível do raio de ação das chamas.</td>
                    <td><strong>Quebra da Reação em Cadeia:</strong> Inibição química de radicais livres (ex: agente Pó ABC).</td>
                </ul>
            </div>
        </div>
        """,
        video_url="https://www.youtube.com/embed/Y0A-z92H-9g",
        order=1
    )

    l2_bc = Lesson.objects.create(
        module=m1_bc,
        title="Aula 2: Classes de Incêndio e Operação de Extintores Portáteis",
        content="""
        <div class="space-y-4">
            <h4 class="font-extrabold text-slate-900 text-lg">Classificação Oficial dos Incêndios (NBR 12693)</h4>
            
            <div class="space-y-3 text-xs">
                <div class="p-3.5 bg-red-50 border border-red-200 rounded-2xl">
                    <strong class="text-red-700 font-extrabold text-sm block">Classe A — Materiais Sólidos Papelosos e Fibrosos</strong>
                    <p class="text-slate-600 mt-0.5">Queimam em superfície e profundidade. Deixam resíduos e cinzas. <strong>Agente Indicado:</strong> Água Pressurizada (AP) ou Pó ABC.</p>
                </div>
                <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl">
                    <strong class="text-amber-700 font-extrabold text-sm block">Classe B — Líquidos e Gases Inflamáveis</strong>
                    <p class="text-slate-600 mt-0.5">Queimam apenas na superfície. Não deixam resíduos. <strong>Agente Indicado:</strong> CO₂ (Gás Carbônico), Pó BC ou ABC.</p>
                </div>
                <div class="p-3.5 bg-blue-50 border border-blue-200 rounded-2xl">
                    <strong class="text-blue-700 font-extrabold text-sm block">Classe C — Equipamentos Elétricos Energizados</strong>
                    <p class="text-slate-600 mt-0.5">Motores, quadros elétricos e computadores ligados na tomada. <strong>Agente Indicado:</strong> CO₂ ou Pó ABC. 🚫 <em>NUNCA USE ÁGUA! (Risco de Eletrocussão)</em></p>
                </div>
                <div class="p-3.5 bg-purple-50 border border-purple-200 rounded-2xl">
                    <strong class="text-purple-700 font-extrabold text-sm block">Classe D — Metais Pirofóricos</strong>
                    <p class="text-slate-600 mt-0.5">Sódio, magnésio, titânio e alumínio em pó. <strong>Agente Indicado:</strong> Pó Químico Especial Classe D.</p>
                </div>
            </div>

            <div class="bg-slate-900 text-white p-5 rounded-3xl space-y-2 text-xs">
                <h5 class="font-extrabold text-red-400 text-sm">💡 Passo a Passo da Operação do Extintor (PASS):</h5>
                <ol class="list-decimal list-inside space-y-1 text-slate-300">
                    <td><strong>P (Puxar):</strong> Retire o lacre e puxe o pino de segurança.</td>
                    <td><strong>A (Apontar):</strong> Aponte a mangueira para a base do fogo (não para a chama solta).</td>
                    <td><strong>S (Aperta):</strong> Aperte o gatilho/alavanca gradualmente.</td>
                    <td><strong>S (Varrer):</strong> Faça um movimento suave de varredura de um lado para o outro a uma distância segura de 2 metros.</td>
                </ol>
            </div>
        </div>
        """,
        video_url="https://www.youtube.com/embed/Pj15bA-Hq0Y",
        order=2
    )

    # Simulado do Módulo 1
    quiz_bc1 = Quiz.objects.create(
        lesson=l2_bc,
        title="Simulado de Avaliação — Combate a Incêndios e Extintores",
        min_score=70.0
    )
    q1 = Question.objects.create(quiz=quiz_bc1, text="Qual agente extintor NUNCA deve ser aplicado em incêndios envolvendo Classe C (equipamentos elétricos energizados)?")
    Answer.objects.create(question=q1, text="Água Pressurizada (AP), devido à condução elétrica de choque fatal.", is_correct=True)
    Answer.objects.create(question=q1, text="Gás Carbônico (CO2), pois causa queimadura de gelo.", is_correct=False)
    Answer.objects.create(question=q1, text="Pó Químico Seco (PQS), pois danifica peças eletrônicas.", is_correct=False)

    q2 = Question.objects.create(quiz=quiz_bc1, text="No combate ao fogo com extintores, para qual local a mangueira deve ser apontada?")
    Answer.objects.create(question=q2, text="Para o topo da coluna de fumaça.", is_correct=False)
    Answer.objects.create(question=q2, text="Para a base das chamas, no combustível gerador.", is_correct=True)
    Answer.objects.create(question=q2, text="Para o ar ao redor do ambiente.", is_correct=False)

    # --- Módulo 2: APH ---
    m2_bc = Module.objects.create(
        course=course_bc,
        title="Módulo 2: Atendimento Pré-Hospitalar (APH) e Suporte Básico de Vida",
        order=2
    )

    l3_bc = Lesson.objects.create(
        module=m2_bc,
        title="Aula 1: Protocolo XABCDE do Trauma e Reanimação Cardiopulmonar (RCP)",
        content="""
        <div class="space-y-4">
            <div class="bg-emerald-50 border-l-4 border-emerald-600 p-4 rounded-r-xl">
                <h4 class="font-extrabold text-emerald-900 text-base">🏥 Protocolo Atualizado de Atendimento Inicial ao Traumatizado</h4>
                <p class="text-xs text-emerald-700 mt-1">A avaliação primária em APH segue a sequência sistemática prioritária de preservação da vida.</p>
            </div>

            <div class="space-y-2 text-xs">
                <div class="p-3 bg-slate-100 rounded-xl"><strong>X (Exsanguinação):</strong> Controle imediato de hemorragias massivas ativas (uso de torniquetes ou compressão direta).</div>
                <div class="p-3 bg-slate-100 rounded-xl"><strong>A (Airway):</strong> Abertura de vias aéreas com proteção e alinhamento neutro da coluna cervical.</div>
                <div class="p-3 bg-slate-100 rounded-xl"><strong>B (Breathing):</strong> Avaliação da ventilação e respiração (presença de pneumotórax ou tórax instável).</div>
                <div class="p-3 bg-slate-100 rounded-xl"><strong>C (Circulation):</strong> Verificação de pulso, perfusão capilar e controle de choque hipovolêmico.</div>
                <div class="p-3 bg-slate-100 rounded-xl"><strong>D (Disability):</strong> Exame neurológico sumário (Escala de Coma de Glasgow e reatividade pupilar).</div>
                <div class="p-3 bg-slate-100 rounded-xl"><strong>E (Exposure):</strong> Exposição total da vítima com prevenção e controle de hipotermia (coberta térmica).</div>
            </div>

            <div class="bg-red-900 text-white p-5 rounded-3xl space-y-2 text-xs">
                <h5 class="font-extrabold text-amber-300 text-sm">🫀 Parâmetros da Reanimação Cardiopulmonar (RCP em Adultos):</h5>
                <ul class="list-disc list-inside space-y-1 text-slate-200">
                    <td><strong>Frequência:</strong> 100 a 120 compressões por minuto.</td>
                    <td><strong>Profundidade:</strong> 5 cm a no máximo 6 cm no terço inferior do esterno.</td>
                    <td><strong>Proporção:</strong> 30 compressões para 2 ventilações (ou compressões contínuas se via aérea avançada).</td>
                    <td><strong>Retorno do Tórax:</strong> Permitir o retorno completo do tórax sem manter pressão contínua.</td>
                </ul>
            </div>
        </div>
        """,
        video_url="https://www.youtube.com/embed/2g811Eo7K8U",
        order=1
    )

    # =========================================================================
    # CURSO 2: NR-35 - Trabalho em Altura (16h)
    # =========================================================================
    course_nr35 = Course.objects.create(
        title="NR-35 - Segurança no Trabalho em Altura",
        description="Treinamento teórico e prático para trabalhadores autorizados e supervisores em atividades executadas acima de 2,00m do nível inferior conforme a Norma Regulamentadora 35.",
        is_active=True
    )

    m1_nr35 = Module.objects.create(
        course=course_nr35,
        title="Módulo 1: Análise de Risco, Permissão de Trabalho e Equipamentos de Proteção",
        order=1
    )

    Lesson.objects.create(
        module=m1_nr35,
        title="Aula 1: Análise Preliminar de Risco (APR) e Sistema de Proteção Contra Quedas (SPIQ)",
        content="""
        <div class="space-y-4">
            <h4 class="font-extrabold text-slate-900 text-lg">Regras Fundamentais da NR-35</h4>
            
            <div class="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900">
                <p><strong>Definição Legal:</strong> Considera-se trabalho em altura toda atividade executada acima de 2,00 metros do nível inferior, onde haja risco de queda.</p>
            </div>

            <h5 class="font-bold text-slate-900 text-sm">📋 Requisitos Obrigatórios Pré-Operacionais:</h5>
            <ul class="list-disc list-inside text-xs text-slate-700 space-y-1.5 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <td><strong>APR (Análise Preliminar de Risco):</strong> Mapeamento antecedente de fatores de risco do local (vento, eletricidade, pontos de ancoragem).</td>
                <td><strong>PT (Permissão de Trabalho):</strong> Documento emitido e assinado autorizando a equipe a iniciar o serviço específico naquele turno.</td>
                <td><strong>Atestado de Saúde Ocupacional (ASO):</strong> Exames aptos com enfase em aptidão física e psicossocial para altura.</td>
            </ul>

            <div class="bg-slate-900 text-white p-5 rounded-3xl space-y-2 text-xs">
                <h5 class="font-extrabold text-red-400 text-sm">🛡️ Componentes do Sistema de Proteção Individual Contra Quedas (SPIQ):</h5>
                <ol class="list-decimal list-inside space-y-1 text-slate-300">
                    <td><strong>Cinto Tipo Paraquedista:</strong> Deve possuir elemento de engate dorsal ou peitoral.</td>
                    <td><strong>Talabarte Duplo Y com Absorvedor de Energia:</strong> Garante conexão 100% contínua ao trocar de ponto de ancoragem.</td>
                    <td><strong>Ponto de Ancoragem (Sistema de Ancoragem Ancorado NBR 16325):</strong> Deve suportar carga mínima estática exigida no projeto.</td>
                </ol>
            </div>
        </div>
        """,
        video_url="https://www.youtube.com/embed/YpX8s_76mB8",
        order=1
    )

    # =========================================================================
    # CURSO 3: NR-33 - Espaço Confinado (16h)
    # =========================================================================
    course_nr33 = Course.objects.create(
        title="NR-33 - Segurança em Espaços Confinados",
        description="Capacitação para Trabalhadores Autorizados e Vigias em ambientes não projetados para ocupação humana contínua com atmosfera de risco.",
        is_active=True
    )

    m1_nr33 = Module.objects.create(
        course=course_nr33,
        title="Módulo 1: Atmosfera Perigosa, Monitoramento de Gases e Atribuições do Vigia",
        order=1
    )

    Lesson.objects.create(
        module=m1_nr33,
        title="Aula 1: Permissão de Entrada e Trabalho (PET) e Papel do Vigia",
        content="""
        <div class="space-y-4">
            <div class="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-xl">
                <h4 class="font-extrabold text-blue-900 text-base">☣️ Características de um Espaço Confinado (NR-33)</h4>
                <p class="text-xs text-blue-700 mt-1">Espaço não projetado para ocupação humana contínua, com meios limitados de entrada/saída e ventilação deficiente.</p>
            </div>

            <h5 class="font-bold text-slate-900 text-sm">🚨 Atribuições Exclusivas do Vigia de Espaço Confinado:</h5>
            <ul class="list-disc list-inside text-xs text-slate-700 space-y-1.5 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <td>Manter contagem contínua dos trabalhadores autorizados no interior do vaso/tanque.</td>
                <td>Permanecer obrigatoriamente do lado de fora do espaço confinado junto à entrada.</td>
                <td>Operar os detetores multigás (LEL, O₂, H₂S, CO) continuamente durante todo o turno.</td>
                <td>Acionar imediatamente a equipe de resgate externa em emergências. 🚫 <strong>NUNCA ENTRAR NO ESPAÇO PARA FAZER RESGATE SEM SUPORTE AUTÔNOMO!</strong></td>
            </ul>
        </div>
        """,
        video_url="https://www.youtube.com/embed/8v_YpPZ4W-E",
        order=1
    )

    # =========================================================================
    # CURSO 4: NR-20 - Inflamáveis e Combustíveis
    # =========================================================================
    course_nr20 = Course.objects.create(
        title="NR-20 - Segurança com Inflamáveis e Combustíveis",
        description="Diretrizes de segurança para extração, armazenamento, manuseio e transporte de líquidos combustíveis e gases inflamáveis.",
        is_active=True
    )

    m1_nr20 = Module.objects.create(
        course=course_nr20,
        title="Módulo 1: Classificação dos Inflamáveis e Medidas de Controle de Ignição",
        order=1
    )

    Lesson.objects.create(
        module=m1_nr20,
        title="Aula 1: Ponto de Fulgor, Ponto de Ignição e Áreas Classificadas",
        content="""
        <div class="space-y-4">
            <h4 class="font-extrabold text-slate-900 text-lg">Parâmetros Térmicos dos Inflamáveis</h4>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="bg-red-50 border border-red-200 p-4 rounded-2xl">
                    <strong class="text-red-700 font-extrabold text-sm block mb-1">Líquidos Inflamáveis</strong>
                    Possuem ponto de fulgor menor que 60°C. Ex: Gasolina (-43°C), Álcool etílico (13°C), Acetona.
                </div>
                <div class="bg-amber-50 border border-amber-200 p-4 rounded-2xl">
                    <strong class="text-amber-700 font-extrabold text-sm block mb-1">Líquidos Combustíveis</strong>
                    Possuem ponto de fulgor maior ou igual a 60°C e menor ou igual a 93°C. Ex: Óleo Diesel, Querosene.
                </div>
            </div>
        </div>
        """,
        video_url="https://www.youtube.com/embed/KjL9L3u502k",
        order=1
    )

    print("\n🎓 [3/5] Matriculando alunos em todos os cursos oficiais...")
    users = User.objects.all()
    all_courses = [course_bc, course_nr35, course_nr33, course_nr20]

    count_enrollments = 0
    for user in users:
        for course in all_courses:
            Enrollment.objects.get_or_create(
                student=user,
                course=course,
                defaults={'is_active': True}
            )
            count_enrollments += 1

    print(f"✅ Habilitadas {count_enrollments} matrículas de alunos com sucesso!")

    print("\n🎉 [5/5] BANCO DE DADOS ALIMENTADO E POVOADO COM SUCESSO!")
    print(f"📊 Resumo dos Conteúdo:")
    print(f"   • Cursos Ativos: {Course.objects.count()}")
    print(f"   • Módulos Criados: {Module.objects.count()}")
    print(f"   • Aulas Criadas: {Lesson.objects.count()}")
    print(f"   • Quizzes Criados: {Quiz.objects.count()}")
    print(f"   • Perguntas de Avaliação: {Question.objects.count()}")


if __name__ == "__main__":
    run_populate()