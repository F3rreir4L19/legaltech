# -*- coding: utf-8 -*-
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # ViewSets que criaremos
    EscritorioViewSet,
    UsuarioViewSet,
    ClienteViewSet,
    AnotacaoViewSet,
    EntrevistaViewSet,
    ProcessoViewSet,
    AndamentoViewSet,
    PrazoViewSet,
    AudienciaViewSet,
    FinanceiroViewSet,
    ContratoHonorariosViewSet,
    WhatsAppConfigViewSet,
    MensagemWhatsAppViewSet,
    FluxoChatbotViewSet,
    ConversaWhatsAppViewSet,
)

# Router para gerar automaticamente as URLs RESTful
router = DefaultRouter()

# Registrar ViewSets
router.register(r'escritorios', EscritorioViewSet, basename='escritorio')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'anotacoes', AnotacaoViewSet, basename='anotacao')
router.register(r'entrevistas', EntrevistaViewSet, basename='entrevista')
router.register(r'processos', ProcessoViewSet, basename='processo')
router.register(r'andamentos', AndamentoViewSet, basename='andamento')
router.register(r'prazos', PrazoViewSet, basename='prazo')
router.register(r'audiencias', AudienciaViewSet, basename='audiencia')
router.register(r'financeiro', FinanceiroViewSet, basename='financeiro')
router.register(r'contratos-honorarios', ContratoHonorariosViewSet, basename='contrato-honorarios')
router.register(r'whatsapp-configs', WhatsAppConfigViewSet, basename='whatsapp-config')
router.register(r'mensagens-whatsapp', MensagemWhatsAppViewSet, basename='mensagem-whatsapp')
router.register(r'fluxos-chatbot', FluxoChatbotViewSet, basename='fluxo-chatbot')
router.register(r'conversas-whatsapp', ConversaWhatsAppViewSet, basename='conversa-whatsapp')

app_name = 'core'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # URLs customizadas (ações específicas) podem ser adicionadas aqui
    # Exemplo:
    # path('processos/<int:pk>/gerar-relatorio/', views.gerar_relatorio_processo),
]