from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid

class Escritorio(models.Model):
    """Escritório de advocacia"""
    
    nome = models.CharField(_('Nome do Escritório'), max_length=200)
    razao_social = models.CharField(_('Razão Social'), max_length=200)
    
    # Documentos
    cnpj = models.CharField(
        _('CNPJ'),
        max_length=18,
        unique=True,
        blank=True,
        null=True
    )
    
    # Contato
    telefone = models.CharField(_('Telefone'), max_length=20, blank=True)
    email = models.EmailField(_('E-mail Principal'), blank=True)
    
    # Endereço
    endereco = models.TextField(_('Endereço'), blank=True)
    
    # Status
    ativo = models.BooleanField(_('Ativo'), default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Escritório')
        verbose_name_plural = _('Escritórios')
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    """Usuário customizado do sistema"""
    
    TIPO_CHOICES = [
        ('admin', _('Administrador')),
        ('socio', _('Sócio')),
        ('advogado', _('Advogado')),
        ('estagiario', _('Estagiário')),
        ('secretaria', _('Secretária')),
        ('financeiro', _('Financeiro')),
        ('outro', _('Outro')),
    ]
    
    STATUS_CHOICES = [
        ('ativo', _('Ativo')),
        ('inativo', _('Inativo')),
        ('ferias', _('Férias')),
        ('licenca', _('Licença')),
    ]
    
    # Informações básicas
    tipo = models.CharField(_('Tipo de Usuário'), max_length=20, choices=TIPO_CHOICES, default='advogado')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    # Documentos profissionais
    oab = models.CharField(_('Número da OAB'), max_length=20, blank=True, null=True)
    
    # Contato
    telefone = models.CharField(_('Telefone'), max_length=20, blank=True)
    celular = models.CharField(_('Celular'), max_length=20, blank=True)
    
    # Relacionamento com escritório
    escritorio = models.ForeignKey(
        Escritorio,
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name=_('Escritório'),
        null=True,
        blank=True
    )
    
    # Mídia
    avatar = models.ImageField(_('Avatar'), upload_to='usuarios/avatars/', null=True, blank=True)
    
    # Configurações do usuário
    receber_notificacoes_email = models.BooleanField(_('Receber Notificações por E-mail'), default=True)
    
    # Permissões específicas
    pode_gerenciar_usuarios = models.BooleanField(_('Pode Gerenciar Usuários'), default=False)
    pode_gerenciar_clientes = models.BooleanField(_('Pode Gerenciar Clientes'), default=True)
    pode_gerenciar_processos = models.BooleanField(_('Pode Gerenciar Processos'), default=True)
    pode_gerenciar_financeiro = models.BooleanField(_('Pode Gerenciar Financeiro'), default=False)
    pode_gerenciar_whatsapp = models.BooleanField(_('Pode Gerenciar WhatsApp'), default=False)
    
    # Status
    ativo = models.BooleanField(_('Ativo'), default=True)
    
    # Informações de login
    ultimo_login = models.DateTimeField(_('Último Login'), null=True, blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    # IMPORTANTE: Configurar related_name para evitar conflitos
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('Grupos'),
        blank=True,
        help_text=_('Grupos aos quais este usuário pertence'),
        related_name='usuario_set',  # Nome único para evitar conflito
        related_query_name='usuario'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('Permissões de usuário'),
        blank=True,
        help_text=_('Permissões específicas para este usuário'),
        related_name='usuario_set',  # Nome único para evitar conflito
        related_query_name='usuario'
    )
    
    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        nome_completo = self.get_full_name()
        if nome_completo:
            return f"{nome_completo} ({self.get_tipo_display()})"
        return f"{self.username} ({self.get_tipo_display()})"
    
    def save(self, *args, **kwargs):
        # Define permissões baseadas no tipo
        self._definir_permissoes_por_tipo()
        
        # Se for superusuário, tem todas as permissões
        if self.is_superuser:
            self.acesso_total = True
            self.pode_gerenciar_usuarios = True
            self.pode_gerenciar_clientes = True
            self.pode_gerenciar_processos = True
            self.pode_gerenciar_financeiro = True
            self.pode_gerenciar_whatsapp = True
        
        super().save(*args, **kwargs)
    
    def _definir_permissoes_por_tipo(self):
        """Define permissões baseadas no tipo de usuário"""
        if self.tipo == 'admin':
            self.pode_gerenciar_usuarios = True
            self.pode_gerenciar_clientes = True
            self.pode_gerenciar_processos = True
            self.pode_gerenciar_financeiro = True
            self.pode_gerenciar_whatsapp = True
        elif self.tipo == 'socio':
            self.pode_gerenciar_usuarios = True
            self.pode_gerenciar_clientes = True
            self.pode_gerenciar_processos = True
            self.pode_gerenciar_financeiro = True
            self.pode_gerenciar_whatsapp = True
        elif self.tipo == 'advogado':
            self.pode_gerenciar_clientes = True
            self.pode_gerenciar_processos = True
            self.pode_gerenciar_whatsapp = True
        elif self.tipo == 'financeiro':
            self.pode_gerenciar_financeiro = True
        elif self.tipo == 'secretaria':
            self.pode_gerenciar_clientes = True
            self.pode_gerenciar_processos = True
            self.pode_gerenciar_whatsapp = True
    
    @property
    def nome_completo(self):
        return self.get_full_name()
    
    @property
    def esta_ativo(self):
        return self.ativo and self.status == 'ativo'