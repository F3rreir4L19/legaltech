# core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Escritorio)
class EscritorioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'email', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'cnpj']

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'email', 'tipo', 'escritorio', 'ativo']
    list_filter = ['tipo', 'ativo', 'escritorio']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email', 'telefone', 'avatar')
        }),
        ('Informações Profissionais', {
            'fields': ('tipo', 'oab', 'escritorio')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'cpf_cnpj', 'telefone', 'email', 'ativo']
    list_filter = ['tipo', 'ativo', 'escritorio']
    search_fields = ['nome', 'cpf_cnpj', 'telefone']