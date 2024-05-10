from django.db import models

# Create your models here.
class clientes(models.Model):
    cpf = models.CharField(primary_key=True, unique=True, max_length=14)
    # identidade = models.CharField(unique=True, max_length=10)
    # orgao_expedidor = models.TextField(max_length=50)
    nome = models.TextField(max_length=225)
    # nome_social = models.TextField(max_length=225)
    # data_nascimento = models.DateField()
    # sexo = models.TextField(max_length=20)
    # genero = models.TextField(max_length=50)
    # etnia = models.CharField(max_length=20)
    # nome_mae = models.TextField(max_length=225)
    # nome_pai = models.TextField(max_length=225)
    cep = models.CharField(max_length=20)
    endereco = models.TextField(max_length=225)
    numero = models.CharField(max_length=10)
    complemento = models.TextField(max_length=100)
    bairro = models.TextField(max_length=36)
    cidade = models.TextField(max_length=36)
    estado = models.TextField(max_length=36)
    telefone_principal = models.CharField(max_length=16)
    # celular = models.CharField(max_length=14)
    email = models.TextField(max_length=100)
    
class CadastroFinanceiro(models.Model):
    id = models.AutoField(primary_key=True)
    cpf = models.CharField(max_length=14)
    # servico = models.TextField(max_length=50)
    # solicitante = models.TextField(max_length=50)
    valor = models.CharField(max_length=20)
    data_pagamento = models.DateField()
    forma_pagamento = models.TextField(max_length=50)
    chave_seguranca = models.TextField(max_length=50)
    departamento = models.TextField(max_length=50)
    # nivel = models.TextField(max_length=50)
    # subarea = models.TextField(max_length=50)
    descricao = models.TextField(max_length=500, default='Serviço sem descrição.')