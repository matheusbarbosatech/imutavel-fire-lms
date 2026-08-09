import os
import django

# Configuração do ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.courses.models import Course, Module, Lesson, Quiz, Question, Answer, Enrollment
from django.contrib.auth import get_user_model

User = get_user_model()


def run_populate():
    print("🧹 [1/4] Limpando dados antigos dos cursos, módulos, aulas e quizzes...")
    Answer.objects.all().delete()
    Question.objects.all().delete()
    Quiz.objects.all().delete()
    Lesson.objects.all().delete()
    Module.objects.all().delete()
    Course.objects.all().delete()
    print("✅ Dados antigos limpos com sucesso!")

    print("\n🔥 [2/4] Cadastrando estrutura oficial de cursos do Imutável Fire...")

    # ==========================================
    # CURSO 1: Formação de Bombeiro Civil (80h)
    # ==========================================
    course_bc = Course.objects.create(
        title="Formação de Bombeiro Civil - 80h",
        description="Treinamento completo profissional para prevenção, combate a incêndios, abandono de área e primeiros socorros avançados conforme NBR 14608.",
        is_active=True
    )

    # Módulo 1.1
    m1_bc = Module.objects.create(
        course=course_bc,
        title="Módulo 1: Teoria do Fogo e Combate a Incêndios",
        order=1
    )

    l1_bc = Lesson.objects.create(
        module=m1_bc,
        title="Aula 1: Química e Física do Fogo",
        content="""
        <h3>Triângulo e Tetraedro do Fogo</h3>
        <p>Para que ocorra o fogo, é necessária a presença de quatro elementos essenciais:</p>
        <ul>
            <li><strong>Combustível:</strong> É o material que queima (Sólido, Líquido ou Gasoso).</li>
            <li><strong>Comburente (Oxigênio):</strong> O gás que alimenta a reação química.</li>
            <li><strong>Calor:</strong> A energia de ativação inicial.</li>
            <li><strong>Reação em Cadeia:</strong> O processo químico auto-sustentável.</li>
        </ul>
        <p>A remoção de qualquer um desses elementos resultará na extinção do fogo.</p>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=1
    )

    l2_bc = Lesson.objects.create(
        module=m1_bc,
        title="Aula 2: Classes de Incêndio e Extintores",
        content="""
        <h3>Classes de Incêndio e Agentes Extintores</h3>
        <p>Conheça os principais tipos de fogo e como combatê-los de forma segura:</p>
        <ul>
            <li><strong>Classe A:</strong> Sólidos (papel, madeira, tecido). <em>Extintor: Água ou Pó ABC.</em></li>
            <li><strong>Classe B:</strong> Líquidos Inflamáveis (gasolina, álcool). <em>Extintor: CO2 ou Pó BC/ABC.</em></li>
            <li><strong>Classe C:</strong> Equipamentos Elétricos Energizados. <em>Extintor: CO2 ou Pó ABC. NUNCA use água!</em></li>
            <li><strong>Classe D:</strong> Metais Pirofóricos (magnésio, titânio). <em>Extintor: Pó Especial Classe D.</em></li>
        </ul>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=2
    )

    # Quiz da Aula 2
    quiz_bc = Quiz.objects.create(
        lesson=l2_bc,
        title="Avaliação de Classes de Incêndio",
        min_score=70.0
    )
    q1 = Question.objects.create(quiz=quiz_bc, text="Qual o extintor NUNCA deve ser usado em incêndios da Classe C (Elétrico Energizado)?")
    Answer.objects.create(question=q1, text="Água Pressurizada (AP)", is_correct=True)
    Answer.objects.create(question=q1, text="Gás Carbônico (CO2)", is_correct=False)
    Answer.objects.create(question=q1, text="Pó Químico Seco (PQS)", is_correct=False)

    q2 = Question.objects.create(quiz=quiz_bc, text="Líquidos inflamáveis como gasolina e óleo pertencem a qual classe de incêndio?")
    Answer.objects.create(question=q2, text="Classe A", is_correct=False)
    Answer.objects.create(question=q2, text="Classe B", is_correct=True)
    Answer.objects.create(question=q2, text="Classe C", is_correct=False)

    # Módulo 1.2
    m2_bc = Module.objects.create(
        course=course_bc,
        title="Módulo 2: APH - Atendimento Pré-Hospitalar",
        order=2
    )

    Lesson.objects.create(
        module=m2_bc,
        title="Aula 1: Protocolo XABCDE do Trauma",
        content="""
        <h3>Avaliação Primária de Emergência</h3>
        <p>Siga rigorosamente a ordem de atendimento ao acidentado:</p>
        <ol>
            <li><strong>X (Exsanguinação):</strong> Controle de hemorragias graves.</li>
            <li><strong>A (Airway):</strong> Vias aéreas e controle da coluna cervical.</li>
            <li><strong>B (Breathing):</strong> Ventilação e respiração.</li>
            <li><strong>C (Circulation):</strong> Circulação e controle de choque.</li>
            <li><strong>D (Disability):</strong> Exame neurológico rápido (Escala de Glasgow).</li>
            <li><strong>E (Exposure):</strong> Exposição total com prevenção da hipotermia.</li>
        </ol>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=1
    )

    # ==========================================
    # CURSO 2: NR-35 - Trabalho em Altura (16h)
    # ==========================================
    course_nr35 = Course.objects.create(
        title="NR-35 - Segurança no Trabalho em Altura",
        description="Norma Regulamentadora para capacitação de trabalhadores autorizados e supervisores em trabalhos realizados acima de 2,00m do nível inferior.",
        is_active=True
    )

    m1_nr35 = Module.objects.create(
        course=course_nr35,
        title="Módulo 1: Requisitos Normativos e EPIs",
        order=1
    )

    l1_nr35 = Lesson.objects.create(
        module=m1_nr35,
        title="Aula 1: Permissão de Trabalho (PT) e Análise de Risco (APR)",
        content="""
        <h3>Documentação Obrigatória para Trabalho em Altura</h3>
        <p>Todo trabalho em altura acima de 2 metros exige:</p>
        <ul>
            <li><strong>Análise Preliminar de Risco (APR):</strong> Mapeamento antecedente de todos os perigos no local.</li>
            <li><strong>Permissão de Trabalho (PT):</strong> Documento emitido e assinado autorizando a execução da tarefa específica.</li>
            <li><strong>EPIs Básicos:</strong> Cinto de segurança tipo paraquedista, talabarte duplo com absorvedor de energia e capacete com jugular.</li>
        </ul>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=1
    )

    # ==========================================
    # CURSO 3: NR-33 - Espaço Confinado (16h)
    # ==========================================
    course_nr33 = Course.objects.create(
        title="NR-33 - Segurança em Espaços Confinados",
        description="Treinamento de segurança para Trabalhadores Autorizados e Vigias em ambientes não projetados para ocupação humana contínua.",
        is_active=True
    )

    m1_nr33 = Module.objects.create(
        course=course_nr33,
        title="Módulo 1: Reconhecimento e Monitoramento de Atmosferas",
        order=1
    )

    Lesson.objects.create(
        module=m1_nr33,
        title="Aula 1: A Importância do Vigia e a PET",
        content="""
        <h3>O Papel do Vigia na NR-33</h3>
        <p>O Vigia deve permanecer fora do espaço confinado durante toda a operação, sendo responsável por:</p>
        <ul>
            <li>Manter a contagem contínua do número de trabalhadores autorizados.</li>
            <li>Operar os detectores contínuos de gás.</li>
            <li>Acionar a equipe de resgate em caso de emergência. NUNCA entrar no espaço confinado para resgate sem equipamento autônomo!</li>
        </ul>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=1
    )

    # ==========================================
    # CURSO 4: NR-20 - Inflamáveis e Combustíveis
    # ==========================================
    course_nr20 = Course.objects.create(
        title="NR-20 - Segurança com Inflamáveis e Combustíveis",
        description="Treinamento sobre extração, produção, armazenamento, transferência, manuseio e manipulação de inflamáveis e líquidos combustíveis.",
        is_active=True
    )

    m1_nr20 = Module.objects.create(
        course=course_nr20,
        title="Módulo 1: Propriedades dos Inflamáveis",
        order=1
    )

    Lesson.objects.create(
        module=m1_nr20,
        title="Aula 1: Ponto de Fulgor e Ponto de Combustão",
        content="""
        <h3>Definições da NR-20</h3>
        <p>Entenda a classificação dos combustíveis e inflamáveis:</p>
        <ul>
            <li><strong>Líquidos Inflamáveis:</strong> Possuem ponto de fulgor inferior a 60°C.</li>
            <li><strong>Líquidos Combustíveis:</strong> Possuem ponto de fulgor maior ou igual a 60°C e menor ou igual a 93°C.</li>
        </ul>
        """,
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        order=1
    )

    print("\n🎓 [3/4] Matriculando usuários existentes nos cursos...")
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

    print(f"✅ Realizadas {count_enrollments} matrículas de teste com sucesso!")

    print("\n🎉 [4/4] POVOAMENTO COMPLETO E FINALIZADO COM SUCESSO!")
    print(f"📊 Resumo do Banco:")
    print(f"   • Cursos Criados: {Course.objects.count()}")
    print(f"   • Módulos Criados: {Module.objects.count()}")
    print(f"   • Aulas Criadas: {Lesson.objects.count()}")
    print(f"   • Quizzes Criados: {Quiz.objects.count()}")
    print(f"   • Perguntas Criadas: {Question.objects.count()}")


if __name__ == "__main__":
    run_populate()