from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

class LegalFlowAdminSite(admin.AdminSite):
    site_header = "⚖️ LegalFlow - Sistema Jurídico"
    site_title = "LegalFlow Admin"
    index_title = "Dashboard"
    site_url = "/api/"  # Link para sua API
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.custom_dashboard), name='custom-dashboard'),
            path('stats/', self.admin_view(self.stats_view), name='stats'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        # Redireciona para dashboard customizado
        return HttpResponseRedirect('/admin/dashboard/')
    
    def custom_dashboard(self, request):
        # Dashboard customizado
        context = {
            **self.each_context(request),
            'title': 'Dashboard LegalFlow',
            'subtitle': 'Gestão Jurídica Inteligente',
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def stats_view(self, request):
        # View de estatísticas
        context = {
            **self.each_context(request),
            'title': 'Estatísticas',
        }
        return TemplateResponse(request, 'admin/stats.html', context)

# Substitua o admin padrão no seu __init__.py do core
admin_site = LegalFlowAdminSite(name='legalflow_admin')