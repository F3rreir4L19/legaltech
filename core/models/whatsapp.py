from django.db import models
from django.utils import timezone
from .usuario import Usuario, Escritorio
from .cliente import Cliente
from .processo import Processo
import json

class WhatsAppConfig(models.Model):
    """Configuração de conexão com WhatsApp"""
    
    PROVIDER_CHOICES = [
        ('evolution', 'Evolution API'),
        ('whapi', 'Whapi.cloud'),
        ('wppconnect', 'WPPConnect'),
        ('official', 'WhatsApp Business API Oficial'),
        ('venom', 'Venom (local)'),
        ('outro', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('desconectado', 'Desconectado'),
        ('conectando', 'Conectando...'),
        ('conectado', 'Conectado'),
        ('qr_code', 'Aguardando QR Code'),
        ('erro', 'Erro na Conexão'),
        ('desconhecido', 'Status Desconhecido'),
    ]
    
    escritorio = models.ForeignKey(
        Escritorio, 
        on_delete=models.CASCADE, 
        related_name='whatsapp_configs'
    )
    
    # Identificação
    nome = models.CharField('Nome da Conexão', max_length=100)
    numero_telefone = models.CharField('Número do WhatsApp', max_length=20)
    provider = models.CharField('Provedor', max_length=20, choices=PROVIDER_CHOICES, default='evolution')
    
    # Credenciais da API
    api_url = models.URLField('URL da API', max_length=500)
    api_key = models.CharField('API Key/Token', max_length=500)
    instance_name = models.CharField('Nome da Instância', max_length=100, blank=True)
    instance_id = models.CharField('ID da Instância', max_length=100, blank=True)
    
    # Configurações de webhook
    webhook_url = models.URLField('URL do Webhook', max_length=500, blank=True)
    webhook_secret = models.CharField('Secret do Webhook', max_length=100, blank=True)
    
    # Status da conexão
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='desconectado')
    qr_code = models.TextField('QR Code (base64)', blank=True)
    qr_code_image = models.ImageField('Imagem do QR Code', upload_to='whatsapp_qr/', null=True, blank=True)
    
    # Logs de erro
    ultimo_erro = models.TextField('Último Erro', blank=True)
    data_ultimo_erro = models.DateTimeField('Data do Último Erro', null=True, blank=True)
    tentativas_conexao = models.IntegerField('Tentativas de Conexão', default=0)
    
    # Controle de conexão
    ultima_conexao = models.DateTimeField('Última Conexão Bem-sucedida', null=True, blank=True)
    tempo_medio_resposta = models.FloatField('Tempo Médio de Resposta (ms)', default=0.0)
    mensagens_enviadas = models.IntegerField('Total de Mensagens Enviadas', default=0)
    mensagens_recebidas = models.IntegerField('Total de Mensagens Recebidas', default=0)
    
    # Configurações de operação
    ativo = models.BooleanField('Ativo', default=True)
    auto_responder = models.BooleanField('Auto Responder', default=False)
    enviar_saudacao = models.BooleanField('Enviar Saudação Automática', default=True)
    saudacao_mensagem = models.TextField('Mensagem de Saudação', blank=True, default='Olá! Como posso ajudar?')
    
    # Permissões de usuários
    usuarios_permitidos = models.ManyToManyField(
        Usuario,
        related_name='whatsapp_configs_permitidas',
        verbose_name='Usuários com Acesso',
        blank=True
    )
    
    # Horário de funcionamento
    horario_inicio = models.TimeField('Horário de Início', default='09:00')
    horario_fim = models.TimeField('Horário de Fim', default='18:00')
    funcionar_fim_semana = models.BooleanField('Funcionar no Fim de Semana', default=False)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='whatsapp_configs_criadas'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração WhatsApp'
        verbose_name_plural = 'Configurações WhatsApp'
        ordering = ['-ativo', '-criado_em']
        unique_together = ['escritorio', 'numero_telefone']
        indexes = [
            models.Index(fields=['escritorio', 'ativo']),
            models.Index(fields=['status', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.numero_telefone}) - {self.get_status_display()}"
    
    @property
    def esta_conectado(self):
        """Verifica se está conectado"""
        return self.status == 'conectado'
    
    @property
    def precisa_qr_code(self):
        """Verifica se precisa de QR Code"""
        return self.status == 'qr_code'
    
    @property
    def em_horario_funcionamento(self):
        """Verifica se está no horário de funcionamento"""
        agora = timezone.now()
        hora_atual = agora.time()
        dia_semana = agora.weekday()  # 0=segunda, 6=domingo
        
        # Verifica fim de semana
        if dia_semana >= 5 and not self.funcionar_fim_semana:
            return False
        
        # Verifica horário
        return self.horario_inicio <= hora_atual <= self.horario_fim
    
    def pode_usar(self, usuario):
        """Verifica se usuário pode usar esta configuração"""
        if usuario.is_superuser:
            return True
        
        if usuario.escritorio != self.escritorio:
            return False
        
        if self.usuarios_permitidos.exists():
            return self.usuarios_permitidos.filter(id=usuario.id).exists()
        
        return usuario.pode_gerenciar_whatsapp
    
    def incrementar_mensagem_enviada(self):
        """Incrementa contador de mensagens enviadas"""
        self.mensagens_enviadas += 1
        self.save(update_fields=['mensagens_enviadas'])
    
    def incrementar_mensagem_recebida(self):
        """Incrementa contador de mensagens recebidas"""
        self.mensagens_recebidas += 1
        self.save(update_fields=['mensagens_recebidas'])


class MensagemWhatsApp(models.Model):
    """Mensagens do WhatsApp"""
    
    TIPO_CHOICES = [
        ('texto', 'Texto'),
        ('imagem', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('documento', 'Documento'),
        ('sticker', 'Sticker'),
        ('contato', 'Contato'),
        ('localizacao', 'Localização'),
        ('link', 'Link'),
        ('outro', 'Outro'),
    ]
    
    DIRECAO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]
    
    STATUS_CHOICES = [
        ('enviando', 'Enviando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('lido', 'Lido'),
        ('erro', 'Erro'),
        ('aguardando', 'Aguardando'),
    ]
    
    whatsapp_config = models.ForeignKey(
        WhatsAppConfig, 
        on_delete=models.CASCADE, 
        related_name='mensagens'
    )
    
    # Relacionamentos
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mensagens_whatsapp'
    )
    processo = models.ForeignKey(
        Processo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mensagens_whatsapp'
    )
    
    # Informações do contato
    numero_contato = models.CharField('Número do Contato', max_length=20)
    nome_contato = models.CharField('Nome do Contato', max_length=100, blank=True)
    contato_id = models.CharField('ID do Contato', max_length=100, blank=True)
    
    # Informações da mensagem
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='texto')
    direcao = models.CharField('Direção', max_length=10, choices=DIRECAO_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='enviado')
    
    # Conteúdo
    conteudo = models.TextField('Conteúdo', blank=True)
    legenda = models.TextField('Legenda', blank=True)
    
    # Mídia
    midia_url = models.URLField('URL da Mídia', max_length=500, blank=True)
    midia_arquivo = models.FileField('Arquivo de Mídia', upload_to='whatsapp_midia/%Y/%m/', null=True, blank=True)
    tipo_midia = models.CharField('Tipo de Mídia', max_length=50, blank=True)
    tamanho_midia = models.IntegerField('Tamanho da Mídia (bytes)', default=0)
    
    # Controle
    lida = models.BooleanField('Lida', default=False)
    respondida_bot = models.BooleanField('Respondida por Bot', default=False)
    usuario_responsavel = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='mensagens_whatsapp_responsaveis'
    )
    
    # IDs e referências
    message_id = models.CharField('ID da Mensagem', max_length=200, blank=True)
    message_id_externo = models.CharField('ID Externo', max_length=200, blank=True)
    mensagem_respondida = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respostas'
    )
    
    # Metadados
    latitude = models.FloatField('Latitude', null=True, blank=True)
    longitude = models.FloatField('Longitude', null=True, blank=True)
    duracao_audio = models.IntegerField('Duração do Áudio (segundos)', null=True, blank=True)
    
    # Temporizador
    tempo_envio = models.DateTimeField('Tempo de Envio', null=True, blank=True)
    tempo_entrega = models.DateTimeField('Tempo de Entrega', null=True, blank=True)
    tempo_leitura = models.DateTimeField('Tempo de Leitura', null=True, blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Mensagem WhatsApp'
        verbose_name_plural = 'Mensagens WhatsApp'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['whatsapp_config', 'numero_contato', '-criado_em']),
            models.Index(fields=['cliente', '-criado_em']),
            models.Index(fields=['direcao', 'status', 'lida']),
            models.Index(fields=['message_id']),
        ]
    
    def __str__(self):
        direcao = "→" if self.direcao == 'saida' else "←"
        return f"{direcao} {self.numero_contato}: {self.conteudo[:50]}..."
    
    def save(self, *args, **kwargs):
        # Se for mensagem de saída e não tiver usuário responsável, tenta definir
        if self.direcao == 'saida' and not self.usuario_responsavel:
            # Aqui você pode adicionar lógica para definir o usuário baseado no contexto
            pass
        
        # Se for mensagem de entrada, tenta vincular a cliente
        if self.direcao == 'entrada' and not self.cliente:
            self._vincular_cliente()
        
        super().save(*args, **kwargs)
    
    def _vincular_cliente(self):
        """Tenta vincular a mensagem a um cliente existente"""
        try:
            # Tenta encontrar por número de telefone
            cliente = Cliente.objects.filter(
                telefone__contains=self.numero_contato[-8:]  # Últimos 8 dígitos
            ).first()
            
            if cliente:
                self.cliente = cliente
        
        except Exception as e:
            # Log erro silenciosamente
            pass
    
    @property
    def preview(self):
        """Preview da mensagem"""
        if self.tipo == 'texto':
            return self.conteudo[:100] + ('...' if len(self.conteudo) > 100 else '')
        elif self.tipo == 'imagem':
            return f"📷 Imagem: {self.legenda[:50] if self.legenda else 'Sem legenda'}"
        elif self.tipo == 'audio':
            return f"🎤 Áudio ({self.duracao_audio or '?'}s)"
        else:
            return f"{self.get_tipo_display()}"
    
    @property
    def tempo_resposta(self):
        """Calcula tempo de resposta se for resposta a uma mensagem"""
        if self.direcao == 'saida' and self.mensagem_respondida:
            return self.criado_em - self.mensagem_respondida.criado_em
        return None
    
    def marcar_como_lida(self):
        """Marca mensagem como lida"""
        self.lida = True
        self.tempo_leitura = timezone.now()
        self.save()
    
    def responder(self, conteudo, usuario=None, tipo='texto'):
        """Cria uma resposta para esta mensagem"""
        resposta = MensagemWhatsApp(
            whatsapp_config=self.whatsapp_config,
            cliente=self.cliente,
            processo=self.processo,
            numero_contato=self.numero_contato,
            nome_contato=self.nome_contato,
            tipo=tipo,
            direcao='saida',
            conteudo=conteudo,
            usuario_responsavel=usuario,
            mensagem_respondida=self,
        )
        resposta.save()
        return resposta


class FluxoChatbot(models.Model):
    """Fluxos conversacionais do chatbot"""
    
    TIPO_CHOICES = [
        ('saudacao', 'Saudação Inicial'),
        ('atendimento', 'Atendimento'),
        ('processos', 'Consulta de Processos'),
        ('financeiro', 'Financeiro'),
        ('agendamento', 'Agendamento'),
        ('duvidas', 'Dúvidas Frequentes'),
        ('outro', 'Outro'),
    ]
    
    escritorio = models.ForeignKey(Escritorio, on_delete=models.CASCADE, related_name='fluxos_chatbot')
    
    # Identificação
    nome = models.CharField('Nome do Fluxo', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='atendimento')
    
    # Ativação
    palavras_chave = models.TextField(
        'Palavras-chave', 
        help_text='Uma por linha. Use * para curinga (ex: olá*, *prazo*)'
    )
    expressoes_regulares = models.TextField(
        'Expressões Regulares', 
        blank=True,
        help_text='Regex para match mais preciso'
    )
    ativo = models.BooleanField('Ativo', default=True)
    ordem = models.IntegerField('Ordem de Execução', default=0, help_text='Menor executa primeiro')
    
    # Configuração do fluxo
    fluxo_json = models.JSONField(
        'Fluxo',
        default=dict,
        help_text='Estrutura do fluxo em JSON'
    )
    
    # Comportamento
    responder_automaticamente = models.BooleanField('Responder Automaticamente', default=True)
    transferir_humano = models.BooleanField('Transferir para Humano', default=False)
    usuario_transferencia = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fluxos_transferencia'
    )
    mensagem_transferencia = models.TextField('Mensagem de Transferência', blank=True)
    
    # Validações
    validar_cliente = models.BooleanField('Validar se é Cliente', default=False)
    solicitar_cpf = models.BooleanField('Solicitar CPF/CNPJ', default=False)
    solicitar_numero_processo = models.BooleanField('Solicitar Número do Processo', default=False)
    
    # Estatísticas
    vezes_executado = models.IntegerField('Vezes Executado', default=0)
    sucessos = models.IntegerField('Sucessos', default=0)
    falhas = models.IntegerField('Falhas', default=0)
    ultima_execucao = models.DateTimeField('Última Execução', null=True, blank=True)
    tempo_medio_resposta = models.FloatField('Tempo Médio de Resposta (ms)', default=0.0)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Fluxo de Chatbot'
        verbose_name_plural = 'Fluxos de Chatbot'
        ordering = ['ordem', 'nome']
        indexes = [
            models.Index(fields=['escritorio', 'ativo']),
            models.Index(fields=['tipo', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
    
    def verificar_ativacao(self, mensagem):
        """Verifica se a mensagem ativa este fluxo"""
        mensagem_lower = mensagem.lower()
        
        # Verifica palavras-chave
        palavras = [p.strip().lower() for p in self.palavras_chave.split('\n') if p.strip()]
        
        for palavra in palavras:
            # Suporte a curinga
            if palavra.endswith('*'):
                if mensagem_lower.startswith(palavra[:-1]):
                    return True
            elif palavra.startswith('*'):
                if mensagem_lower.endswith(palavra[1:]):
                    return True
            elif palavra in mensagem_lower:
                return True
        
        # Verifica regex se existir
        if self.expressoes_regulares:
            import re
            try:
                for regex in self.expressoes_regulares.split('\n'):
                    regex = regex.strip()
                    if regex and re.search(regex, mensagem, re.IGNORECASE):
                        return True
            except:
                pass
        
        return False
    
    def executar(self, contexto):
        """Executa o fluxo com o contexto fornecido"""
        try:
            # Incrementa estatísticas
            self.vezes_executado += 1
            self.ultima_execucao = timezone.now()
            
            # Processa fluxo
            fluxo = self.fluxo_json
            
            # Aqui você implementaria a lógica de execução do fluxo
            # Por enquanto, retorna a primeira mensagem do fluxo
            if fluxo.get('steps') and len(fluxo['steps']) > 0:
                self.sucessos += 1
                return fluxo['steps'][0].get('mensagem', 'Olá! Como posso ajudar?')
            
            self.falhas += 1
            return None
            
        except Exception as e:
            self.falhas += 1
            return f"Desculpe, ocorreu um erro: {str(e)}"
        
        finally:
            self.save()
    
    def get_passo_atual(self, session_id):
        """Obtém o passo atual para uma sessão"""
        from django.core.cache import cache
        
        chave = f"chatbot_{self.id}_{session_id}"
        dados = cache.get(chave, {'step': 0, 'data': {}})
        
        return dados['step']
    
    def avancar_passo(self, session_id, resposta_usuario=None):
        """Avança para o próximo passo"""
        from django.core.cache import cache
        
        chave = f"chatbot_{self.id}_{session_id}"
        dados = cache.get(chave, {'step': 0, 'data': {}})
        
        # Salva resposta do usuário no contexto se fornecida
        if resposta_usuario:
            dados['data'][f'resposta_{dados["step"]}'] = resposta_usuario
        
        # Avança passo
        dados['step'] += 1
        fluxo = self.fluxo_json
        
        # Verifica se chegou ao fim
        if dados['step'] >= len(fluxo.get('steps', [])):
            dados['fim'] = True
        
        cache.set(chave, dados, timeout=3600)  # 1 hora
        
        return dados['step']


class ConversaWhatsApp(models.Model):
    """Agrupamento de mensagens em conversas"""
    
    whatsapp_config = models.ForeignKey(WhatsAppConfig, on_delete=models.CASCADE, related_name='conversas')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversas')
    processo = models.ForeignKey(Processo, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversas')
    
    # Informações da conversa
    numero_contato = models.CharField('Número do Contato', max_length=20)
    nome_contato = models.CharField('Nome do Contato', max_length=100, blank=True)
    
    # Status
    aberta = models.BooleanField('Aberta', default=True)
    arquivada = models.BooleanField('Arquivada', default=False)
    resolvida = models.BooleanField('Resolvida', default=False)
    
    # Atribuição
    usuario_atribuido = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversas_atribuidas'
    )
    
    # Estatísticas
    total_mensagens = models.IntegerField('Total de Mensagens', default=0)
    mensagens_nao_lidas = models.IntegerField('Mensagens Não Lidas', default=0)
    primeira_mensagem = models.DateTimeField('Primeira Mensagem', null=True, blank=True)
    ultima_mensagem = models.DateTimeField('Última Mensagem', null=True, blank=True)
    
    # Tags
    tags = models.CharField('Tags', max_length=200, blank=True, help_text='Separadas por vírgula')
    
    # Auditoria
    criada_em = models.DateTimeField('Criada em', auto_now_add=True)
    atualizada_em = models.DateTimeField('Atualizada em', auto_now=True)
    
    class Meta:
        verbose_name = 'Conversa WhatsApp'
        verbose_name_plural = 'Conversas WhatsApp'
        ordering = ['-ultima_mensagem', '-aberta']
        unique_together = ['whatsapp_config', 'numero_contato']
        indexes = [
            models.Index(fields=['whatsapp_config', 'aberta', '-ultima_mensagem']),
            models.Index(fields=['cliente', '-ultima_mensagem']),
        ]
    
    def __str__(self):
        return f"Conversa com {self.nome_contato or self.numero_contato}"
    
    @property
    def ultimas_mensagens(self):
        """Obtém as últimas mensagens da conversa"""
        from . import MensagemWhatsApp
        return MensagemWhatsApp.objects.filter(
            whatsapp_config=self.whatsapp_config,
            numero_contato=self.numero_contato
        ).order_by('-criado_em')[:10]
    
    @property
    def precisa_atendimento(self):
        """Verifica se precisa de atendimento humano"""
        return (
            self.aberta and 
            not self.usuario_atribuido and 
            self.mensagens_nao_lidas > 0
        )
    
    def atualizar_estatisticas(self):
        """Atualiza estatísticas da conversa"""
        from . import MensagemWhatsApp
        
        mensagens = MensagemWhatsApp.objects.filter(
            whatsapp_config=self.whatsapp_config,
            numero_contato=self.numero_contato
        )
        
        if mensagens.exists():
            self.total_mensagens = mensagens.count()
            self.mensagens_nao_lidas = mensagens.filter(lida=False, direcao='entrada').count()
            self.primeira_mensagem = mensagens.earliest('criado_em').criado_em
            self.ultima_mensagem = mensagens.latest('criado_em').criado_em
            
            # Verifica se conversa deve ser fechada
            # (ex: última mensagem de saída há mais de 24 horas)
            from django.utils import timezone
            from datetime import timedelta
            
            ultima_mensagem_saida = mensagens.filter(
                direcao='saida'
            ).order_by('-criado_em').first()
            
            if ultima_mensagem_saida:
                horas_passadas = (timezone.now() - ultima_mensagem_saida.criado_em).total_seconds() / 3600
                if horas_passadas > 24 and self.mensagens_nao_lidas == 0:
                    self.aberta = False
            
            self.save()