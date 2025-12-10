# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import (
    Escritorio, Usuario, Cliente, Anotacao, Entrevista,
    Processo, Andamento, Prazo, Audiencia,
    Financeiro, ContratoHonorarios, ParcelaHonorarios,
    WhatsAppConfig, MensagemWhatsApp, FluxoChatbot, ConversaWhatsApp
)


# ========== ESCRITÓRIO ==========
class EscritorioSerializer(serializers.ModelSerializer):
    total_usuarios = serializers.SerializerMethodField()
    total_clientes = serializers.SerializerMethodField()
    total_processos = serializers.SerializerMethodField()
    
    class Meta:
        model = Escritorio
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em']
    
    def get_total_usuarios(self, obj):
        return obj.usuarios.count()
    
    def get_total_clientes(self, obj):
        return obj.clientes.count()
    
    def get_total_processos(self, obj):
        return obj.processos.count()


# ========== USUÁRIO ==========
class UsuarioSerializer(serializers.ModelSerializer):
    escritorio_nome = serializers.CharField(source='escritorio.nome', read_only=True)
    nome_completo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'tipo', 'status', 'oab', 'telefone', 'celular',
            'escritorio', 'escritorio_nome', 'avatar',
            'pode_gerenciar_usuarios', 'pode_gerenciar_clientes',
            'pode_gerenciar_processos', 'pode_gerenciar_financeiro',
            'pode_gerenciar_whatsapp', 'ativo', 'nome_completo',
            'ultimo_login', 'criado_em'
        ]
        read_only_fields = ['criado_em', 'ultimo_login', 'nome_completo']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UsuarioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'tipo', 'oab']


# ========== CLIENTE ==========
class ClienteSerializer(serializers.ModelSerializer):
    escritorio_nome = serializers.CharField(source='escritorio.nome', read_only=True)
    idade = serializers.IntegerField(read_only=True)
    total_processos = serializers.IntegerField(read_only=True)
    processos_ativos = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por',
            'idade', 'total_processos', 'processos_ativos'
        ]


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'tipo', 'cpf_cnpj', 'telefone', 
            'email', 'cidade', 'estado', 'ativo'
        ]


# ========== ANOTAÇÃO ==========
class AnotacaoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    resumo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Anotacao
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em', 'resumo']


# ========== ENTREVISTA ==========
class EntrevistaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    duracao = serializers.IntegerField(read_only=True)
    esta_agora = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Entrevista
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em', 'duracao', 'esta_agora']


# ========== PROCESSO ==========
class ProcessoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    advogado_nome = serializers.CharField(source='advogado_responsavel.get_full_name', read_only=True)
    dias_ate_proxima_audiencia = serializers.IntegerField(read_only=True)
    total_custas = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Processo
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por',
            'dias_ate_proxima_audiencia', 'total_custas'
        ]


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    
    class Meta:
        model = Processo
        fields = [
            'id', 'numero_cnj', 'cliente_nome', 'tipo',
            'situacao', 'valor_causa', 'data_distribuicao'
        ]


# ========== ANDAMENTO ==========
class AndamentoSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    resumo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Andamento
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em', 'resumo']


# ========== PRAZO ==========
class PrazoSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    precisa_alerta = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Prazo
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'atualizado_em', 'dias_restantes',
            'esta_vencido', 'precisa_alerta'
        ]


# ========== AUDIÊNCIA ==========
class AudienciaSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    
    class Meta:
        model = Audiencia
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em']


# ========== FINANCEIRO ==========
class FinanceiroSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    valor_pendente = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    percentual_pago = serializers.FloatField(read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Financeiro
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por',
            'valor_pendente', 'percentual_pago', 'esta_vencido'
        ]


class FinanceiroListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    
    class Meta:
        model = Financeiro
        fields = [
            'id', 'tipo', 'categoria', 'descricao', 'valor',
            'data_vencimento', 'status', 'cliente_nome'
        ]


# ========== CONTRATO HONORÁRIOS ==========
class ParcelaHonorariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelaHonorarios
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em']


class ContratoHonorariosSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    valor_parcela = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    parcelas = ParcelaHonorariosSerializer(many=True, read_only=True)
    
    class Meta:
        model = ContratoHonorarios
        fields = '__all__'
        read_only_fields = ['criado_em', 'criado_por', 'atualizado_em', 'valor_parcela']


# ========== WHATSAPP ==========
class WhatsAppConfigSerializer(serializers.ModelSerializer):
    escritorio_nome = serializers.CharField(source='escritorio.nome', read_only=True)
    esta_conectado = serializers.BooleanField(read_only=True)
    em_horario_funcionamento = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WhatsAppConfig
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'criado_por', 'atualizado_em',
            'esta_conectado', 'em_horario_funcionamento',
            'mensagens_enviadas', 'mensagens_recebidas'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},
            'webhook_secret': {'write_only': True}
        }


class MensagemWhatsAppSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    preview = serializers.CharField(read_only=True)
    tempo_resposta = serializers.DurationField(read_only=True)
    
    class Meta:
        model = MensagemWhatsApp
        fields = '__all__'
        read_only_fields = ['criado_em', 'atualizado_em', 'preview', 'tempo_resposta']


class FluxoChatbotSerializer(serializers.ModelSerializer):
    escritorio_nome = serializers.CharField(source='escritorio.nome', read_only=True)
    
    class Meta:
        model = FluxoChatbot
        fields = '__all__'
        read_only_fields = [
            'criado_em', 'criado_por', 'atualizado_em',
            'vezes_executado', 'sucessos', 'falhas', 'ultima_execucao'
        ]


class ConversaWhatsAppSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero_cnj', read_only=True)
    precisa_atendimento = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ConversaWhatsApp
        fields = '__all__'
        read_only_fields = [
            'criada_em', 'atualizada_em', 'total_mensagens',
            'mensagens_nao_lidas', 'primeira_mensagem',
            'ultima_mensagem', 'precisa_atendimento'
        ]