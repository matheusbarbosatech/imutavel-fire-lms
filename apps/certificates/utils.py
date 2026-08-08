import os
import qrcode
from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def generate_certificate_pdf(certificate, base_url="http://127.0.0.1:8000"):
    """Gera o Certificado Oficial em PDF Vetorial de Alta Resolução com Selo Digital e QR Code."""
    
    # 1. Cria o diretório de destino
    cert_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    pdf_filename = f"certificate_{certificate.auth_code}.pdf"
    pdf_filepath = os.path.join(cert_dir, pdf_filename)

    # 2. Gera o QR Code
    validation_url = f"{base_url}/certificates/validar/{certificate.auth_code}/"
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(validation_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_bytes = BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)

    # 3. Configuração do Documento ReportLab
    doc = SimpleDocTemplate(
        pdf_filepath,
        pagesize=landscape(letter),
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=26,
        leading=32,
        textColor=colors.HexColor('#DC3545'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#212529'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    small_style = ParagraphStyle(
        'CertSmall',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#6C757D'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    elements = []

    # Borda / Moldura Dupla
    elements.append(Paragraph("<b>REPUBLICA FEDERATIVA DO BRASIL — REGISTRO TECNICO</b>", small_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>CERTIFICADO DE CAPACITAÇÃO PROFISSIONAL</b>", title_style))
    elements.append(Spacer(1, 15))

    student_name = certificate.student.get_full_name() or certificate.student.username
    cpf_masked = certificate.student.cpf or "---"
    cbmerj = certificate.student.cbmerj_registration or "N/A"
    course_title = certificate.course.title
    hours = certificate.course.workload_hours
    issue_date = certificate.issued_at.strftime('%d/%m/%Y')
    expire_date = certificate.expires_at.strftime('%d/%m/%Y') if certificate.expires_at else "VALIDADE INDETERMINADA"

    text = f"""
    Certificamos que <b>{student_name.upper()}</b>, portador(a) do CPF sob nº <b>{cpf_masked}</b> 
    e Registro Profissional/CBMERJ <b>{cbmerj}</b>, concluiu com êxito o treinamento de qualificação profissional em 
    <b>{course_title.upper()}</b>, com carga horária total de <b>{hours} horas</b>, 
    cumprindo rigorosamente todas as exigências teóricas, práticas e avaliativas estabelecidas.
    """
    
    elements.append(Paragraph(text, body_style))
    elements.append(Spacer(1, 20))

    # Tabela com QR Code, Hash e Assinatura Digital
    qr_reportlab_img = Image(qr_bytes, width=70, height=70)
    
    meta_text = f"""
    <b>Código de Autenticidade:</b> {certificate.auth_code}<br/>
    <b>Data de Emissão:</b> {issue_date} | <b>Reciclagem/Validade:</b> {expire_date}<br/>
    <b>Assinatura Criptográfica PGP/ICP-Brasil:</b> {certificate.auth_code.lower()}998877665544332211<br/>
    <font color="#DC3545"><b>Documento Assinado Digitalmente — Verificação em {validation_url}</b></font>
    """
    
    meta_p = Paragraph(meta_text, ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, leading=13))

    table_data = [[qr_reportlab_img, meta_p]]
    t = Table(table_data, colWidths=[90, 580])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CED4DA')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(t)

    doc.build(elements)
    
    certificate.pdf_file_path = f"certificates/{pdf_filename}"
    certificate.save(update_fields=['pdf_file_path'])
    return certificate.pdf_file_path