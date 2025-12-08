from django.db import models
from .usuario import Usuario, Escritorio
from .cliente import Cliente
from .processo import Processo

class Financeiro(models.Model):
    """Sistema financeiro completo para escritório jurídico"""
    
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('transferencia', 'Transferência'),
    ]
    
    CATEGORIA_RECEITA_CHOICES = [
        ('honorarios', 'Honorários Advocatícios'),
        ('parcelamento', 'Parcelamento'),
        ('acordo', 'Acordo'),
        ('indenizacao', 'Indenização'),
        ('custas', 'Custas Recebidas'),
        ('reembolso', 'Reembolso'),
        ('multa', 'Multa'),
        ('outra_receita', 'Outra Receita'),
    ]
    
    CATEGORIA_DESPESA_CHOICES = [
        ('custas_judiciais', 'Custas Judiciais'),
        ('pericias', 'Perícias'),
        ('cartorio', 'Cartório'),
        ('publicacao', 'Publicação'),
        ('correio', 'Correio'),
        ('viagem', 'Viagens'),
        ('material', 'Material'),
        ('salario', 'Salários'),
        ('aluguel', 'Aluguel'),
        ('energia', 'Energia'),
        ('agua', 'Água'),
        ('telefone', 'Telefone/Internet'),
        ('software', 'Softwares'),
        ('marketing', 'Marketing'),
        ('outra_despesa', 'Outra Despesa'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago/Recebido'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
        ('parcial', 'Parcialmente Pago'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('transferencia', 'Transferência Bancária'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('boleto', 'Boleto'),
        ('cheque', 'Cheque'),
        ('deposito', 'Depósito'),
        ('outro', 'Outro'),
    ]
    
    PERIODICIDADE_CHOICES = [
        ('unica', 'Única'),
        ('mensal', 'Mensal'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
    ]
    
    escritorio = models.ForeignKey(Escritorio, on_delete=models.CASCADE, related_name='financeiro')
    
    # Relacionamentos
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='financeiro',
        null=True, 
        blank=True
    )
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.SET_NULL, 
        related_name='financeiro',
        null=True, 
        blank=True
    )
    
    # Informações básicas
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES)
    
    # Categoria dinâmica baseada no tipo
    categoria = models.CharField('Categoria', max_length=30)
    
    # Descrição e valores
    descricao = models.CharField('Descrição', max_length=300)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    valor_pago = models.DecimalField('Valor Pago', max_digits=12, decimal_places=2, default=0.00)
    
    # Datas
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento/Recebimento', null=True, blank=True)
    data_competencia = models.DateField('Data de Competência', null=True, blank=True)
    
    # Status e pagamento
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='pendente')
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, blank=True)
    periodicidade = models.CharField('Periodicidade', max_length=15, choices=PERIODICIDADE_CHOICES, default='unica')
    
    # Informações financeiras
    banco = models.CharField('Banco', max_length=100, blank=True)
    agencia = models.CharField('Agência', max_length=10, blank=True)
    conta = models.CharField('Conta', max_length=20, blank=True)
    pix = models.CharField('Chave PIX', max_length=100, blank=True)
    
    # Documentos
    comprovante = models.FileField('Comprovante', upload_to='comprovantes/%Y/%m/', null=True, blank=True)
    nota_fiscal = models.FileField('Nota Fiscal', upload_to='notas_fiscais/%Y/%m/', null=True, blank=True)
    contrato = models.FileField('Contrato/Recibo', upload_to='contratos/%Y/%m/', null=True, blank=True)
    
    # Controle
    parcela_atual = models.IntegerField('Parcela Atual', default=1)
    total_parcelas = models.IntegerField('Total de Parcelas', default=1)
    observacoes = models.TextField('Observações', blank=True)
    enviar_lembrete = models.BooleanField('Enviar Lembrete', default=True)
    dias_lembrete = models.IntegerField('Dias para Lembrete', default=3)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='financeiro_criado'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='financeiro_atualizado',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Lançamento Financeiro'
        verbose_name_plural = 'Lançamentos Financeiros'
        ordering = ['-data_vencimento', '-criado_em']
        indexes = [
            models.Index(fields=['escritorio', 'tipo', 'status']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['processo', 'tipo']),
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['categoria', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao} - R$ {self.valor}"
    
    def save(self, *args, **kwargs):
        # Determina categoria baseada no tipo
        if not self.categoria:
            if self.tipo == 'receita':
                self.categoria = 'honorarios'
            elif self.tipo == 'despesa':
                self.categoria = 'custas_judiciais'
        
        # Atualiza status baseado no pagamento
        if self.valor_pago >= self.valor and self.valor > 0:
            self.status = 'pago'
            if not self.data_pagamento:
                from django.utils import timezone
                self.data_pagamento = timezone.now().date()
        elif self.valor_pago > 0:
            self.status = 'parcial'
        
        super().save(*args, **kwargs)
    
    @property
    def valor_pendente(self):
        """Calcula valor pendente"""
        return self.valor - self.valor_pago
    
    @property
    def percentual_pago(self):
        """Calcula percentual pago"""
        if self.valor == 0:
            return 100
        return (self.valor_pago / self.valor) * 100
    
    @property
    def esta_vencido(self):
        """Verifica se está vencido"""
        from django.utils import timezone
        return (
            self.status in ['pendente', 'parcial'] and 
            self.data_vencimento < timezone.now().date()
        )
    
    @property
    def precisa_lembrete(self):
        """Verifica se precisa enviar lembrete"""
        if not self.enviar_lembrete or self.status == 'pago':
            return False
        
        from django.utils import timezone
        delta = self.data_vencimento - timezone.now().date()
        return 0 <= delta.days <= self.dias_lembrete
    
    def gerar_proxima_parcela(self):
        """Gera próxima parcela para lançamentos parcelados"""
        if self.parcela_atual < self.total_parcelas:
            from datetime import timedelta
            from django.utils import timezone
            
            # Calcula intervalo baseado na periodicidade
            intervalos = {
                'mensal': 30,
                'bimestral': 60,
                'trimestral': 90,
                'semestral': 180,
                'anual': 365,
            }
            
            dias_intervalo = intervalos.get(self.periodicidade, 30)
            nova_data = self.data_vencimento + timedelta(days=dias_intervalo)
            
            # Cria nova parcela
            nova_parcela = Financeiro(
                escritorio=self.escritorio,
                cliente=self.cliente,
                processo=self.processo,
                tipo=self.tipo,
                categoria=self.categoria,
                descricao=f"{self.descricao} - Parcela {self.parcela_atual + 1}/{self.total_parcelas}",
                valor=self.valor / self.total_parcelas,
                data_vencimento=nova_data,
                periodicidade=self.periodicidade,
                parcela_atual=self.parcela_atual + 1,
                total_parcelas=self.total_parcelas,
                criado_por=self.criado_por,
            )
            nova_parcela.save()
            return nova_parcela
        return None


class ContratoHonorarios(models.Model):
    """Contrato de honorários advocatícios"""
    
    TIPO_CHOICES = [
        ('sucesso', 'Honorários de Sucesso'),
        ('fixo', 'Honorários Fixos'),
        ('horista', 'Honorários Horistas'),
        ('misto', 'Misto (Fixo + Sucesso)'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('parcelado', 'Parcelado'),
        ('unico', 'Pagamento Único'),
        ('mensal', 'Mensal'),
    ]
    
    processo = models.OneToOneField(
        Processo, 
        on_delete=models.CASCADE, 
        related_name='contrato_honorarios'
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contratos')
    
    # Tipo de contrato
    tipo = models.CharField('Tipo de Contrato', max_length=20, choices=TIPO_CHOICES, default='sucesso')
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='parcelado')
    
    # Valores
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2)
    percentual_sucesso = models.DecimalField(
        'Percentual de Sucesso', 
        max_digits=5, 
        decimal_places=2,
        default=0.00,
        help_text='Se for tipo sucesso ou misto'
    )
    valor_hora = models.DecimalField(
        'Valor por Hora', 
        max_digits=8, 
        decimal_places=2,
        default=0.00,
        help_text='Se for tipo horista'
    )
    
    # Parcelamento
    numero_parcelas = models.IntegerField('Número de Parcelas', default=1)
    dia_vencimento = models.IntegerField(
        'Dia de Vencimento',
        default=10,
        help_text='Dia do mês para vencimento das parcelas'
    )
    
    # Cláusulas
    clausulas = models.TextField('Cláusulas do Contrato')
    observacoes = models.TextField('Observações', blank=True)
    
    # Documentos
    contrato_pdf = models.FileField(
        'Contrato PDF', 
        upload_to='contratos_honorarios/%Y/%m/', 
        null=True, 
        blank=True
    )
    assinado = models.BooleanField('Contrato Assinado', default=False)
    data_assinatura = models.DateField('Data de Assinatura', null=True, blank=True)
    
    # Status
    ativo = models.BooleanField('Contrato Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Contrato de Honorários'
        verbose_name_plural = 'Contratos de Honorários'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Contrato - {self.processo.numero_cnj} - R$ {self.valor_total}"
    
    @property
    def valor_parcela(self):
        """Calcula valor da parcela"""
        if self.numero_parcelas > 0:
            return self.valor_total / self.numero_parcelas
        return self.valor_total
    
    def gerar_parcelas(self):
        """Gera parcelas do contrato"""
        from datetime import date
        from django.utils import timezone
        
        # Deleta parcelas existentes
        self.parcelas.all().delete()
        
        # Cria novas parcelas
        for i in range(self.numero_parcelas):
            # Calcula data de vencimento
            if i == 0:
                data_vencimento = timezone.now().date()
            else:
                # Próximo mês
                import calendar
                ano_atual = timezone.now().year
                mes_atual = timezone.now().month + i
                
                # Ajusta ano se passar de dezembro
                while mes_atual > 12:
                    mes_atual -= 12
                    ano_atual += 1
                
                # Último dia do mês se o dia de vencimento for maior
                ultimo_dia = calendar.monthrange(ano_atual, mes_atual)[1]
                dia_vencimento = min(self.dia_vencimento, ultimo_dia)
                
                data_vencimento = date(ano_atual, mes_atual, dia_vencimento)
            
            # Cria parcela no financeiro
            Financeiro.objects.create(
                escritorio=self.processo.escritorio,
                cliente=self.cliente,
                processo=self.processo,
                tipo='receita',
                categoria='honorarios',
                descricao=f"Honorários - Parcela {i+1}/{self.numero_parcelas}",
                valor=self.valor_parcela,
                data_vencimento=data_vencimento,
                status='pendente',
                periodicidade='mensal' if self.numero_parcelas > 1 else 'unica',
                parcela_atual=i+1,
                total_parcelas=self.numero_parcelas,
                criado_por=self.criado_por,
            )


class ParcelaHonorarios(models.Model):
    """Parcelas de honorários"""
    contrato = models.ForeignKey(ContratoHonorarios, on_delete=models.CASCADE, related_name='parcelas')
    numero = models.IntegerField('Número da Parcela')
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('atrasada', 'Atrasada'),
        ('cancelada', 'Cancelada'),
    ], default='pendente')
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Parcela de Honorários'
        verbose_name_plural = 'Parcelas de Honorários'
        ordering = ['numero']
        unique_together = ['contrato', 'numero']
    
    def __str__(self):
        return f"Parcela {self.numero} - R$ {self.valor}"