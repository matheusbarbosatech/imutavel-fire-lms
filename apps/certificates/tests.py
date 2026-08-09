from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.courses.models import Course
from apps.certificates.models import Certificate
from apps.certificates.utils import issue_certificate_for_user, generate_certificate_pdf
from apps.certificates.card_generator import generate_pvc_card_pdf

User = get_user_model()

class CertificatesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='bombeiro@test.com', 
            email='bombeiro@test.com', 
            password='Password123', 
            first_name='Carlos',
            cpf='123.456.789-00',
            cbmerj_registration='CBMERJ-12345'
        )
        self.course = Course.objects.create(title='Resgate Técnico em Altura', description='Treinamento de Altura')
        self.certificate = Certificate.objects.create(
            student=self.user,
            course=self.course,
            code='CERT-TEST-001'
        )

    def test_pdf_generation(self):
        rel_path = generate_certificate_pdf(self.certificate)
        self.assertTrue(rel_path.endswith('.pdf'))

    def test_pvc_card_generation(self):
        rel_path = generate_pvc_card_pdf(self.user, self.certificate)
        self.assertTrue('carteirinha_' in rel_path)

    def test_certificate_download_views(self):
        self.client.login(username='bombeiro@test.com', password='Password123')
        response_cert = self.client.get(f'/certificates/download-pdf/{self.certificate.id}/')
        self.assertEqual(response_cert.status_code, 200)

        response_card = self.client.get(f'/certificates/pvc-card/{self.certificate.id}/')
        self.assertEqual(response_card.status_code, 200)
