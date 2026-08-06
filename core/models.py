import uuid
from django.db import models
from validate_docbr import CPF

def validate_cpf(value):
    if not CPF().validate(value.replace('.', '').replace('-', '')):
        raise ValueError('CPF inválido.')
    return value

class Matricula(models.Model):
    STATUS = [('pending', 'Pendente'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField('Nome Completo', max_length=255)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[validate_cpf])
    rg = models.CharField('RG', max_length=50)
    nascimento = models.DateField('Data de Nascimento')
    email = models.EmailField('E-mail')
    telefone = models.CharField('Telefone', max_length=20)
    endereco = models.TextField('Endereço')
    aceitou_termos = models.BooleanField('Aceitou os termos', default=False)
    ip_registro = models.GenericIPAddressField('IP de Registro', blank=True, null=True)
    user_agent = models.CharField('Navegador/Dispositivo', max_length=500, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS, default='pending')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Matrícula'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.nome} ({self.cpf})"

class Documento(models.Model):
    # ✅ REMOVIDO 'foto' dos tipos
    TIPOS = [('rg', 'RG'), ('cpf', 'CPF')]
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='docs')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPOS)
    # ✅ MUDANÇA CRÍTICA: CharField em vez de FileField
    arquivo = models.CharField('Caminho do Arquivo', max_length=500, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.matricula.nome}"