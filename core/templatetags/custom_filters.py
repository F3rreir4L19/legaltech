# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter para acessar item de dicionário por chave"""
    return dictionary.get(key)