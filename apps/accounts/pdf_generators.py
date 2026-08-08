import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.conf import settings
from django.utils import timezone


def generate_declaration_pdf(user, doc_type_code, course_name="Curso Regular de Qualificação"):
    """
    Gera os PDFs Oficiais Institucionais:
      - MATRICULA: Declaração de Matrícula Ativa
      - FREQUENCIA: Comprovante de Frequência
      - HISTORICO: Histórico Escolar
      - HOMOLOGACAO: Declaração de Aguardando Homologação (30 a 90 dias)
    """
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'declarations')
    os.makedirs(pdf_dir, exist_ok=True)
    filename = f"declaracao_{doc_type_code}_{user.id}.pdf"
    file_path = os.path.join(pdf_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('DeclTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor('#DC3545'), spaceAfter=15)
    body_style = ParagraphStyle('DeclBody', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=18, spaceAfter=12)

    titles = {
        'MATRICULA': 'DECLARAÇÃO DE MATRÍCULA ATIVA',
        'FREQUENCIA': 'COMPROVANTE DE FREQUÊNCIA E ENGAJAMENTO',
        'HISTORICO': 'HISTÓRICO ESCOLAR E DESEMPENHO TÉCNICO',
        'HOMOLOGACAO': 'DECLARAÇÃO DE AGUARDANDO HOMOLOGAÇÃO (CBMERJ / MTE)'
    }

    doc_title = titles.get(doc_type_code, 'DECLARAÇÃO INSTITUCIONAL')
    today_str = timezone.now().strftime('%d de %B de %Y')
    full_name = (user.get_full_name() or user.username).upper()
    cpf = user.cpf or "---"
    cbmerj = user.cbmerj_registration or "Em Cadastramento"

    if doc_type_code == 'HOMOLOGACAO':
        text_content = (
            f"Declaramos para os devidos fins de direito e comprovação junto a órgãos fiscalizadores (CBMERJ / MTE / Contratantes) que "
            f"<b>{full_name}</b>, inscrito(a) no CPF sob o nº <b>{cpf}</b>, concluiu com aproveitamento o treinamento do curso <b>{course_name}</b>.<br/><br/>"
            f"Ressaltamos que a documentação oficial física encontra-se em fase de <b>processamento e homologação institucional no prazo de 30 a 90 dias úteis</b>, "
            f"estando o(a) aluno(a) devidamente apto(a) para o exercício das atividades operacionais."
        )
    elif doc_type_code == 'MATRICULA':
        text_content = (
            f"Declaramos que <b>{full_name}</b>, portador(a) do CPF nº <b>{cpf}</b>, encontra-se regularmente matriculado(a) e ativo(a) "
            f"na plataforma IMUTÁVEL FIRE LMS no treinamento <b>{course_name}</b>."
        )
    else:
        text_content = (
            f"Declaramos que <b>{full_name}</b>, CPF nº <b>{cpf}</b>, cumpre a carga horária estabelecida para o curso <b>{course_name}</b> "
            f"com acesso registrado aos conteúdos programáticos."
        )

    elements = [
        Paragraph("<b>IMUTÁVEL FIRE — ENSINO OPERACIONAL</b>", styles['Heading2']),
        Spacer(1, 10),
        Paragraph(doc_title, title_style),
        Spacer(1, 15),
        Paragraph(text_content, body_style),
        Spacer(1, 40),
        Paragraph(f"Rio de Janeiro, {today_str}.", body_style),
        Spacer(1, 50),
        Paragraph("____________________________________________________<br/><b>SECRETARIA ACADÊMICA — IMUTÁVEL FIRE</b>", ParagraphStyle('Sign', alignment=1, fontName='Helvetica-Bold', fontSize=10))
    ]

    doc.build(elements)
    return f"declarations/{filename}"