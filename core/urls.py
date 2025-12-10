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
from .views_whatsapp import (
    painel_whatsapp,
    api_whatsapp_configs,
    api_conversas,
    api_mensagens,
    api_enviar_mensagem,
    api_marcar_lida,
    api_permissoes,
    api_atribuir_conversa,
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
    
    # URLs do Painel WhatsApp
    path('whatsapp/painel/', painel_whatsapp, name='painel-whatsapp'),
    path('whatsapp/configs/', api_whatsapp_configs, name='api-whatsapp-configs'),
    path('whatsapp/<int:config_id>/conversas/', api_conversas, name='api-conversas'),
    path('whatsapp/<int:config_id>/mensagens/<str:numero_contato>/', api_mensagens, name='api-mensagens'),
    path('whatsapp/<int:config_id>/enviar/', api_enviar_mensagem, name='api-enviar-mensagem'),
    path('whatsapp/<int:config_id>/mensagens/<int:mensagem_id>/marcar-lida/', api_marcar_lida, name='api-marcar-lida'),
    path('whatsapp/<int:config_id>/permissoes/', api_permissoes, name='api-permissoes'),
    path('whatsapp/<int:config_id>/atribuir/<str:numero_contato>/', api_atribuir_conversa, name='api-atribuir-conversa'),
]