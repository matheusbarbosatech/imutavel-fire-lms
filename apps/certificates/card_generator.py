import os
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, Line
from django.conf import settings


def generate_pvc_card_pdf(user, certificate, base_url="http://127.0.0.1:8000"):
    """
    Gera um PDF em folha A4 com a Credencial Operacional em PVC (Frente e Verso side-by-side)
    com guias e linhas de corte para impressão gráfica e plastificação.
    """
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pvc_cards_pdf')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"carteirinha_{certificate.auth_code}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Tamanho padrão CR-80 em Pontos ReportLab (85.6mm x 54mm -> 242.6pt x 153pt)
    CARD_W = 242.6
    CARD_H = 153.0

    # 1. Gerar QR Code
    validation_url = f"{base_url}/certificates/validar/{certificate.auth_code}/"
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(validation_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_reportlab_img = Image(qr_buffer, width=45, height=45)

    # 2. Processar Foto 3x4 do Aluno
    if user.photo and os.path.exists(user.photo.path):
        student_photo = Image(user.photo.path, width=45, height=55)
    else:
        student_photo = Paragraph("<font color='#888888' size=7><b>SEM FOTO</b></font>", styles['Normal'])

    # Estilos Internos
    style_header = ParagraphStyle('CardH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, textColor=colors.white, leading=8)
    style_sub = ParagraphStyle('CardSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=5.5, textColor=colors.HexColor('#FFD700'), leading=7)
    style_body = ParagraphStyle('CardB', parent=styles['Normal'], fontName='Helvetica', fontSize=5.5, textColor=colors.white, leading=7)
    style_body_bold = ParagraphStyle('CardBB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=6, textColor=colors.white, leading=7)
    style_hash = ParagraphStyle('CardHash', parent=styles['Normal'], fontName='Courier-Bold', fontSize=5, textColor=colors.HexColor('#CCCCCC'), leading=6)

    # Conteúdo Frente
    name = (user.get_full_name() or user.username).upper()
    cpf = user.cpf or "---"
    cbmerj = user.cbmerj_registration or "N/A"
    blood = user.blood_type or "A+"

    front_data = [
        [Paragraph("CREDENCIAL PROFISSIONAL OPERACIONAL", style_header), ""],
        [Paragraph("BOMBEIRO CIVIL & RESGATISTA TÉCNICO", style_sub), ""],
        [student_photo, Paragraph(
            f"<b>NOME:</b> {name}<br/>"
            f"<b>CPF:</b> {cpf}<br/>"
            f"<b>REG. CBMERJ:</b> <font color='#FF4D4D'><b>{cbmerj}</b></font><br/>"
            f"<b>TIPO SANGUÍNEO:</b> <font color='#00E5FF'><b>{blood}</b></font><br/>"
            f"<b>CURSO:</b> {certificate.course.title[:30]}", style_body
        )],
        [Paragraph(f"HASH: {certificate.auth_code}", style_hash), qr_reportlab_img]
    ]

    front_table = Table(front_data, colWidths=[55, CARD_W - 65], rowHeights=[15, 12, 80, 46])
    front_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('BACKGROUND', (0, 0), (1, 1), colors.HexColor('#DC3545')),
        ('BACKGROUND', (0, 2), (1, 3), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Conteúdo Verso
    verso_data = [
        [Paragraph("VALIDAÇÃO TÉCNICA E TERMO DE USO", style_header)],
        [Paragraph(
            "Documento pessoal e intransferível, emitido conforme NBR 14608 e Diretrizes do CBMERJ.<br/><br/>"
            f"<b>EMISSÃO:</b> {certificate.issued_at.strftime('%d/%m/%Y')}<br/>"
            f"<b>VALIDADE / RECICLAGEM:</b> {certificate.expires_at.strftime('%d/%m/%Y') if certificate.expires_at else 'INDETERMINADA'}<br/><br/>"
            "Validação pública em tempo real via QR Code ou no portal oficial da instituição.", style_body
        )],
        [Paragraph("IMUTÁVEL FIRE — SISTEMA OPERACIONAL LMS", style_sub)]
    ]

    verso_table = Table(verso_data, colWidths=[CARD_W], rowHeights=[20, 113, 20])
    verso_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#1E293B')),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#0F172A')),
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#DC3545')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Tabela de Impressão Lado a Lado com Linha de Corte
    master_table = Table([[front_table, Paragraph("<font size=8 color='#888888'>| LINHA DE CORTE |</font>", style_body), verso_table]],
                         colWidths=[CARD_W, 40, CARD_W])
    master_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#999999')),
        ('BOX', (2, 0), (2, 0), 0.5, colors.HexColor('#999999')),
    ]))

    elements = [
        Paragraph("<b>IMUTÁVEL FIRE — GUIA DE IMPRESSÃO DA CREDENCIAL PVC</b>", styles['Title']),
        Paragraph("Imprima este documento em papel couchê 300g ou folha PVC A4. Recorte nas linhas indicadas e dobre para plastificação.", styles['Normal']),
        Spacer(1, 30),
        master_table
    ]

    doc.build(elements)
    return f"pvc_cards_pdf/{pdf_filename}"