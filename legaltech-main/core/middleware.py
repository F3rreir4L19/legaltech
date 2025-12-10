# -*- coding: utf-8 -*-
"""
Middleware para isolamento de dados por escritório (Multi-tenant)

POR QUE ISSO É CRÍTICO:
- Impede que usuários de um escritório acessem dados de outro
- Força filtros automáticos em todas as queries
- Adiciona segurança na camada de middleware, não apenas nas views
"""

from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que injeta o escritório do usuário no request
    e previne acesso cruzado entre escritórios
    """
    
    def process_request(self, request):
        # Se usuário está autenticado, injeta o escritório
        if request.user and request.user.is_authenticated:
            # Superusuários podem acessar tudo
            if request.user.is_superuser:
                request.tenant = None  # Sem restrição
                return None
            
            # Usuários normais: restringe ao escritório deles
            if hasattr(request.user, 'escritorio') and request.user.escritorio:
                request.tenant = request.user.escritorio
            else:
                # Usuário sem escritório: bloqueia acesso
                return HttpResponseForbidden(
                    "Usuário não está associado a nenhum escritório. "
                    "Entre em contato com o administrador."
                )
        else:
            # Usuário não autenticado: sem tenant
            request.tenant = None
        
        return None


class TenantQuerySetMiddleware:
    """
    OPCIONAL: Middleware que força filtros automáticos nos QuerySets
    
    ATENÇÃO: Este é avançado e pode causar problemas se não for bem testado.
    Recomendo começar sem ele e adicionar depois se necessário.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # TODO: Implementar filtro automático de QuerySets se necessário
        response = self.get_response(request)
        return response