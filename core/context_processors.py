from django.utils import timezone
from datetime import date
from .models import Processo, Cliente, Prazo, Audiencia, MensagemWhatsApp

def dashboard_context(request):
    if not request.user.is_authenticated:
        return {}
    
    context = {}
    
    try:
        # Se o usuário tem escritório
        escritorio = request.user.escritorio
        
        # Estatísticas
        context['processos_count'] = Processo.objects.filter(
            escritorio=escritorio,
            situacao='ativo'
        ).count()
        
        context['clientes_count'] = Cliente.objects.filter(
            escritorio=escritorio,
            ativo=True
        ).count()
        
        # Prazos que vencem hoje
        hoje = date.today()
        context['prazos_hoje'] = Prazo.objects.filter(
            processo__escritorio=escritorio,
            data_limite=hoje,
            status='pendente'
        ).count()
        
        # Mensagens não lidas do WhatsApp
        context['mensagens_nao_lidas'] = MensagemWhatsApp.objects.filter(
            whatsapp_config__escritorio=escritorio,
            lida=False,
            direcao='entrada'
        ).count()
        
        # Próximas audiências (próximos 7 dias)
        semana = hoje + timezone.timedelta(days=7)
        context['proximas_audiencias'] = Audiencia.objects.filter(
            processo__escritorio=escritorio,
            data__gte=hoje,
            data__lte=semana,
            status__in=['agendada', 'confirmada']
        ).order_by('data', 'hora')[:5]
        
    except Exception as e:
        # Em caso de erro, retorna contexto vazio
        print(f"Erro no dashboard_context: {e}")
    
    return context