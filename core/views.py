# -*- coding: utf-8 -*-
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import (
    Escritorio, Usuario, Cliente, Anotacao, Entrevista,
    Processo, Andamento, Prazo, Audiencia,
    Financeiro, ContratoHonorarios, ParcelaHonorarios,
    WhatsAppConfig, MensagemWhatsApp, FluxoChatbot, ConversaWhatsApp
)
from .serializers import (
    EscritorioSerializer, UsuarioSerializer, UsuarioListSerializer,
    ClienteSerializer, ClienteListSerializer, AnotacaoSerializer,
    EntrevistaSerializer, ProcessoSerializer, ProcessoListSerializer,
    AndamentoSerializer, PrazoSerializer, AudienciaSerializer,
    FinanceiroSerializer, FinanceiroListSerializer,
    ContratoHonorariosSerializer, ParcelaHonorariosSerializer,
    WhatsAppConfigSerializer, MensagemWhatsAppSerializer,
    FluxoChatbotSerializer, ConversaWhatsAppSerializer
)
from .permissions import IsEscritorioMember, CanManageUsuarios, CanManageFinanceiro


# ========== ESCRITÓRIO ==========
class EscritorioViewSet(viewsets.ModelViewSet):
    queryset = Escritorio.objects.all()
    serializer_class = EscritorioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'razao_social', 'cnpj']
    ordering_fields = ['nome', 'criado_em']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Escritorio.objects.all()
        return Escritorio.objects.filter(id=user.escritorio_id)
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Retorna estatísticas do escritório"""
        escritorio = self.get_object()
        
        stats = {
            'total_usuarios': escritorio.usuarios.count(),
            'total_clientes': escritorio.clientes.count(),
            'total_processos': escritorio.processos.count(),
            'processos_ativos': escritorio.processos.filter(situacao='ativo').count(),
            'processos_por_tipo': escritorio.processos.values('tipo').annotate(total=Count('id')),
            'receitas_mes': escritorio.financeiro.filter(
                tipo='receita',
                data_vencimento__month=timezone.now().month
            ).aggregate(total=Sum('valor'))['total'] or 0,
            'despesas_mes': escritorio.financeiro.filter(
                tipo='despesa',
                data_vencimento__month=timezone.now().month
            ).aggregate(total=Sum('valor'))['total'] or 0,
        }
        
        return Response(stats)


# ========== USUÁRIO ==========
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated, CanManageUsuarios]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'status', 'ativo', 'escritorio']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'oab']
    ordering_fields = ['username', 'first_name', 'criado_em']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UsuarioListSerializer
        return UsuarioSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Usuario.objects.all()
        return Usuario.objects.filter(escritorio=user.escritorio)
    
    @action(detail=True, methods=['post'])
    def alterar_senha(self, request, pk=None):
        """Permite usuário alterar sua própria senha"""
        usuario = self.get_object()
        
        if usuario != request.user and not request.user.is_superuser:
            return Response(
                {'erro': 'Você só pode alterar sua própria senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        nova_senha = request.data.get('nova_senha')
        if not nova_senha:
            return Response(
                {'erro': 'Nova senha não fornecida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario.set_password(nova_senha)
        usuario.save()
        
        return Response({'sucesso': 'Senha alterada com sucesso'})


# ========== CLIENTE ==========
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'ativo', 'estado', 'cliente_preferencial']
    search_fields = ['nome', 'nome_social', 'cpf_cnpj', 'telefone', 'email']
    ordering_fields = ['nome', 'criado_em']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer
    
    def get_queryset(self):
        return Cliente.objects.filter(escritorio=self.request.user.escritorio)
    
    def perform_create(self, serializer):
        serializer.save(
            escritorio=self.request.user.escritorio,
            criado_por=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def processos(self, request, pk=None):
        """Retorna todos os processos do cliente"""
        cliente = self.get_object()
        processos = cliente.processos.all()
        serializer = ProcessoListSerializer(processos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def financeiro(self, request, pk=None):
        """Retorna histórico financeiro do cliente"""
        cliente = self.get_object()
        financeiro = cliente.financeiro.all()
        serializer = FinanceiroListSerializer(financeiro, many=True)
        return Response(serializer.data)

# ========== ENTREVISTA ==========
class EntrevistaViewSet(viewsets.ModelViewSet):
    queryset = Entrevista.objects.all()
    serializer_class = EntrevistaSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'tipo', 'status', 'data']
    search_fields = ['assunto', 'cliente__nome']
    ordering_fields = ['data', 'hora_inicio']
    
    def get_queryset(self):
        return Entrevista.objects.filter(cliente__escritorio=self.request.user.escritorio)
    
    @action(detail=False, methods=['get'])
    def agenda_hoje(self, request):
        """Retorna entrevistas agendadas para hoje"""
        hoje = timezone.now().date()
        entrevistas = self.get_queryset().filter(
            data=hoje,
            status__in=['agendada', 'confirmada']
        )
        serializer = self.get_serializer(entrevistas, many=True)
        return Response(serializer.data)


# ========== PROCESSO ==========
class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.all()
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'situacao', 'cliente', 'advogado_responsavel']
    search_fields = ['numero_cnj', 'cliente__nome', 'objeto']
    ordering_fields = ['data_distribuicao', 'criado_em']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        return ProcessoSerializer
    
    def get_queryset(self):
        return Processo.objects.filter(escritorio=self.request.user.escritorio)
    
    def perform_create(self, serializer):
        serializer.save(
            escritorio=self.request.user.escritorio,
            criado_por=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def andamentos(self, request, pk=None):
        """Retorna andamentos do processo"""
        processo = self.get_object()
        andamentos = processo.andamentos.all()
        serializer = AndamentoSerializer(andamentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def prazos(self, request, pk=None):
        """Retorna prazos do processo"""
        processo = self.get_object()
        prazos = processo.prazos.filter(status='pendente')
        serializer = PrazoSerializer(prazos, many=True)
        return Response(serializer.data)


# ========== ANDAMENTO ==========
class AndamentoViewSet(viewsets.ModelViewSet):
    queryset = Andamento.objects.all()
    serializer_class = AndamentoSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['processo', 'tipo', 'importante', 'data']
    search_fields = ['descricao', 'processo__numero_cnj']
    ordering_fields = ['data', 'criado_em']
    
    def get_queryset(self):
        return Andamento.objects.filter(processo__escritorio=self.request.user.escritorio)


# ========== PRAZO ==========
class PrazoViewSet(viewsets.ModelViewSet):
    queryset = Prazo.objects.all()
    serializer_class = PrazoSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['processo', 'tipo', 'prioridade', 'status', 'responsavel']
    search_fields = ['titulo', 'descricao', 'processo__numero_cnj']
    ordering_fields = ['data_limite', 'prioridade']
    
    def get_queryset(self):
        return Prazo.objects.filter(processo__escritorio=self.request.user.escritorio)
    
    @action(detail=False, methods=['get'])
    def vencendo(self, request):
        """Retorna prazos vencendo nos próximos dias"""
        dias = int(request.query_params.get('dias', 7))
        hoje = timezone.now().date()
        limite = hoje + timezone.timedelta(days=dias)
        
        prazos = self.get_queryset().filter(
            status='pendente',
            data_limite__range=[hoje, limite]
        )
        serializer = self.get_serializer(prazos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        """Marca prazo como concluído"""
        prazo = self.get_object()
        prazo.marcar_concluido(request.user)
        serializer = self.get_serializer(prazo)
        return Response(serializer.data)


# ========== AUDIÊNCIA ==========
class AudienciaViewSet(viewsets.ModelViewSet):
    queryset = Audiencia.objects.all()
    serializer_class = AudienciaSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['processo', 'tipo', 'status', 'data']
    search_fields = ['processo__numero_cnj', 'local']
    ordering_fields = ['data', 'hora']
    
    def get_queryset(self):
        return Audiencia.objects.filter(processo__escritorio=self.request.user.escritorio)
    
    @action(detail=False, methods=['get'])
    def proximas(self, request):
        """Retorna próximas audiências"""
        hoje = timezone.now().date()
        audiencias = self.get_queryset().filter(
            data__gte=hoje,
            status__in=['agendada', 'confirmada']
        ).order_by('data', 'hora')[:10]
        
        serializer = self.get_serializer(audiencias, many=True)
        return Response(serializer.data)


# ========== FINANCEIRO ==========
class FinanceiroViewSet(viewsets.ModelViewSet):
    queryset = Financeiro.objects.all()
    permission_classes = [IsAuthenticated, IsEscritorioMember, CanManageFinanceiro]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'categoria', 'status', 'cliente', 'processo']
    search_fields = ['descricao', 'cliente__nome']
    ordering_fields = ['data_vencimento', 'valor']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FinanceiroListSerializer
        return FinanceiroSerializer
    
    def get_queryset(self):
        return Financeiro.objects.filter(escritorio=self.request.user.escritorio)
    
    def perform_create(self, serializer):
        serializer.save(
            escritorio=self.request.user.escritorio,
            criado_por=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """Retorna resumo financeiro"""
        qs = self.get_queryset()
        mes_atual = timezone.now().month
        
        resumo = {
            'receitas_mes': qs.filter(tipo='receita', data_vencimento__month=mes_atual).aggregate(
                total=Sum('valor')
            )['total'] or 0,
            'despesas_mes': qs.filter(tipo='despesa', data_vencimento__month=mes_atual).aggregate(
                total=Sum('valor')
            )['total'] or 0,
            'pendentes': qs.filter(status='pendente').count(),
            'vencidos': qs.filter(status='vencido').count(),
        }
        
        resumo['saldo_mes'] = resumo['receitas_mes'] - resumo['despesas_mes']
        
        return Response(resumo)


# ========== CONTRATO HONORÁRIOS ==========
class ContratoHonorariosViewSet(viewsets.ModelViewSet):
    queryset = ContratoHonorarios.objects.all()
    serializer_class = ContratoHonorariosSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'assinado', 'ativo', 'cliente']
    search_fields = ['processo__numero_cnj', 'cliente__nome']
    ordering_fields = ['criado_em', 'valor_total']
    
    def get_queryset(self):
        return ContratoHonorarios.objects.filter(processo__escritorio=self.request.user.escritorio)
    
    @action(detail=True, methods=['post'])
    def gerar_parcelas(self, request, pk=None):
        """Gera parcelas do contrato"""
        contrato = self.get_object()
        contrato.gerar_parcelas()
        serializer = self.get_serializer(contrato)
        return Response(serializer.data)


# ========== WHATSAPP ==========
class WhatsAppConfigViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppConfig.objects.all()
    serializer_class = WhatsAppConfigSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'status', 'ativo']
    search_fields = ['nome', 'numero_telefone']
    ordering_fields = ['criado_em', 'nome']
    
    def get_queryset(self):
        user = self.request.user
        configs = WhatsAppConfig.objects.filter(escritorio=user.escritorio)
        
        # Filtrar por permissão se não for admin
        if not user.pode_gerenciar_whatsapp and not user.is_superuser:
            configs = configs.filter(usuarios_permitidos=user)
        
        return configs


class MensagemWhatsAppViewSet(viewsets.ModelViewSet):
    queryset = MensagemWhatsApp.objects.all()
    serializer_class = MensagemWhatsAppSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'direcao', 'status', 'lida', 'cliente']
    search_fields = ['conteudo', 'numero_contato', 'nome_contato']
    ordering_fields = ['criado_em']
    
    def get_queryset(self):
        return MensagemWhatsApp.objects.filter(
            whatsapp_config__escritorio=self.request.user.escritorio
        )
    
    @action(detail=True, methods=['post'])
    def marcar_lida(self, request, pk=None):
        """Marca mensagem como lida"""
        mensagem = self.get_object()
        mensagem.marcar_como_lida()
        serializer = self.get_serializer(mensagem)
        return Response(serializer.data)


class FluxoChatbotViewSet(viewsets.ModelViewSet):
    queryset = FluxoChatbot.objects.all()
    serializer_class = FluxoChatbotSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'ativo']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['ordem', 'nome']
    
    def get_queryset(self):
        return FluxoChatbot.objects.filter(escritorio=self.request.user.escritorio)


class ConversaWhatsAppViewSet(viewsets.ModelViewSet):
    queryset = ConversaWhatsApp.objects.all()
    serializer_class = ConversaWhatsAppSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['aberta', 'arquivada', 'resolvida', 'cliente']
    search_fields = ['numero_contato', 'nome_contato']
    ordering_fields = ['ultima_mensagem', 'criada_em']
    
    def get_queryset(self):
        return ConversaWhatsApp.objects.filter(
            whatsapp_config__escritorio=self.request.user.escritorio
        )
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Retorna conversas pendentes de atendimento"""
        conversas = self.get_queryset().filter(
            aberta=True,
            mensagens_nao_lidas__gt=0
        ).order_by('-ultima_mensagem')
        
        serializer = self.get_serializer(conversas, many=True)
        return Response(serializer.data)