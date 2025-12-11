# core/views_notes.py
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import CategoriaAnotacao, Anotacao
from .serializers import AnotacaoSerializer
from .permissions import IsEscritorioMember

# ViewSet para API (mantém o existente)
class AnotacaoViewSet(viewsets.ModelViewSet):
    queryset = Anotacao.objects.all()
    serializer_class = AnotacaoSerializer
    permission_classes = [IsAuthenticated, IsEscritorioMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'categoria', 'importante']
    search_fields = ['titulo', 'conteudo']
    ordering_fields = ['criado_em', 'importante']
    
    def get_queryset(self):
        qs = Anotacao.objects.filter(cliente__escritorio=self.request.user.escritorio)
        # Filtrar anotações privadas
        if not self.request.user.is_superuser:
            qs = qs.filter(Q(privada=False) | Q(usuario=self.request.user))
        return qs
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
    
    @action(detail=False, methods=['post'])
    def update_kanban(self, request):
        """API para atualizar posição das anotações no Kanban"""
        try:
            data = request.data
            anotacao = Anotacao.objects.get(
                id=data.get('anotacao_id'), 
                usuario=request.user  # Segurança: só dono pode mover
            )
            
            nova_categoria_id = data.get('nova_categoria_id')
            nova_ordem = data.get('nova_ordem', 0)
            
            if nova_categoria_id:
                nova_categoria = CategoriaAnotacao.objects.get(
                    id=nova_categoria_id,
                    usuario=request.user  # Só pode mover para suas categorias
                )
                anotacao.categoria = nova_categoria
            
            anotacao.ordem = nova_ordem
            anotacao.save()
            
            return Response({'success': True, 'message': 'Anotação movida com sucesso'})
            
        except Anotacao.DoesNotExist:
            return Response({'error': 'Anotação não encontrada'}, status=404)
        except CategoriaAnotacao.DoesNotExist:
            return Response({'error': 'Categoria não encontrada'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

# Views para template HTML (painel Kanban)
@login_required
def kanban_anotacoes(request):
    """View principal do Kanban"""
    # Cria categorias padrão se não existirem
    categorias = CategoriaAnotacao.objects.filter(usuario=request.user)
    
    if not categorias.exists():
        categorias_padrao = [
            ('A Fazer', '#ffeaa7'),
            ('Em Progresso', '#74b9ff'),
            ('Revisão', '#fd79a8'),
            ('Concluído', '#00b894'),
        ]
        
        for ordem, (nome, cor) in enumerate(categorias_padrao):
            CategoriaAnotacao.objects.create(
                usuario=request.user,
                nome=nome,
                ordem=ordem,
                cor=cor
            )
        
        categorias = CategoriaAnotacao.objects.filter(usuario=request.user)
    
    # Organiza anotações por categoria
    categorias_ordenadas = categorias.order_by('ordem')
    anotacoes_por_categoria = {}
    
    for categoria in categorias_ordenadas:
        anotacoes = Anotacao.objects.filter(
            categoria=categoria,
            usuario=request.user
        ).order_by('ordem')
        anotacoes_por_categoria[categoria.id] = anotacoes
    
    return render(request, 'anotacoes/kanban.html', {
        'categorias': categorias_ordenadas,
        'anotacoes_por_categoria': anotacoes_por_categoria,
        'user': request.user
    })

@csrf_exempt
@require_POST
@login_required
def update_kanban_simple(request):
    """Versão simples para o template (sem DRF)"""
    try:
        data = json.loads(request.body)
        anotacao = Anotacao.objects.get(
            id=data['anotacao_id'], 
            usuario=request.user
        )
        
        nova_categoria_id = data['nova_categoria_id']
        nova_ordem = data.get('nova_ordem', 0)
        
        if nova_categoria_id:
            nova_categoria = CategoriaAnotacao.objects.get(
                id=nova_categoria_id,
                usuario=request.user
            )
            anotacao.categoria = nova_categoria
        
        anotacao.ordem = nova_ordem
        anotacao.save()
        
        return JsonResponse({'success': True})
        
    except Anotacao.DoesNotExist:
        return JsonResponse({'error': 'Anotação não encontrada'}, status=404)
    except CategoriaAnotacao.DoesNotExist:
        return JsonResponse({'error': 'Categoria não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_POST
@login_required
def criar_categoria(request):
    """Cria nova categoria"""
    try:
        data = json.loads(request.body)
        nome = data.get('nome', 'Nova Categoria')
        cor = data.get('cor', '#f0f0f0')
        
        # Verifica ordem (última + 1)
        ultima_ordem = CategoriaAnotacao.objects.filter(
            usuario=request.user
        ).order_by('-ordem').first()
        
        ordem = ultima_ordem.ordem + 1 if ultima_ordem else 0
        
        categoria = CategoriaAnotacao.objects.create(
            usuario=request.user,
            nome=nome,
            cor=cor,
            ordem=ordem
        )
        
        return JsonResponse({
            'success': True, 
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome,
                'cor': categoria.cor
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_POST
@login_required
def criar_anotacao_rapida(request):
    """Cria anotação rápida no Kanban"""
    try:
        data = json.loads(request.body)
        titulo = data.get('titulo', 'Nova Anotação')
        conteudo = data.get('conteudo', '')
        categoria_id = data.get('categoria_id')
        
        if not categoria_id:
            return JsonResponse({'error': 'Categoria é obrigatória'}, status=400)
        
        categoria = CategoriaAnotacao.objects.get(
            id=categoria_id,
            usuario=request.user
        )
        
        # Verifica última ordem nesta categoria
        ultima_anotacao = Anotacao.objects.filter(
            categoria=categoria
        ).order_by('-ordem').first()
        
        ordem = ultima_anotacao.ordem + 1 if ultima_anotacao else 0
        
        anotacao = Anotacao.objects.create(
            usuario=request.user,
            categoria=categoria,
            titulo=titulo,
            conteudo=conteudo,
            ordem=ordem
        )
        
        return JsonResponse({
            'success': True,
            'anotacao': {
                'id': anotacao.id,
                'titulo': anotacao.titulo,
                'conteudo': anotacao.conteudo,
                'categoria_id': anotacao.categoria_id
            }
        })
        
    except CategoriaAnotacao.DoesNotExist:
        return JsonResponse({'error': 'Categoria não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)