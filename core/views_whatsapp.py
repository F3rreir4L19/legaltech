# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import WhatsAppConfig, MensagemWhatsApp, ConversaWhatsApp
from .serializers import (
    WhatsAppConfigSerializer, 
    MensagemWhatsAppSerializer,
    ConversaWhatsAppSerializer
)


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
