# -*- coding: utf-8 -*-
from rest_framework import permissions


class IsEscritorioMember(permissions.BasePermission):
    """
    Permissão que verifica se o usuário pertence ao mesmo escritório do objeto
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Superusuário tem acesso a tudo
        if request.user.is_superuser:
            return True
        
        # Verifica se o objeto tem um atributo 'escritorio'
        if hasattr(obj, 'escritorio'):
            return obj.escritorio == request.user.escritorio
        
        # Verifica se o objeto tem 'cliente' com 'escritorio'
        if hasattr(obj, 'cliente') and hasattr(obj.cliente, 'escritorio'):
            return obj.cliente.escritorio == request.user.escritorio
        
        # Verifica se o objeto tem 'processo' com 'escritorio'
        if hasattr(obj, 'processo') and hasattr(obj.processo, 'escritorio'):
            return obj.processo.escritorio == request.user.escritorio
        
        # Se não encontrou relação com escritório, nega acesso
        return False


class CanManageUsuarios(permissions.BasePermission):
    """
    Permissão para gerenciar usuários
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre pode
        if request.user.is_superuser:
            return True
        
        # Métodos de leitura são permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Para criar, editar ou deletar, precisa ter permissão
        return request.user.pode_gerenciar_usuarios
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuário sempre pode
        if request.user.is_superuser:
            return True
        
        # Usuário pode ver seus próprios dados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Usuário pode editar seus próprios dados
        if obj == request.user:
            return True
        
        # Para editar outros usuários, precisa ter permissão
        return request.user.pode_gerenciar_usuarios


class CanManageClientes(permissions.BasePermission):
    """
    Permissão para gerenciar clientes
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.pode_gerenciar_clientes


class CanManageProcessos(permissions.BasePermission):
    """
    Permissão para gerenciar processos
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.pode_gerenciar_processos


class CanManageFinanceiro(permissions.BasePermission):
    """
    Permissão para gerenciar financeiro
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Leitura restrita - apenas quem tem permissão pode ver
        if request.method in permissions.SAFE_METHODS:
            return request.user.pode_gerenciar_financeiro or request.user.tipo in ['admin', 'socio']
        
        return request.user.pode_gerenciar_financeiro


class CanManageWhatsApp(permissions.BasePermission):
    """
    Permissão para gerenciar WhatsApp
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Leitura permitida para todos que tem acesso ao WhatsApp
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.pode_gerenciar_whatsapp
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Verifica se o usuário tem acesso a esta config
        if hasattr(obj, 'pode_usar'):
            return obj.pode_usar(request.user)
        
        return request.user.pode_gerenciar_whatsapp


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite apenas o dono editar
    """
    
    def has_object_permission(self, request, view, obj):
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Apenas o criador pode editar
        if hasattr(obj, 'criado_por'):
            return obj.criado_por == request.user
        
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        return False


class IsResponsavelOrReadOnly(permissions.BasePermission):
    """
    Permissão para responsáveis por processos/prazos
    """
    
    def has_object_permission(self, request, view, obj):
        # Leitura permitida
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin e sócio podem tudo
        if request.user.tipo in ['admin', 'socio']:
            return True
        
        # Verifica se é o responsável
        if hasattr(obj, 'responsavel'):
            return obj.responsavel == request.user
        
        if hasattr(obj, 'advogado_responsavel'):
            return obj.advogado_responsavel == request.user
        
        return False