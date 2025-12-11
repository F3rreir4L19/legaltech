from django.db import models
from django.utils.translation import gettext_lazy as _
from .usuario import Usuario, Escritorio


class Cliente(models.Model):
    """Cliente do escritório"""
    
    TIPO_CHOICES = [
        ('pf', _('Pessoa Física')),
        ('pj', _('Pessoa Jurídica')),
    ]
    
    ESTADO_CIVIL_CHOICES = [
        ('solteiro', _('Solteiro(a)')),
        ('casado', _('Casado(a)')),
        ('divorciado', _('Divorciado(a)')),
        ('viuvo', _('Viúvo(a)')),
        ('separado', _('Separado(a)')),
        ('uniao_estavel', _('União Estável')),
    ]
    
    escritorio = models.ForeignKey(
        Escritorio, 
        on_delete=models.CASCADE, 
        related_name='clientes'
    )
    
    # Informações básicas
    tipo = models.CharField(_('Tipo'), max_length=2, choices=TIPO_CHOICES, default='pf')
    nome = models.CharField(_('Nome/Razão Social'), max_length=200)
    nome_social = models.CharField(_('Nome Social'), max_length=200, blank=True)
    apelido = models.CharField(_('Apelido'), max_length=100, blank=True)
    
    # Documentos
    cpf_cnpj = models.CharField(_('CPF/CNPJ'), max_length=18, blank=True)
    rg = models.CharField(_('RG'), max_length=20, blank=True)
    orgao_emissor = models.CharField(_('Órgão Emissor'), max_length=50, blank=True)
    data_emissao_rg = models.DateField(_('Data de Emissão RG'), null=True, blank=True)
    inscricao_estadual = models.CharField(_('Inscrição Estadual'), max_length=20, blank=True)
    inscricao_municipal = models.CharField(_('Inscrição Municipal'), max_length=20, blank=True)
    
    # Informações pessoais
    data_nascimento = models.DateField(_('Data de Nascimento'), null=True, blank=True)
    estado_civil = models.CharField(_('Estado Civil'), max_length=20, choices=ESTADO_CIVIL_CHOICES, blank=True)
    nacionalidade = models.CharField(_('Nacionalidade'), max_length=100, default='Brasileira')
    naturalidade = models.CharField(_('Naturalidade'), max_length=100, blank=True)
    profissao = models.CharField(_('Profissão'), max_length=100, blank=True)
    empresa_trabalho = models.CharField(_('Empresa onde Trabalha'), max_length=200, blank=True)
    cargo = models.CharField(_('Cargo'), max_length=100, blank=True)
    renda_mensal = models.DecimalField(
        _('Renda Mensal'), 
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Contato
    telefone = models.CharField(_('Telefone'), max_length=20)
    celular = models.CharField(_('Celular'), max_length=20, blank=True)
    email = models.EmailField(_('E-mail'), blank=True)
    email_secundario = models.EmailField(_('E-mail Secundário'), blank=True)
    
    # Endereço
    cep = models.CharField(_('CEP'), max_length=10)
    endereco = models.CharField(_('Endereço'), max_length=200)
    numero = models.CharField(_('Número'), max_length=10)
    complemento = models.CharField(_('Complemento'), max_length=100, blank=True)
    bairro = models.CharField(_('Bairro'), max_length=100)
    cidade = models.CharField(_('Cidade'), max_length=100)
    estado = models.CharField(_('Estado'), max_length=2, choices=[
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ])
    
    # Informações bancárias (para repasses)
    banco = models.CharField(_('Banco'), max_length=100, blank=True)
    agencia = models.CharField(_('Agência'), max_length=10, blank=True)
    conta = models.CharField(_('Conta'), max_length=20, blank=True)
    tipo_conta = models.CharField(_('Tipo de Conta'), max_length=20, choices=[
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
        ('salario', 'Conta Salário'),
    ], blank=True)
    pix = models.CharField(_('Chave PIX'), max_length=100, blank=True)
    
    # Contato de emergência
    contato_emergencia_nome = models.CharField(_('Nome do Contato de Emergência'), max_length=200, blank=True)
    contato_emergencia_parentesco = models.CharField(_('Parentesco'), max_length=100, blank=True)
    contato_emergencia_telefone = models.CharField(_('Telefone do Contato de Emergência'), max_length=20, blank=True)
    
    # Informações adicionais
    como_conheceu = models.CharField(_('Como Conheceu o Escritório'), max_length=200, blank=True)
    indicado_por = models.CharField(_('Indicado por'), max_length=200, blank=True)
    observacoes = models.TextField(_('Observações'), blank=True)
    restricoes = models.TextField(_('Restrições/Alertas'), blank=True)
    foto = models.ImageField(_('Foto'), upload_to='clientes/', null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(_('Ativo'), default=True)
    cliente_preferencial = models.BooleanField(_('Cliente Preferencial'), default=False)
    receber_newsletter = models.BooleanField(_('Receber Newsletter'), default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    criado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='clientes_criados',
        verbose_name=_('Criado por')
    )
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)
    atualizado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='clientes_atualizados',
        verbose_name=_('Atualizado por'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['nome']
        indexes = [
            models.Index(fields=['escritorio', 'nome']),
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['tipo', 'ativo']),
            models.Index(fields=['ativo', 'cliente_preferencial']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.cpf_cnpj})"
    
    def save(self, *args, **kwargs):
        # Formata CPF/CNPJ se fornecido
        if self.cpf_cnpj:
            cpf_cnpj = ''.join(filter(str.isdigit, self.cpf_cnpj))
            if len(cpf_cnpj) == 11:  # CPF
                self.cpf_cnpj = f'{cpf_cnpj[:3]}.{cpf_cnpj[3:6]}.{cpf_cnpj[6:9]}-{cpf_cnpj[9:]}'
            elif len(cpf_cnpj) == 14:  # CNPJ
                self.cpf_cnpj = f'{cpf_cnpj[:2]}.{cpf_cnpj[2:5]}.{cpf_cnpj[5:8]}/{cpf_cnpj[8:12]}-{cpf_cnpj[12:]}'
        
        super().save(*args, **kwargs)
    
    @property
    def idade(self):
        """Calcula idade do cliente"""
        if self.data_nascimento:
            from datetime import date
            today = date.today()
            age = today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
            return age
        return None
    
    @property
    def total_processos(self):
        return self.processos.count()
    
    @property
    def processos_ativos(self):
        return self.processos.filter(situacao='ativo').count()
    
    @property
    def contatos(self):
        """Retorna todos os telefones do cliente"""
        contatos = []
        if self.telefone:
            contatos.append(self.telefone)
        if self.celular:
            contatos.append(self.celular)
        return contatos

class Entrevista(models.Model):
    """Entrevistas/Atendimentos com clientes"""
    
    TIPO_CHOICES = [
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('telefonica', 'Telefônica'),
        ('outro', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada'),
    ]
    
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='entrevistas'
    )
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='entrevistas_realizadas',
        verbose_name=_('Advogado/Responsável')
    )
    
    # Informações básicas
    tipo = models.CharField(_('Tipo de Entrevista'), max_length=20, choices=TIPO_CHOICES, default='presencial')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='agendada')
    
    # Data e hora
    data = models.DateField(_('Data da Entrevista'))
    hora_inicio = models.TimeField(_('Hora de Início'))
    hora_fim = models.TimeField(_('Hora de Fim'), null=True, blank=True)
    
    # Local
    local = models.CharField(_('Local'), max_length=200, blank=True)
    endereco = models.TextField(_('Endereço Completo'), blank=True)
    link_videoconferencia = models.URLField(_('Link da Videoconferência'), max_length=500, blank=True)
    
    # Conteúdo
    assunto = models.CharField(_('Assunto'), max_length=200)
    objetivo = models.TextField(_('Objetivo'), blank=True)
    relato = models.TextField(_('Relato da Entrevista'))
    documentos_apresentados = models.TextField(_('Documentos Apresentados'), blank=True)
    acordos = models.TextField(_('Acordos/Combinações'), blank=True)
    proximos_passos = models.TextField(_('Próximos Passos'), blank=True)
    observacoes = models.TextField(_('Observações'), blank=True)
    
    # Acompanhantes
    acompanhantes = models.TextField(_('Acompanhantes'), blank=True)
    
    # Documentos
    gravacao = models.FileField(_('Gravação'), upload_to='entrevistas/gravacoes/', null=True, blank=True)
    anexos = models.FileField(_('Anexos'), upload_to='entrevistas/anexos/', null=True, blank=True)
    ata = models.FileField(_('Ata/Resumo'), upload_to='entrevistas/atas/', null=True, blank=True)
    
    # Controle
    confimado_por_cliente = models.BooleanField(_('Confirmado pelo Cliente'), default=False)
    cliente_compareceu = models.BooleanField(_('Cliente Compareceu'), default=False)
    gerou_processo = models.BooleanField(_('Gerou Processo'), default=False)
    
    # Auditoria
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Entrevista')
        verbose_name_plural = _('Entrevistas')
        ordering = ['-data', '-hora_inicio']
        indexes = [
            models.Index(fields=['cliente', '-data']),
            models.Index(fields=['usuario', 'status']),
            models.Index(fields=['status', 'data']),
        ]
    
    def __str__(self):
        return f"Entrevista: {self.cliente.nome} - {self.data.strftime('%d/%m/%Y')} - {self.assunto}"
    
    @property
    def duracao(self):
        """Calcula duração da entrevista em minutos"""
        if self.hora_inicio and self.hora_fim:
            from datetime import datetime
            inicio = datetime.combine(self.data, self.hora_inicio)
            fim = datetime.combine(self.data, self.hora_fim)
            duracao = (fim - inicio).seconds // 60
            return duracao
        return None
    
    @property
    def esta_agora(self):
        """Verifica se a entrevista está acontecendo agora"""
        from django.utils import timezone
        from datetime import datetime
        
        if self.status != 'agendada' and self.status != 'confirmada':
            return False
        
        agora = timezone.now()
        data_hora_inicio = datetime.combine(self.data, self.hora_inicio)
        data_hora_fim = datetime.combine(self.data, self.hora_fim) if self.hora_fim else None
        
        if data_hora_fim:
            return data_hora_inicio <= agora <= data_hora_fim
        return data_hora_inicio <= agora