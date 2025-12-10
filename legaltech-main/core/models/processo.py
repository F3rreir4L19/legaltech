from django.db import models
from .usuario import Usuario, Escritorio
from .cliente import Cliente

class Processo(models.Model):
    """Processo judicial completo"""
    
    TIPO_CHOICES = [
        ('trabalhista', 'Trabalhista'),
        ('civil', 'Cível'),
        ('criminal', 'Criminal'),
        ('previdenciario', 'Previdenciário'),
        ('tributario', 'Tributário'),
        ('familia', 'Família'),
        ('consumidor', 'Consumidor'),
        ('administrativo', 'Administrativo'),
        ('ambiental', 'Ambiental'),
        ('outro', 'Outro'),
    ]
    
    SITUACAO_CHOICES = [
        ('ativo', 'Ativo'),
        ('arquivado', 'Arquivado'),
        ('suspenso', 'Suspenso'),
        ('baixado', 'Baixado'),
        ('encerrado', 'Encerrado'),
        ('transitado', 'Transitado em Julgado'),
    ]
    
    escritorio = models.ForeignKey(
        Escritorio, 
        on_delete=models.CASCADE, 
        related_name='processos'
    )
    numero_cnj = models.CharField(
        'Número CNJ', 
        max_length=25, 
        unique=True,
        help_text='Formato: NNNNNNN-DD.AAAA.J.TR.OOOO'
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='processos'
    )
    advogado_responsavel = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT, 
        related_name='processos_responsavel',
        limit_choices_to={'tipo__in': ['admin', 'socio', 'advogado']}
    )
    
    # Informações do processo
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='civil')
    situacao = models.CharField('Situação', max_length=20, choices=SITUACAO_CHOICES, default='ativo')
    
    # Informações judiciais
    vara = models.CharField('Vara', max_length=200)
    comarca = models.CharField('Comarca', max_length=100)
    tribunal = models.CharField('Tribunal', max_length=100)
    valor_causa = models.DecimalField(
        'Valor da Causa', 
        max_digits=15, 
        decimal_places=2,
        default=0.00
    )
    data_distribuicao = models.DateField('Data de Distribuição')
    data_arquivamento = models.DateField('Data de Arquivamento', null=True, blank=True)
    data_encerramento = models.DateField('Data de Encerramento', null=True, blank=True)
    
    # Partes envolvidas
    polo_ativo = models.TextField('Polo Ativo (Autor/Requerente)', blank=True)
    polo_passivo = models.TextField('Polo Passivo (Réu/Requerido)', blank=True)
    testemunhas = models.TextField('Testemunhas', blank=True)
    
    # Descrição
    objeto = models.TextField('Objeto do Processo')
    honorarios = models.DecimalField(
        'Honorários Contratados',
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    # Controle
    observacoes = models.TextField('Observações', blank=True)
    tags = models.CharField('Tags', max_length=200, blank=True, help_text='Separadas por vírgula')
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='processos_criados'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='processos_atualizados'
    )
    
    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-data_distribuicao', '-criado_em']
        indexes = [
            models.Index(fields=['numero_cnj']),
            models.Index(fields=['escritorio', 'situacao']),
            models.Index(fields=['cliente', 'situacao']),
            models.Index(fields=['advogado_responsavel', 'situacao']),
            models.Index(fields=['tipo', 'situacao']),
        ]
    
    def __str__(self):
        return f"{self.numero_cnj} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        # Validação básica do número CNJ
        if self.numero_cnj and '-' in self.numero_cnj and '.' in self.numero_cnj:
            # Formato básico: 0000000-00.0000.0.00.0000
            pass
        super().save(*args, **kwargs)
    
    @property
    def dias_ate_proxima_audiencia(self):
        """Calcula dias até a próxima audiência"""
        from django.utils import timezone
        audiencias = self.audiencias.filter(data__gte=timezone.now().date()).order_by('data')
        if audiencias.exists():
            return (audiencias.first().data - timezone.now().date()).days
        return None
    
    @property
    def total_custas(self):
        """Calcula total de custas do processo"""
        return self.custas.aggregate(total=models.Sum('valor'))['total'] or 0


class Andamento(models.Model):
    """Andamentos processuais"""
    
    TIPO_CHOICES = [
        ('audiencia', 'Audiência'),
        ('decisao', 'Decisão'),
        ('sentenca', 'Sentença'),
        ('recurso', 'Recurso'),
        ('intimacao', 'Intimação'),
        ('citacao', 'Citação'),
        ('publicacao', 'Publicação'),
        ('protocolo', 'Protocolo'),
        ('outro', 'Outro'),
    ]
    
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='andamentos'
    )
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='outro')
    data = models.DateField('Data do Andamento')
    descricao = models.TextField('Descrição')
    
    # Detalhes
    juiz = models.CharField('Juiz', max_length=200, blank=True)
    resultado = models.TextField('Resultado', blank=True)
    proximo_prazo = models.DateField('Próximo Prazo', null=True, blank=True)
    
    # Documentos
    documento = models.FileField(
        'Documento', 
        upload_to='andamentos/%Y/%m/', 
        null=True, 
        blank=True
    )
    numero_documento = models.CharField('Número do Documento', max_length=100, blank=True)
    
    # Controle
    capturado_automatico = models.BooleanField('Capturado Automaticamente', default=False)
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='andamentos_registrados'
    )
    importante = models.BooleanField('Importante', default=False)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Andamento'
        verbose_name_plural = 'Andamentos'
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['processo', '-data']),
            models.Index(fields=['tipo', 'data']),
        ]
    
    def __str__(self):
        return f"{self.processo.numero_cnj} - {self.get_tipo_display()} - {self.data}"
    
    @property
    def resumo(self):
        """Resumo do andamento (50 primeiros caracteres)"""
        return self.descricao[:50] + '...' if len(self.descricao) > 50 else self.descricao


class Prazo(models.Model):
    """Prazos processuais com alertas"""
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    
    TIPO_CHOICES = [
        ('procesual', 'Processual'),
        ('administrativo', 'Administrativo'),
        ('contratual', 'Contratual'),
        ('legal', 'Legal'),
        ('outro', 'Outro'),
    ]
    
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='prazos'
    )
    andamento = models.ForeignKey(
        Andamento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='prazos_gerados'
    )
    
    # Informações do prazo
    titulo = models.CharField('Título', max_length=200)
    descricao = models.TextField('Descrição')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='procesual')
    prioridade = models.CharField('Prioridade', max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='pendente')
    
    # Datas
    data_limite = models.DateField('Data Limite')
    data_conclusao = models.DateField('Data de Conclusão', null=True, blank=True)
    data_lembrete = models.DateField('Data do Lembrete', null=True, blank=True)
    
    # Responsáveis
    responsavel = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='prazos_responsavel'
    )
    atribuido_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='prazos_atribuidos',
        blank=True
    )
    
    # Documentos
    documento = models.FileField(
        'Documento', 
        upload_to='prazos/%Y/%m/', 
        null=True, 
        blank=True
    )
    observacoes = models.TextField('Observações', blank=True)
    
    # Controle
    dias_antecedencia_alerta = models.IntegerField(
        'Dias de Antecedência para Alerta',
        default=3,
        help_text='Dias antes do vencimento para enviar alertas'
    )
    alertas_enviados = models.IntegerField('Alertas Enviados', default=0)
    calculado_automatico = models.BooleanField('Calculado Automaticamente', default=False)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Prazo'
        verbose_name_plural = 'Prazos'
        ordering = ['data_limite', '-prioridade']
        indexes = [
            models.Index(fields=['processo', 'status', 'data_limite']),
            models.Index(fields=['responsavel', 'status', 'data_limite']),
            models.Index(fields=['status', 'data_limite']),
        ]
    
    def __str__(self):
        return f"{self.processo.numero_cnj} - {self.titulo} - {self.data_limite}"
    
    @property
    def esta_vencido(self):
        """Verifica se o prazo está vencido"""
        from django.utils import timezone
        return self.status == 'pendente' and self.data_limite < timezone.now().date()
    
    @property
    def dias_restantes(self):
        """Calcula dias restantes para o prazo"""
        from django.utils import timezone
        if self.status != 'pendente':
            return None
        delta = self.data_limite - timezone.now().date()
        return delta.days
    
    @property
    def precisa_alerta(self):
        """Verifica se precisa enviar alerta"""
        if self.status != 'pendente':
            return False
        
        from django.utils import timezone
        dias_restantes = self.dias_restantes
        return dias_restantes is not None and dias_restantes <= self.dias_antecedencia_alerta
    
    def marcar_concluido(self, usuario):
        """Marca o prazo como concluído"""
        from django.utils import timezone
        self.status = 'concluido'
        self.data_conclusao = timezone.now().date()
        self.atualizado_por = usuario
        self.save()


class Audiencia(models.Model):
    """Audiências do processo"""
    
    TIPO_CHOICES = [
        ('conciliação', 'Conciliação'),
        ('instrucao', 'Instrução'),
        ('julgamento', 'Julgamento'),
        ('sustentacao', 'Sustentação Oral'),
        ('outro', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('adiada', 'Adiada'),
        ('cancelada', 'Cancelada'),
    ]
    
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='audiencias')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='conciliação')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='agendada')
    
    # Informações da audiência
    data = models.DateField('Data da Audiência')
    hora = models.TimeField('Hora', null=True, blank=True)
    local = models.CharField('Local', max_length=300)
    sala = models.CharField('Sala', max_length=100, blank=True)
    juiz = models.CharField('Juiz', max_length=200, blank=True)
    
    # Controle
    presentes = models.TextField('Presentes', blank=True)
    resultado = models.TextField('Resultado', blank=True)
    observacoes = models.TextField('Observações', blank=True)
    
    # Documentos
    ata = models.FileField('Ata da Audiência', upload_to='audiencias/', null=True, blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Audiência'
        verbose_name_plural = 'Audiências'
        ordering = ['data', 'hora']
        indexes = [
            models.Index(fields=['processo', 'data']),
            models.Index(fields=['status', 'data']),
        ]
    
    def __str__(self):
        return f"Audiência - {self.processo.numero_cnj} - {self.data}"