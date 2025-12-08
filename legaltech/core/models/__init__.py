# Importe todos os models para facilitar acesso

# Usuario
from .usuario import Escritorio, Usuario

# Cliente
from .cliente import Cliente, Anotacao, Entrevista

# Processo
from .processo import Processo, Andamento, Prazo, Audiencia

# Financeiro
from .financeiro import Financeiro, ContratoHonorarios, ParcelaHonorarios

# WhatsApp
from .whatsapp import (
    WhatsAppConfig, 
    MensagemWhatsApp, 
    FluxoChatbot, 
    ConversaWhatsApp
)

# Lista todos os models para facilitar imports
__all__ = [
    # Usuario
    'Escritorio',
    'Usuario',
    
    # Cliente
    'Cliente',
    'Anotacao',
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