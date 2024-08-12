from django.db import models

# Create your models here.
class clientes(models.Model):
    id = models.AutoField(primary_key=True)
    cpf = models.CharField(unique=True, max_length=14)
    nome = models.TextField(max_length=225)
    cep = models.CharField(max_length=20)
    endereco = models.TextField(max_length=225)
    numero = models.CharField(max_length=10)
    complemento = models.TextField(max_length=100)
    bairro = models.TextField(max_length=36)
    cidade = models.TextField(max_length=36)
    estado = models.TextField(max_length=36)
    telefone_principal = models.CharField(max_length=16)
    email = models.TextField(max_length=100)
    
class CadastroFinanceiro(models.Model):
    id = models.AutoField(primary_key=True)
    cpf = models.CharField(max_length=14)
    valor = models.CharField(max_length=20)
    data_pagamento = models.DateField()
    forma_pagamento = models.TextField(max_length=50)
    chave_seguranca = models.TextField(max_length=50)
    departamento = models.TextField(max_length=50)
    descricao = models.TextField(max_length=500, default='Serviço sem descrição.')
    pago = models.BooleanField(default=False)