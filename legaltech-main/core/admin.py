# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Escritorio, Usuario, Cliente, Anotacao, Entrevista,
    Processo, Andamento, Prazo, Audiencia,
    Financeiro, ContratoHonorarios, ParcelaHonorarios,
    WhatsAppConfig, MensagemWhatsApp, FluxoChatbot, ConversaWhatsApp
)


# ========== ESCRITÓRIO ==========
@admin.register(Escritorio)
class EscritorioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'email', 'ativo', 'total_usuarios', 'total_clientes']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'cnpj', 'razao_social']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'razao_social', 'cnpj')
        }),
        ('Contato', {
            'fields': ('telefone', 'email', 'endereco')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def total_usuarios(self, obj):
        count = obj.usuarios.count()
        return format_html('<strong>{}</strong>', count)
    total_usuarios.short_description = 'Usuários'
    
    def total_clientes(self, obj):
        count = obj.clientes.count()
        return format_html('<strong>{}</strong>', count)
    total_clientes.short_description = 'Clientes'


# ========== USUÁRIO ==========
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'get_full_name', 'email', 'tipo', 
        'escritorio', 'oab', 'status_badge', 'ultimo_login'
    ]
    list_filter = ['tipo', 'status', 'ativo', 'escritorio', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'oab']
    readonly_fields = ['ultimo_login', 'criado_em', 'atualizado_em', 'date_joined']
    
    fieldsets = (
        ('Credenciais', {
            'fields': ('username', 'password')
        }),
        ('Informações Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'telefone', 'celular', 'avatar')
        }),
        ('Informações Profissionais', {
            'fields': ('tipo', 'status', 'oab', 'escritorio')
        }),
        ('Permissões', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'pode_gerenciar_usuarios', 'pode_gerenciar_clientes',
                'pode_gerenciar_processos', 'pode_gerenciar_financeiro',
                'pode_gerenciar_whatsapp'
            )
        }),
        ('Grupos e Permissões', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('receber_notificacoes_email',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('date_joined', 'ultimo_login', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'ativo': 'success',
            'inativo': 'danger',
            'ferias': 'warning',
            'licenca': 'info'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ========== CLIENTE ==========
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'tipo_badge', 'cpf_cnpj', 'telefone', 
        'email', 'total_processos', 'ativo_badge'
    ]
    list_filter = ['tipo', 'ativo', 'escritorio', 'estado_civil', 'estado', 'cliente_preferencial']
    search_fields = ['nome', 'nome_social', 'cpf_cnpj', 'telefone', 'email']
    readonly_fields = [
        'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por', 
        'idade', 'total_processos', 'processos_ativos'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'nome', 'nome_social', 'apelido', 'escritorio')
        }),
        ('Documentos', {
            'fields': (
                'cpf_cnpj', 'rg', 'orgao_emissor', 'data_emissao_rg',
                'inscricao_estadual', 'inscricao_municipal'
            )
        }),
        ('Informações Pessoais', {
            'fields': (
                'data_nascimento', 'idade', 'estado_civil', 'nacionalidade',
                'naturalidade', 'profissao', 'empresa_trabalho', 'cargo', 'renda_mensal'
            ),
            'classes': ('collapse',)
        }),
        ('Contato', {
            'fields': ('telefone', 'celular', 'email', 'email_secundario')
        }),
        ('Endereço', {
            'fields': (
                'cep', 'endereco', 'numero', 'complemento',
                'bairro', 'cidade', 'estado'
            ),
            'classes': ('collapse',)
        }),
        ('Informações Bancárias', {
            'fields': ('banco', 'agencia', 'conta', 'tipo_conta', 'pix'),
            'classes': ('collapse',)
        }),
        ('Contato de Emergência', {
            'fields': (
                'contato_emergencia_nome', 'contato_emergencia_parentesco',
                'contato_emergencia_telefone'
            ),
            'classes': ('collapse',)
        }),
        ('Informações Adicionais', {
            'fields': (
                'como_conheceu', 'indicado_por', 'observacoes',
                'restricoes', 'foto'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('ativo', 'cliente_preferencial', 'receber_newsletter')
        }),
        ('Estatísticas', {
            'fields': ('total_processos', 'processos_ativos'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_badge(self, obj):
        colors = {'pf': 'primary', 'pj': 'info'}
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.tipo, 'secondary'),
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def ativo_badge(self, obj):
        color = 'success' if obj.ativo else 'danger'
        texto = 'Ativo' if obj.ativo else 'Inativo'
        return format_html('<span class="badge badge-{}">{}</span>', color, texto)
    ativo_badge.short_description = 'Status'


# ========== ANOTAÇÃO ==========
@admin.register(Anotacao)
class AnotacaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'cliente', 'categoria', 'importante', 'privada', 'usuario', 'criado_em']
    list_filter = ['categoria', 'importante', 'privada', 'criado_em']
    search_fields = ['titulo', 'conteudo', 'cliente__nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'resumo']
    date_hierarchy = 'criado_em'


# ========== ENTREVISTA ==========
@admin.register(Entrevista)
class EntrevistaAdmin(admin.ModelAdmin):
    list_display = [
        'cliente', 'assunto', 'tipo', 'status_badge', 
        'data', 'hora_inicio', 'usuario', 'cliente_compareceu'
    ]
    list_filter = ['tipo', 'status', 'data', 'cliente_compareceu']
    search_fields = ['cliente__nome', 'assunto']
    readonly_fields = ['criado_em', 'atualizado_em', 'duracao']
    date_hierarchy = 'data'
    
    def status_badge(self, obj):
        colors = {
            'agendada': 'info',
            'confirmada': 'primary',
            'realizada': 'success',
            'cancelada': 'danger',
            'adiada': 'warning'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ========== PROCESSO ==========
@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_cnj', 'cliente', 'tipo', 'situacao_badge',
        'advogado_responsavel', 'data_distribuicao', 'valor_causa'
    ]
    list_filter = ['tipo', 'situacao', 'tribunal', 'data_distribuicao', 'escritorio']
    search_fields = ['numero_cnj', 'cliente__nome', 'vara', 'comarca']
    readonly_fields = [
        'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por',
        'dias_ate_proxima_audiencia', 'total_custas'
    ]
    date_hierarchy = 'data_distribuicao'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'numero_cnj', 'escritorio', 'cliente',
                'advogado_responsavel', 'tipo', 'situacao'
            )
        }),
        ('Informações Judiciais', {
            'fields': (
                'vara', 'comarca', 'tribunal', 'valor_causa',
                'data_distribuicao', 'data_arquivamento', 'data_encerramento'
            )
        }),
        ('Partes', {
            'fields': ('polo_ativo', 'polo_passivo', 'testemunhas'),
            'classes': ('collapse',)
        }),
        ('Detalhes', {
            'fields': ('objeto', 'honorarios', 'observacoes', 'tags')
        }),
        ('Estatísticas', {
            'fields': ('dias_ate_proxima_audiencia', 'total_custas'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def situacao_badge(self, obj):
        colors = {
            'ativo': 'success',
            'arquivado': 'secondary',
            'suspenso': 'warning',
            'baixado': 'info',
            'encerrado': 'dark',
            'transitado': 'primary'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.situacao, 'secondary'),
            obj.get_situacao_display()
        )
    situacao_badge.short_description = 'Situação'


# ========== ANDAMENTO ==========
@admin.register(Andamento)
class AndamentoAdmin(admin.ModelAdmin):
    list_display = ['processo', 'tipo', 'data', 'importante', 'usuario', 'criado_em']
    list_filter = ['tipo', 'importante', 'capturado_automatico', 'data']
    search_fields = ['processo__numero_cnj', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em', 'resumo']
    date_hierarchy = 'data'


# ========== PRAZO ==========
@admin.register(Prazo)
class PrazoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'processo', 'tipo', 'prioridade_badge',
        'status_badge', 'data_limite', 'responsavel', 'dias_restantes_display'
    ]
    list_filter = ['tipo', 'prioridade', 'status', 'data_limite']
    search_fields = ['titulo', 'processo__numero_cnj', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em', 'dias_restantes', 'esta_vencido', 'precisa_alerta']
    date_hierarchy = 'data_limite'
    
    def prioridade_badge(self, obj):
        colors = {
            'baixa': 'secondary',
            'media': 'info',
            'alta': 'warning',
            'urgente': 'danger'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.prioridade, 'secondary'),
            obj.get_prioridade_display()
        )
    prioridade_badge.short_description = 'Prioridade'
    
    def status_badge(self, obj):
        colors = {
            'pendente': 'warning',
            'em_andamento': 'info',
            'concluido': 'success',
            'vencido': 'danger',
            'cancelado': 'secondary'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        if dias is None:
            return '-'
        if dias < 0:
            return format_html('<span class="badge badge-danger">Vencido há {} dias</span>', abs(dias))
        if dias == 0:
            return format_html('<span class="badge badge-danger">Vence hoje!</span>')
        if dias <= 3:
            return format_html('<span class="badge badge-warning">{} dias</span>', dias)
        return format_html('<span class="badge badge-info">{} dias</span>', dias)
    dias_restantes_display.short_description = 'Dias Restantes'


# ========== AUDIÊNCIA ==========
@admin.register(Audiencia)
class AudienciaAdmin(admin.ModelAdmin):
    list_display = ['processo', 'tipo', 'status', 'data', 'hora', 'local']
    list_filter = ['tipo', 'status', 'data']
    search_fields = ['processo__numero_cnj', 'local', 'juiz']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data'


# ========== FINANCEIRO ==========
@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    list_display = [
        'descricao', 'tipo_badge', 'categoria', 'valor',
        'data_vencimento', 'status_badge', 'cliente', 'processo'
    ]
    list_filter = ['tipo', 'status', 'categoria', 'data_vencimento', 'escritorio']
    search_fields = ['descricao', 'cliente__nome', 'processo__numero_cnj']
    readonly_fields = [
        'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por',
        'valor_pendente', 'percentual_pago', 'esta_vencido', 'precisa_lembrete'
    ]
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('escritorio', 'tipo', 'categoria', 'descricao')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'processo')
        }),
        ('Valores', {
            'fields': ('valor', 'valor_pago', 'valor_pendente', 'percentual_pago')
        }),
        ('Datas', {
            'fields': ('data_vencimento', 'data_pagamento', 'data_competencia')
        }),
        ('Pagamento', {
            'fields': ('status', 'forma_pagamento', 'banco', 'agencia', 'conta', 'pix')
        }),
        ('Parcelamento', {
            'fields': ('periodicidade', 'parcela_atual', 'total_parcelas'),
            'classes': ('collapse',)
        }),
        ('Documentos', {
            'fields': ('comprovante', 'nota_fiscal', 'contrato'),
            'classes': ('collapse',)
        }),
        ('Lembretes', {
            'fields': ('enviar_lembrete', 'dias_lembrete', 'observacoes'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('esta_vencido', 'precisa_lembrete')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_badge(self, obj):
        colors = {'receita': 'success', 'despesa': 'danger', 'transferencia': 'info'}
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.tipo, 'secondary'),
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def status_badge(self, obj):
        colors = {
            'pendente': 'warning',
            'pago': 'success',
            'vencido': 'danger',
            'cancelado': 'secondary',
            'parcial': 'info'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ========== CONTRATO DE HONORÁRIOS ==========
@admin.register(ContratoHonorarios)
class ContratoHonorariosAdmin(admin.ModelAdmin):
    list_display = [
        'processo', 'cliente', 'tipo', 'valor_total',
        'numero_parcelas', 'assinado', 'ativo'
    ]
    list_filter = ['tipo', 'forma_pagamento', 'assinado', 'ativo']
    search_fields = ['processo__numero_cnj', 'cliente__nome']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'valor_parcela']


@admin.register(ParcelaHonorarios)
class ParcelaHonorariosAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'numero', 'valor', 'data_vencimento', 'status']
    list_filter = ['status', 'data_vencimento']
    search_fields = ['contrato__processo__numero_cnj']
    readonly_fields = ['criado_em', 'atualizado_em']


# ========== WHATSAPP ==========
@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'numero_telefone', 'provider', 'status_badge',
        'ativo', 'mensagens_enviadas', 'mensagens_recebidas'
    ]
    list_filter = ['provider', 'status', 'ativo']
    search_fields = ['nome', 'numero_telefone']
    readonly_fields = [
        'criado_em', 'criado_por', 'atualizado_em',
        'esta_conectado', 'em_horario_funcionamento',
        'mensagens_enviadas', 'mensagens_recebidas'
    ]
    
    def status_badge(self, obj):
        colors = {
            'desconectado': 'secondary',
            'conectando': 'info',
            'conectado': 'success',
            'qr_code': 'warning',
            'erro': 'danger',
            'desconhecido': 'dark'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(MensagemWhatsApp)
class MensagemWhatsAppAdmin(admin.ModelAdmin):
    list_display = [
        'preview', 'numero_contato', 'tipo', 'direcao_badge',
        'status', 'lida', 'criado_em'
    ]
    list_filter = ['tipo', 'direcao', 'status', 'lida', 'criado_em']
    search_fields = ['numero_contato', 'nome_contato', 'conteudo']
    readonly_fields = ['criado_em', 'atualizado_em', 'tempo_resposta']
    date_hierarchy = 'criado_em'
    
    def direcao_badge(self, obj):
        colors = {'entrada': 'info', 'saida': 'success'}
        icons = {'entrada': '↓', 'saida': '↑'}
        return format_html(
            '<span class="badge badge-{}">{} {}</span>',
            colors.get(obj.direcao, 'secondary'),
            icons.get(obj.direcao, '•'),
            obj.get_direcao_display()
        )
    direcao_badge.short_description = 'Direção'


@admin.register(FluxoChatbot)
class FluxoChatbotAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'ordem', 'vezes_executado', 'sucessos', 'falhas']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'vezes_executado', 'sucessos', 'falhas']


@admin.register(ConversaWhatsApp)
class ConversaWhatsAppAdmin(admin.ModelAdmin):
    list_display = [
        'numero_contato', 'nome_contato', 'cliente',
        'aberta', 'mensagens_nao_lidas', 'ultima_mensagem'
    ]
    list_filter = ['aberta', 'arquivada', 'resolvida']
    search_fields = ['numero_contato', 'nome_contato', 'cliente__nome']
    readonly_fields = ['criada_em', 'atualizada_em', 'precisa_atendimento']