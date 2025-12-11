# -*- coding: utf-8 -*-
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import (
    Cliente, Processo, Prazo, Audiencia, Financeiro,
    MensagemWhatsApp, ConversaWhatsApp
)


class ClienteFilter(filters.FilterSet):
    """Filtros avançados para Cliente"""
    
    nome = filters.CharFilter(lookup_expr='icontains')
    cpf_cnpj = filters.CharFilter(lookup_expr='icontains')
    cidade = filters.CharFilter(lookup_expr='icontains')
    # Filtro por data de cadastro
    criado_antes = filters.DateFilter(field_name='criado_em', lookup_expr='lte')
    criado_depois = filters.DateFilter(field_name='criado_em', lookup_expr='gte')
    # Filtro por idade
    idade_min = filters.NumberFilter(method='filter_idade_min')
    idade_max = filters.NumberFilter(method='filter_idade_max')
    
    class Meta:
        model = Cliente
        fields = ['tipo', 'ativo', 'estado', 'cliente_preferencial']
    
    def filter_idade_min(self, queryset, name, value):
        # Calcula data de nascimento máxima para idade mínima
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        data_max = date.today() - relativedelta(years=value)
        return queryset.filter(data_nascimento__lte=data_max)
    
    def filter_idade_max(self, queryset, name, value):
        # Calcula data de nascimento mínima para idade máxima
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        data_min = date.today() - relativedelta(years=value + 1)
        return queryset.filter(data_nascimento__gte=data_min)


class ProcessoFilter(filters.FilterSet):
    """Filtros avançados para Processo"""
    
    numero_cnj = filters.CharFilter(lookup_expr='icontains')
    cliente_nome = filters.CharFilter(field_name='cliente__nome', lookup_expr='icontains')
    comarca = filters.CharFilter(lookup_expr='icontains')
    
    # Filtros de data
    distribuido_antes = filters.DateFilter(field_name='data_distribuicao', lookup_expr='lte')
    distribuido_depois = filters.DateFilter(field_name='data_distribuicao', lookup_expr='gte')
    
    # Filtro por valor da causa
    valor_causa_min = filters.NumberFilter(field_name='valor_causa', lookup_expr='gte')
    valor_causa_max = filters.NumberFilter(field_name='valor_causa', lookup_expr='lte')
    
    # Busca em múltiplos campos
    busca = filters.CharFilter(method='filter_busca_geral')
    
    class Meta:
        model = Processo
        fields = ['tipo', 'situacao', 'cliente', 'advogado_responsavel', 'tribunal']
    
    def filter_busca_geral(self, queryset, name, value):
        """Busca em número CNJ, cliente, objeto"""
        return queryset.filter(
            Q(numero_cnj__icontains=value) |
            Q(cliente__nome__icontains=value) |
            Q(objeto__icontains=value) |
            Q(polo_ativo__icontains=value) |
            Q(polo_passivo__icontains=value)
        )


class PrazoFilter(filters.FilterSet):
    """Filtros avançados para Prazo"""
    
    titulo = filters.CharFilter(lookup_expr='icontains')
    processo_numero = filters.CharFilter(field_name='processo__numero_cnj', lookup_expr='icontains')
    
    # Filtros de data
    vence_antes = filters.DateFilter(field_name='data_limite', lookup_expr='lte')
    vence_depois = filters.DateFilter(field_name='data_limite', lookup_expr='gte')
    vence_hoje = filters.BooleanFilter(method='filter_vence_hoje')
    vencidos = filters.BooleanFilter(method='filter_vencidos')
    
    class Meta:
        model = Prazo
        fields = ['processo', 'tipo', 'prioridade', 'status', 'responsavel']
    
    def filter_vence_hoje(self, queryset, name, value):
        if value:
            from django.utils import timezone
            hoje = timezone.now().date()
            return queryset.filter(data_limite=hoje, status='pendente')
        return queryset
    
    def filter_vencidos(self, queryset, name, value):
        if value:
            from django.utils import timezone
            hoje = timezone.now().date()
            return queryset.filter(data_limite__lt=hoje, status='pendente')
        return queryset


class AudienciaFilter(filters.FilterSet):
    """Filtros avançados para Audiência"""
    
    processo_numero = filters.CharFilter(field_name='processo__numero_cnj', lookup_expr='icontains')
    local = filters.CharFilter(lookup_expr='icontains')
    
    # Filtros de data
    data_inicio = filters.DateFilter(field_name='data', lookup_expr='gte')
    data_fim = filters.DateFilter(field_name='data', lookup_expr='lte')
    proximas = filters.BooleanFilter(method='filter_proximas')
    
    class Meta:
        model = Audiencia
        fields = ['processo', 'tipo', 'status', 'data']
    
    def filter_proximas(self, queryset, name, value):
        if value:
            from django.utils import timezone
            hoje = timezone.now().date()
            return queryset.filter(
                data__gte=hoje,
                status__in=['agendada', 'confirmada']
            ).order_by('data', 'hora')
        return queryset


class FinanceiroFilter(filters.FilterSet):
    """Filtros avançados para Financeiro"""
    
    descricao = filters.CharFilter(lookup_expr='icontains')
    cliente_nome = filters.CharFilter(field_name='cliente__nome', lookup_expr='icontains')
    
    # Filtros de valor
    valor_min = filters.NumberFilter(field_name='valor', lookup_expr='gte')
    valor_max = filters.NumberFilter(field_name='valor', lookup_expr='lte')
    
    # Filtros de data
    vencimento_inicio = filters.DateFilter(field_name='data_vencimento', lookup_expr='gte')
    vencimento_fim = filters.DateFilter(field_name='data_vencimento', lookup_expr='lte')
    mes_vencimento = filters.NumberFilter(field_name='data_vencimento__month')
    ano_vencimento = filters.NumberFilter(field_name='data_vencimento__year')
    
    # Filtros especiais
    vencidos = filters.BooleanFilter(method='filter_vencidos')
    a_vencer = filters.BooleanFilter(method='filter_a_vencer')
    
    class Meta:
        model = Financeiro
        fields = ['tipo', 'categoria', 'status', 'cliente', 'processo', 'forma_pagamento']
    
    def filter_vencidos(self, queryset, name, value):
        if value:
            from django.utils import timezone
            hoje = timezone.now().date()
            return queryset.filter(
                data_vencimento__lt=hoje,
                status__in=['pendente', 'parcial']
            )
        return queryset
    
    def filter_a_vencer(self, queryset, name, value):
        if value:
            from django.utils import timezone
            from datetime import timedelta
            
            hoje = timezone.now().date()
            dias = 7  # Próximos 7 dias
            limite = hoje + timedelta(days=dias)
            
            return queryset.filter(
                data_vencimento__range=[hoje, limite],
                status='pendente'
            )
        return queryset


class MensagemWhatsAppFilter(filters.FilterSet):
    """Filtros avançados para Mensagem WhatsApp"""
    
    conteudo = filters.CharFilter(lookup_expr='icontains')
    numero_contato = filters.CharFilter(lookup_expr='icontains')
    nome_contato = filters.CharFilter(lookup_expr='icontains')
    
    # Filtros de data
    data_inicio = filters.DateTimeFilter(field_name='criado_em', lookup_expr='gte')
    data_fim = filters.DateTimeFilter(field_name='criado_em', lookup_expr='lte')
    
    # Filtros especiais
    nao_lidas = filters.BooleanFilter(method='filter_nao_lidas')
    
    class Meta:
        model = MensagemWhatsApp
        fields = ['tipo', 'direcao', 'status', 'lida', 'cliente', 'whatsapp_config']
    
    def filter_nao_lidas(self, queryset, name, value):
        if value:
            return queryset.filter(lida=False, direcao='entrada')
        return queryset


class ConversaWhatsAppFilter(filters.FilterSet):
    """Filtros avançados para Conversa WhatsApp"""
    
    numero_contato = filters.CharFilter(lookup_expr='icontains')
    nome_contato = filters.CharFilter(lookup_expr='icontains')
    
    # Filtros especiais
    pendentes_atendimento = filters.BooleanFilter(method='filter_pendentes')
    
    class Meta:
        model = ConversaWhatsApp
        fields = ['aberta', 'arquivada', 'resolvida', 'cliente', 'usuario_atribuido']
    
    def filter_pendentes(self, queryset, name, value):
        if value:
            return queryset.filter(
                aberta=True,
                mensagens_nao_lidas__gt=0
            )
        return queryset