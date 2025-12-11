# Importe todos os models para facilitar acesso

# Usuario
from .usuario import Escritorio, Usuario

# Cliente
from .cliente import Cliente, Entrevista

# Processo
from .processo import Processo, Andamento, Prazo, Audiencia

# Financeiro
from .financeiro import Financeiro, ContratoHonorarios, ParcelaHonorarios

# Notas
from .notes import CategoriaAnotacao, Anotacao

# WhatsApp
from .whatsapp import (
    WhatsAppConfig, 
    MensagemWhatsApp, 
    FluxoChatbot, 
    ConversaWhatsApp,
    WebhookEvent
)

# Lista todos os models para facilitar imports
__all__ = [
    # Usuario
    'Escritorio',
    'Usuario',
    
    # Cliente
    'Cliente',
    'Entrevista',
    
    # Processo
    'Processo',
    'Andamento',
    'Prazo',
    'Audiencia',
    
    # Financeiro
    'Financeiro',
    'ContratoHonorarios',
    'ParcelaHonorarios',
    
    # WhatsApp
    'WhatsAppConfig',
    'MensagemWhatsApp',
    'FluxoChatbot',
    'ConversaWhatsApp',
]