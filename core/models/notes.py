# core/models/notes.py
from django.db import models
from .usuario import Usuario
from .cliente import Cliente

class CategoriaAnotacao(models.Model):
    """Categorias (colunas) do Kanban, por usuário"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='categorias_anotacoes')
    nome = models.CharField('Nome da Categoria', max_length=100, default='Nova Categoria')
    ordem = models.IntegerField('Ordem', default=0)  # Pra ordenar colunas
    cor = models.CharField('Cor de Fundo', max_length=20, blank=True, default='#f0f0f0')

    class Meta:
        verbose_name = 'Categoria de Anotação'
        verbose_name_plural = 'Categorias de Anotações'
        ordering = ['ordem']
        unique_together = ['usuario', 'nome']  # Evita duplicatas por user

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

class Anotacao(models.Model):
    # Campos existentes mantidos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='anotacoes', null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='anotacoes')
    categoria = models.ForeignKey(CategoriaAnotacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='anotacoes')
    
    # Campos para o Kanban
    ordem = models.IntegerField('Ordem na Categoria', default=0)
    
    # Campos originais (ajuste conforme seu model real)
    titulo = models.CharField('Título', max_length=200, default='Nova Anotação')
    conteudo = models.TextField('Conteúdo', blank=True)
    importante = models.BooleanField('Importante', default=False)
    privada = models.BooleanField('Privada', default=False)
    criado_em = models.DateTimeField('Criada em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizada em', auto_now=True)
    
    class Meta:
        verbose_name = 'Anotação'
        verbose_name_plural = 'Anotações'
        ordering = ['ordem']
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        # Se não tiver categoria, cria uma padrão
        if not self.categoria and self.usuario:
            categoria_padrao, _ = CategoriaAnotacao.objects.get_or_create(
                usuario=self.usuario,
                nome='Geral',
                defaults={'ordem': 0, 'cor': '#f0f0f0'}
            )
            self.categoria = categoria_padrao
        super().save(*args, **kwargs)# core/models/notes.py