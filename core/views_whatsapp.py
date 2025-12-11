# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
from .models import WebhookEvent, WhatsAppConfig, MensagemWhatsApp, ConversaWhatsApp
from .serializers import (
    WhatsAppConfigSerializer, 
    MensagemWhatsAppSerializer,
    ConversaWhatsAppSerializer
)

@csrf_exempt
def webhook_receber_mensagem(request, config_id):
    """
    Webhook para receber mensagens do WhatsApp
    
    IDEMPOTÊNCIA: Mesmo webhook recebido múltiplas vezes só será processado uma vez
    """
    
    if request.method != 'POST':
        return HttpResponseBadRequest('Apenas POST é aceito')
    
    try:
        # Busca configuração
        config = WhatsAppConfig.objects.get(id=config_id, ativo=True)
    except WhatsAppConfig.DoesNotExist:
        return HttpResponseBadRequest('Configuração não encontrada ou inativa')
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    
    # CRÍTICO: Extrai ID único do webhook (varia por provider)
    # Evolution API: payload['data']['key']['id']
    # Twilio: payload['MessageSid']
    # Ajuste conforme seu provider
    webhook_id = (
        payload.get('id') or 
        payload.get('MessageSid') or 
        payload.get('data', {}).get('key', {}).get('id')
    )
    
    if not webhook_id:
        # Se não tem ID, gera um baseado em timestamp + hash
        import hashlib
        import time
        webhook_id = hashlib.md5(
            f"{time.time()}{json.dumps(payload)}".encode()
        ).hexdigest()
    
    # IDEMPOTÊNCIA: Verifica se já processou este webhook
    if WebhookEvent.objects.filter(webhook_id=webhook_id).exists():
        return JsonResponse({
            'status': 'already_processed',
            'message': 'Webhook já foi processado anteriormente'
        })
    
    # Registra o webhook
    webhook_event = WebhookEvent.objects.create(
        webhook_id=webhook_id,
        whatsapp_config=config,
        payload=payload,
        processed=False
    )
    
    try:
        # Processa a mensagem (ajuste conforme estrutura do seu provider)
        processar_mensagem_recebida(config, payload, webhook_event)
        
        webhook_event.processed = True
        webhook_event.save()
        
        return JsonResponse({
            'status': 'ok',
            'webhook_id': webhook_id,
            'message': 'Mensagem processada com sucesso'
        })
    
    except Exception as e:
        # Log do erro mas NÃO retorna erro (para evitar reenvio)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao processar webhook {webhook_id}: {str(e)}')
        
        # Retorna sucesso para o provider não reenviar
        return JsonResponse({
            'status': 'error_logged',
            'message': 'Erro no processamento mas webhook registrado'
        })


def processar_mensagem_recebida(config, payload, webhook_event):
    """
    Processa o payload e cria MensagemWhatsApp + ConversaWhatsApp
    
    IMPORTANTE: Ajuste conforme a estrutura do SEU provider
    """
    
    # Exemplo genérico - AJUSTE conforme Evolution/Twilio/Meta
    numero_contato = payload.get('from') or payload.get('sender')
    nome_contato = payload.get('pushName') or payload.get('senderName') or ''
    conteudo = payload.get('text') or payload.get('body') or ''
    tipo = 'texto'  # TODO: detectar tipo (imagem, audio, etc)
    
    if not numero_contato:
        raise ValueError('Número do contato não encontrado no payload')
    
    # Cria ou atualiza conversa
    conversa, _ = ConversaWhatsApp.objects.get_or_create(
        whatsapp_config=config,
        numero_contato=numero_contato,
        defaults={
            'nome_contato': nome_contato,
            'aberta': True
        }
    )
    
    # Cria mensagem
    mensagem = MensagemWhatsApp.objects.create(
        whatsapp_config=config,
        numero_contato=numero_contato,
        nome_contato=nome_contato,
        tipo=tipo,
        direcao='entrada',
        conteudo=conteudo,
        status='entregue',
        lida=False,
        metadata={'webhook_payload': payload}
    )
    
    # Atualiza estatísticas da conversa
    conversa.atualizar_estatisticas()
    
    # TODO: Verificar fluxos de chatbot e responder automaticamente
    # executar_fluxos_chatbot(conversa, mensagem)
    
    return mensagem


@login_required
def painel_whatsapp(request):
    """
    View principal do painel WhatsApp
    Renderiza o template HTML com o painel
    """
    # Busca todas as configurações de WhatsApp que o usuário tem acesso
    user = request.user
    
    if user.is_superuser:
        whatsapp_configs = WhatsAppConfig.objects.filter(ativo=True)
    else:
        # Filtra por escritório e permissões
        whatsapp_configs = WhatsAppConfig.objects.filter(
            escritorio=user.escritorio,
            ativo=True
        )
        
        # Se não tem permissão de gerenciar, filtra por usuários permitidos
        if not user.pode_gerenciar_whatsapp:
            whatsapp_configs = whatsapp_configs.filter(usuarios_permitidos=user)
    
    context = {
        'whatsapp_configs': whatsapp_configs,
        'user': user,
    }
    
    return render(request, 'whatsapp/painel.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_whatsapp_configs(request):
    """
    API: Lista todas as configurações de WhatsApp disponíveis
    """
    user = request.user
    
    if user.is_superuser:
        configs = WhatsAppConfig.objects.filter(ativo=True)
    else:
        configs = WhatsAppConfig.objects.filter(
            escritorio=user.escritorio,
            ativo=True
        )
        
        if not user.pode_gerenciar_whatsapp:
            configs = configs.filter(usuarios_permitidos=user)
    
    serializer = WhatsAppConfigSerializer(configs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_conversas(request, config_id):
    """
    API: Lista todas as conversas de uma configuração específica
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    
    # Verifica permissão
    if not config.pode_usar(request.user):
        return Response(
            {'erro': 'Você não tem permissão para acessar esta configuração'},
            status=403
        )
    
    # Busca conversas
    conversas = ConversaWhatsApp.objects.filter(
        whatsapp_config=config
    ).order_by('-ultima_mensagem')
    
    # Filtros opcionais
    if request.GET.get('abertas') == 'true':
        conversas = conversas.filter(aberta=True)
    
    if request.GET.get('nao_lidas') == 'true':
        conversas = conversas.filter(mensagens_nao_lidas__gt=0)
    
    serializer = ConversaWhatsAppSerializer(conversas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_mensagens(request, config_id, numero_contato):
    """
    API: Lista todas as mensagens de uma conversa específica
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    
    # Verifica permissão
    if not config.pode_usar(request.user):
        return Response(
            {'erro': 'Você não tem permissão para acessar esta configuração'},
            status=403
        )
    
    # Busca mensagens
    mensagens = MensagemWhatsApp.objects.filter(
        whatsapp_config=config,
        numero_contato=numero_contato
    ).order_by('criado_em')
    
    # Limita a 100 mensagens mais recentes por padrão
    limite = int(request.GET.get('limite', 100))
    mensagens = mensagens[max(0, mensagens.count() - limite):]
    
    serializer = MensagemWhatsAppSerializer(mensagens, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_enviar_mensagem(request, config_id):
    """
    API: Envia uma nova mensagem
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    
    # Verifica permissão
    if not config.pode_usar(request.user):
        return Response(
            {'erro': 'Você não tem permissão para acessar esta configuração'},
            status=403
        )
    
    # Valida dados
    numero_contato = request.data.get('numero_contato')
    conteudo = request.data.get('conteudo')
    tipo = request.data.get('tipo', 'texto')
    
    if not numero_contato or not conteudo:
        return Response(
            {'erro': 'numero_contato e conteudo são obrigatórios'},
            status=400
        )
    
    # Cria mensagem
    mensagem = MensagemWhatsApp.objects.create(
        whatsapp_config=config,
        numero_contato=numero_contato,
        conteudo=conteudo,
        tipo=tipo,
        direcao='saida',
        status='enviando',
        usuario_responsavel=request.user
    )
    
    # TODO: Aqui você implementaria a lógica para enviar via API do WhatsApp
    # Por enquanto, apenas simula o envio
    mensagem.status = 'enviado'
    mensagem.save()
    
    # Atualiza ou cria conversa
    conversa, created = ConversaWhatsApp.objects.get_or_create(
        whatsapp_config=config,
        numero_contato=numero_contato,
        defaults={
            'nome_contato': request.data.get('nome_contato', ''),
            'aberta': True
        }
    )
    conversa.atualizar_estatisticas()
    
    serializer = MensagemWhatsAppSerializer(mensagem)
    return Response(serializer.data, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marcar_lida(request, config_id, mensagem_id):
    """
    API: Marca uma mensagem como lida
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    mensagem = get_object_or_404(MensagemWhatsApp, id=mensagem_id, whatsapp_config=config)
    
    # Verifica permissão
    if not config.pode_usar(request.user):
        return Response(
            {'erro': 'Você não tem permissão para acessar esta configuração'},
            status=403
        )
    
    mensagem.marcar_como_lida()
    
    # Atualiza estatísticas da conversa
    conversa = ConversaWhatsApp.objects.filter(
        whatsapp_config=config,
        numero_contato=mensagem.numero_contato
    ).first()
    
    if conversa:
        conversa.atualizar_estatisticas()
    
    return Response({'sucesso': True})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_permissoes(request, config_id):
    """
    API: Gerencia permissões de acesso a uma configuração de WhatsApp
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    
    # Apenas quem pode gerenciar WhatsApp pode alterar permissões
    if not request.user.pode_gerenciar_whatsapp and not request.user.is_superuser:
        return Response(
            {'erro': 'Você não tem permissão para gerenciar permissões'},
            status=403
        )
    
    if request.method == 'GET':
        # Lista usuários com permissão
        usuarios = config.usuarios_permitidos.all()
        from .serializers import UsuarioListSerializer
        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Adiciona ou remove permissão
        usuario_id = request.data.get('usuario_id')
        acao = request.data.get('acao')  # 'adicionar' ou 'remover'
        
        from .models import Usuario
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        if acao == 'adicionar':
            config.usuarios_permitidos.add(usuario)
            return Response({'sucesso': True, 'mensagem': f'Permissão concedida para {usuario.get_full_name()}'})
        elif acao == 'remover':
            config.usuarios_permitidos.remove(usuario)
            return Response({'sucesso': True, 'mensagem': f'Permissão removida de {usuario.get_full_name()}'})
        else:
            return Response({'erro': 'Ação inválida. Use "adicionar" ou "remover"'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_atribuir_conversa(request, config_id, numero_contato):
    """
    API: Atribui uma conversa a um usuário
    """
    config = get_object_or_404(WhatsAppConfig, id=config_id)
    
    # Verifica permissão
    if not config.pode_usar(request.user):
        return Response(
            {'erro': 'Você não tem permissão para acessar esta configuração'},
            status=403
        )
    
    conversa = get_object_or_404(
        ConversaWhatsApp,
        whatsapp_config=config,
        numero_contato=numero_contato
    )
    
    # Atribui ao usuário logado ou a outro usuário especificado
    usuario_id = request.data.get('usuario_id')
    
    if usuario_id:
        from .models import Usuario
        usuario = get_object_or_404(Usuario, id=usuario_id)
        conversa.usuario_atribuido = usuario
    else:
        conversa.usuario_atribuido = request.user
    
    conversa.save()
    
    serializer = ConversaWhatsAppSerializer(conversa)
    return Response(serializer.data)
